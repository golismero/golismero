#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abstract classes for message dispatchers.
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
Golismero project mail: contact@golismero-project.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

__all__ = ["AuditNotifier", "OrchestratorNotifier"]

from ..api.config import Config
from ..api.data import Data, Relationship
from ..api.plugin import Plugin
from ..managers.pluginmanager import SwitchToPlugin
from .message import Message
from .codes import MessageType, MessageCode, MessagePriority

from collections import defaultdict
from inspect import isclass
from traceback import format_exc
from warnings import warn


#------------------------------------------------------------------------------
class AbstractNotifier (object):
    """
    Abstract class for message dispatchers.
    """


    #--------------------------------------------------------------------------
    def __init__(self):

        # Call the superclass constructor.
        super(AbstractNotifier, self).__init__()

        # Info message notification list for plugins
        # that receive all information types.
        # list(str)
        self._notification_info_all = []

        # Info message notification mapping for plugins.
        # dict(str -> str)
        self._notification_info_map = defaultdict(set)

        # Relationship notification mappings for plugins.
        # dict(str -> str)
        self._notification_rel_map_left  = defaultdict(set)
        self._notification_rel_map_right = defaultdict(set)

        # Control message notification mapping for plugins.
        # list(Plugin)
        self._notification_msg_list = []

        # Map of plugin IDs to plugin instances.
        # dict(str -> Plugin)
        self._map_id_to_plugin = {}


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this notifier.
        """
        self._notification_msg_list = []
        self._notification_info_map.clear()
        self._notification_rel_map_left.clear()
        self._notification_rel_map_right.clear()
        self._map_id_to_plugin.clear()


    #--------------------------------------------------------------------------
    def add_multiple_plugins(self, plugins):
        """
        Add multiple plugins.

        :param plugins: Map of plugin IDs to plugin instances.
        :type plugins: dict(str -> Plugin)
        """
        for name, plugin in plugins.iteritems():
            self.add_plugin(name, plugin)


    #--------------------------------------------------------------------------
    def add_plugin(self, plugin_id, plugin):
        """
        Add a plugin.

        :param plugin_id: The plugin ID.
        :type plugin_id: str

        :param plugin: The plugin instance.
        :type plugin: Plugin
        """
        if not isinstance(plugin, Plugin):
            raise TypeError("Expected Plugin, got %r instead" % type(plugin))

        # Add the plugin to the names map.
        self._map_id_to_plugin[plugin_id] = plugin

        # UI plugins can receive control messages.
        if plugin.PLUGIN_TYPE == Plugin.PLUGIN_TYPE_UI:
            self._notification_msg_list.append(plugin)

        # Get the data types accepted by this plugin.
        if hasattr(plugin, "get_accepted_types"):
            with SwitchToPlugin(plugin_id):
                accepted_info = plugin.get_accepted_types()
        else:
            accepted_info = []

        # Special value 'None' means all data types.
        if accepted_info is None:
            self._notification_info_map[""].add(plugin_id)

        # Otherwise, it's a list of data subtypes.
        else:
            if isclass(accepted_info):
                accepted_info = [accepted_info]
            else:
                accepted_info = list(accepted_info)

            # Register the plugin for each accepted type.
            for item in accepted_info:

                # If it's a graph node event...
                if issubclass(item, Data):
                    targets = ((self._notification_info_map, item),)

                # If it's a graph vertex event...
                elif issubclass(item, Relationship):
                    targets = (
                        (self._notification_rel_map_left,  item.classes[0]),
                        (self._notification_rel_map_right, item.classes[1])
                    )

                # Anything else is an error.
                else:
                    raise TypeError(
                        "Expected Data subclass or Relationship type, "
                        "got %r instead" % type(item))

                # Register in the corresponding maps.
                for target, item in targets:
                    subtype = item.data_subtype
                    if not subtype or subtype == "data/abstract":
                        subtype = ""
                    elif subtype.endswith("/abstract"):
                        subtype = subtype[:-9]
                    target[subtype].add(plugin_id)


    #--------------------------------------------------------------------------
    def notify(self, message):
        """
        Dispatch messages to the plugins.

        :param message: A message to send to plugins.
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %r instead" % type(message))

        # Keep count of how many messages are sent.
        count = 0

        try:

            # Data request messages are sent to the run() plugin method.
            if (
                message.message_type == MessageType.MSG_TYPE_DATA and
                message.message_code == MessageCode.MSG_DATA_REQUEST
            ):
                audit_name = message.audit_name
                for data in message.message_info:

                    # If it's a relationship...
                    if isinstance(data, Relationship):

                        # Dispatch to the plugins that expect this order.
                        count += self.dispatch_plugin_input(audit_name, data)

                        # Dispatch to those that expect the opposite order.
                        data = data.invert()
                        count += self.dispatch_plugin_input(audit_name, data)

                    # If it's data...
                    else:

                        # Dispatch the data to the plugins.
                        count += self.dispatch_plugin_input(audit_name, data)

            # All other messages are sent to the recv_msg() plugin method.
            else:
                for plugin in self._notification_msg_list:
                    self.dispatch_msg(plugin, message)
                    count += 1

        # On error issue a warning.
        # We can't log the error, because the log messages themselves
        # may trigger the same error again.
        except Exception:
            warn("Error sending message to plugins: %s" % format_exc(),
                 RuntimeWarning)
            raise

        # Return the count of messages sent.
        return count


    #--------------------------------------------------------------------------
    def dispatch_plugin_input(self, audit_name, data):

        # Get the set of plugins to notify.
        m_plugins_to_notify = self.get_plugins_to_notify(data)

        # Dispatch message info to each plugin.
        count = 0
        for plugin_id in m_plugins_to_notify:
            plugin = self._map_id_to_plugin[plugin_id]
            self.dispatch_data(plugin, audit_name, data)
            count += 1

        # Return the count of successfully dispatched entities.
        return count


    #--------------------------------------------------------------------------
    def get_plugins_to_notify(self, data):
        """
        Determine which plugins should receive this data object.

        :param data: Data object.
        :type data: Data

        :returns: set(str) -- Set of plugin IDs.
        """

        plugins_to_notify = set()

        # Plugins that expect all types of events.
        plugins_to_notify.update(self._notification_info_map[""])

        # Plugins that expect vertex events. Order is important!
        if isinstance(data, Relationship):
            left = set()
            right = set()
            self.__collect_plugins(self._notification_rel_map_left,
                                   data.instances[0].data_subtype, left)
            self.__collect_plugins(self._notification_rel_map_right,
                                   data.instances[1].data_subtype, right)
            plugins_to_notify.update(left.intersection(right))

        # Plugins that expect node events.
        else:
            self.__collect_plugins(self._notification_info_map,
                                   data.data_subtype, plugins_to_notify)

        return plugins_to_notify


    #--------------------------------------------------------------------------
    def __collect_plugins(self, info_map, subtype, result):
        if subtype and subtype != "data/abstract":
            if subtype.endswith("/abstract"):
                subtype = subtype[:-9]
            while True:
                if subtype in info_map:
                    result.update(info_map[subtype])
                p = subtype.rfind("/")
                if p <= 0:
                    break
                subtype = subtype[:p]


    #--------------------------------------------------------------------------
    def dispatch_data(self, plugin, audit_name, message_info):
        """
        Send data to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param audit_name: Audit name.
        :type audit_name: str

        :param message_info: Data to send to plugins.
        :type message_info: Data
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def dispatch_msg(self, plugin, message):
        """
        Send messages to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param message: Message to send to plugins.
        :type message: Message
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


#------------------------------------------------------------------------------
class AuditNotifier(AbstractNotifier):
    """
    Audit message dispatcher. Sends messages to plugins.
    """


    #--------------------------------------------------------------------------
    def __init__(self, audit):
        """
        :param audit: Audit instance.
        :type audit: Audit
        """
        super(AuditNotifier, self).__init__()
        self.__audit = audit
        self.__processing = defaultdict(set)


    #--------------------------------------------------------------------------

    @property
    def audit(self):
        """
        :returns: Audit instance.
        :rtype: Audit
        """
        return self.__audit

    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__audit.orchestrator

    @property
    def pluginManager(self):
        """
        :returns: Plugin manager.
        :rtype: PluginManager
        """
        return self.__audit.pluginManager

    @property
    def current_stage(self):
        """
        :returns: Current execution stage.
        :rtype: str
        """
        return self.__audit.current_stage

    @property
    def database(self):
        """
        :returns: Audit database.
        :rtype: AuditDB
        """
        return self.__audit.database


    #--------------------------------------------------------------------------
    def acknowledge(self, message):
        """
        Got an ACK for a message sent from this audit to the plugins.

        :param message: The message with the ACK.
        :type message: Message
        """

        # Get the identity and the plugin ID.
        identity  = message.ack_identity
        plugin_id = message.plugin_id

        # Only ACKs for data messages carry the identity.
        if identity:

            try:

                # Only ACKs for plugin messages carry the plugin ID.
                if plugin_id:

                    # Add the plugin to the already processed set.
                    self.database.mark_plugin_finished(identity, plugin_id)

                    # Remove the plugin from the currently processing data map.
                    try:
                        self.__processing[identity].remove(plugin_id)
                    except KeyError:
                        msg = "Got an unexpected ACK" \
                              " for data ID %s from plugin %s"
                        warn(msg % (identity, plugin_id))

                    # Notify the Orchestrator that the plugin has finished.
                    if message.message_info: # 'do_notify_end' flag
                        msg = Message(
                            message_type = MessageType.MSG_TYPE_STATUS,
                            message_code = MessageCode.MSG_STATUS_PLUGIN_END,
                               plugin_id = plugin_id,
                              audit_name = self.audit.name,
                            ack_identity = identity,
                                priority = MessagePriority.MSG_PRIORITY_MEDIUM,
                        )
                        self.orchestrator.dispatch_msg(msg)

            finally:

                # If the stage was finished, mark it so.
                if self.__has_finished_stage(identity):
                    self.database.mark_stage_finished(identity,
                                                      self.current_stage)

        # Send the plugin end notification for report and import plugins.
        elif (
            plugin_id and
            plugin_id.split("/", 1)[0] in ("import", "report")
        ):
            if message.message_info: # 'do_notify_end' flag
                msg = Message(
                    message_type = MessageType.MSG_TYPE_STATUS,
                    message_code = MessageCode.MSG_STATUS_PLUGIN_END,
                       plugin_id = plugin_id,
                      audit_name = self.audit.name,
                        priority = MessagePriority.MSG_PRIORITY_MEDIUM,
                )
                self.orchestrator.dispatch_msg(msg)


    #--------------------------------------------------------------------------
    def __has_finished_stage(self, identity):

        # XXX FIXME this is very inefficient!
        # this may be fixed by using just the data type
        # instead of the whole data object

        # Get the data object.
        data = self.database.get_data(identity)

        # Get the candidate plugins.
        pending_plugins = self.get_candidate_plugins(data)

        # If there are no plugins pending execution, we finished the stage.
        return not pending_plugins


    #--------------------------------------------------------------------------
    def get_candidate_plugins(self, data):
        """
        Get the set of IDs of plugins that may handle this data object
        at the current execution stage.

        This ignores the plugin-to-plugin dependencies.

        :param data: Data object to find candidate plugins for.
        :type data: Data

        :returns: Set of candidate plugin IDs.
        :rtype: set(str)
        """

        # Get the whole set of plugins that can handle this data.
        next_plugins = super(AuditNotifier, self).get_plugins_to_notify(data)

        # Filter out plugins that already received this data.
        past_plugins = self.database.get_past_plugins(data.identity)
        next_plugins.difference_update(past_plugins)

        # Filter out plugins that don't belong to the current stage.
        stage_plugins = self.pluginManager.stages[self.current_stage]
        next_plugins.intersection_update(stage_plugins)

        # Return them.
        return next_plugins


    #--------------------------------------------------------------------------
    def is_runnable_stage(self, datalist, stage):
        """
        Determine if the given stage has any plugins that can handle the
        pending data.

        :param datalist: List of pending data.
        :type datalist: list(Data)

        :param stage: Current stage.
        :type stage: int

        :returns:
            True if the stage has plugins that can handle the data,
            False otherwise.
        :rtype: bool
        """

        # Early exit if the list of data objects is empty.
        if not datalist:
            return False

        # Make a copy of the set of plugin IDs for this stage.
        available = set( self.pluginManager.stages[stage] )

        # Early exit if the stage is empty.
        if not available:
            return False

        # For each data object...
        for data in datalist:

            # If we have plugins in this stage that can handle this data,
            # then we can run this stage.
            candidates = self.get_candidate_plugins(data)
            if isinstance(data, Relationship):
                candidates.update(self.get_candidate_plugins(data.invert()))
            if candidates.intersection(available):
                return True

        # If we reached this point that means we don't have any plugins
        # that can handle any of the data, so we skip the stage.
        return False


    #--------------------------------------------------------------------------
    def get_plugins_to_notify(self, data):
        """
        Get the plugins that are ready to handle the given data.

        :param data: Data to be handled.
        :type data: Data

        :returns: Set of plugin IDs.
        :rtype: set(str)
        """

        # Get the candidate plugins.
        next_plugins = self.get_candidate_plugins(data)

        # NOTE: the order of the following to filters is important!

        # Filter out plugins not belonging to the current batch.
        next_plugins = self.pluginManager.next_concurrent_plugins(next_plugins)

        # Filter out the currently running plugins.
        next_plugins.difference_update(self.__processing[data.identity])

        # Return the remanining plugins, if any.
        return next_plugins


    #--------------------------------------------------------------------------
    def __run_plugin(self, plugin, method, payload):
        """
        Send messages or information to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param method: Callback method name.
        :type method: str

        :param payload: Message or information to send to plugins.
        :type payload: Message or data

        :raises RuntimeError: The plugin doesn't support the method.
        """

        # If the plugin doesn't support the callback method, drop the message.
        if not hasattr(plugin, method):
            msg = "Tried to run plugin %r but it has no method %r"
            raise RuntimeError(msg % (plugin, method))

        # Get the Audit and Orchestrator instances.
        audit        = self.__audit
        orchestrator = audit.orchestrator

        # If it's a data message...
        if method == "run":

            # Get the payload identity hash.
            ack_identity = payload.identity

            # Check the maximum recursion depth.
            # We don't want to spider the leaf nodes, so we need a special
            # case for the Spider plugin.
            depth = audit.config.depth
            if depth is not None and payload.depth >= depth:
                skip_run = True
                plugin_id = audit.pluginManager.\
                                get_plugin_info_from_instance(plugin)[0]
                if payload.depth == depth and \
                                plugin_id != "testing/recon/spider":
                    skip_run = False
                if skip_run:

                    # If we reached the limit, send a fake ACK message.
                    # This keeps the Orchestrator and the Audit happy.
                    self.__processing[ack_identity].add(plugin_id)
                    orchestrator.enqueue_msg(Message(
                        message_type = MessageType.MSG_TYPE_CONTROL,
                        message_code = MessageCode.MSG_CONTROL_ACK,
                        message_info = False, # do not notify end of execution
                          audit_name = audit.name,
                           plugin_id = plugin_id,
                        ack_identity = ack_identity,
                            priority = MessagePriority.MSG_PRIORITY_LOW,
                    ))

                    # Skip execution of this plugin.
                    return

            # Prepare the context for the plugin execution.
            context = orchestrator.build_plugin_context(
                audit.name, plugin, ack_identity
            )

            # Add the plugin to the currently processing data map.
            self.__processing[ack_identity].add(context.plugin_id)

        # If it's any other message type...
        else:

            # Prepare the context for the plugin execution.
            context = orchestrator.build_plugin_context(
                audit.name, plugin, None
            )

        #
        # XXXXXXXXXXXXXXXXXXXXXXX NOTE XXXXXXXXXXXXXXXXXXXXXXX
        #
        # We currently don't check for errors below,
        # because if we fail to execute plugins then we
        # shut down the Orchestrator anyway.
        #
        # When we implement the NodeManager we'll probably
        # want to review this, since a single node going down
        # shouldn't cause the Orchestrator to go down as well.
        # We'll probably have to fake an ACK on error here.
        #

        # Run the callback in a pooled process.
        orchestrator.processManager.run_plugin(
            context, method, (payload,), {})


    #--------------------------------------------------------------------------
    def dispatch_data(self, plugin, audit_name, message_info):
        """
        Send information to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param audit_name: Audit name.
        :type audit_name: str

        :param message_info: Data to send to plugins.
        :type message_info: Data
        """

        # Validate the audit name.
        if audit_name is not None and audit_name != self.__audit.name:
            raise ValueError("Wrong audit! %r != %r" % (audit_name, self.__audit.name))

        # Run the plugin.
        self.__run_plugin(plugin, "run", message_info)


    #--------------------------------------------------------------------------
    def dispatch_msg(self, plugin, message):
        """
        Send messages to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param message: Message to send to plugins.
        :type message: Message
        """
        self.__run_plugin(plugin, "recv_msg", message)


    #--------------------------------------------------------------------------
    def start_report(self, plugin, output_file):
        """
        Start an audit report.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param output_file: Output file where the report will be written.
        :type output_file: str
        """
        self.__run_plugin(plugin, "generate_report", output_file)


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this notifier.
        """
        self.__audit = None
        self.__processing = None
        super(AuditNotifier, self).close()


#------------------------------------------------------------------------------
class OrchestratorNotifier(AbstractNotifier):
    """
    Dispatcher of messages for special plugins that run in the same process
    as the Orchestrator, instead of running in a background process.
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator
        """
        super(OrchestratorNotifier, self).__init__()
        self.__orchestrator = orchestrator


    #--------------------------------------------------------------------------
    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__orchestrator


    #--------------------------------------------------------------------------
    def dispatch_data(self, plugin, audit_name, message_info):
        """
        Send information to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param audit_name: Audit name.
        :type audit_name: str

        :param message_info: Data to send to plugins.
        :type message_info: Data
        """
        self.__run_plugin(plugin, audit_name, "run", message_info)


    #--------------------------------------------------------------------------
    def dispatch_msg(self, plugin, message):
        """
        Send messages to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param message: Message to send to plugins.
        :type message: Message
        """
        self.__run_plugin(plugin, message.audit_name, "recv_msg", message)


    #--------------------------------------------------------------------------
    def start_report(self, plugin, audit_name, output_file):
        """
        Start an audit report.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param audit_name: Audit name.
        :type audit_name: str

        :param output_file: Output file where the report will be written.
        :type output_file: str
        """
        self.__run_plugin(plugin, audit_name, "generate_report", output_file)


    #--------------------------------------------------------------------------
    def __run_plugin(self, plugin, audit_name, method, payload):
        """
        Send messages or information to the plugins.

        :param plugin: Target plugin.
        :type plugin: Plugin

        :param method: Callback method name.
        :type method: str

        :param payload: Message or data to send to plugins.
        :type payload: Message or Data
        """

        # If the plugin doesn't support the callback method, drop the message.
        # XXX FIXME: maybe we want to raise an exception here instead.
        if not hasattr(plugin, method):
            return

        # Check the audit still exists.
        if audit_name is not None:
            try:
                audit = self.orchestrator.auditManager.get_audit(audit_name)
            except KeyError:
                audit = None
            if not audit:
                warn("Tried to run a plugin from a finished audit! %s"
                     % audit_name,
                     RuntimeWarning)
                return

        # Prepare the plugin execution context.
        context = self.orchestrator.build_plugin_context(
            audit_name, plugin,
            payload.identity if method == "run" else None
        )

        # Run the callback directly in our process.
        try:
            old_context = Config._context
            try:
                Config._context = context
                getattr(plugin, method)(payload)
            finally:
                Config._context = old_context

        # Log exceptions thrown by the plugins.
        except Exception:
            ##raise                                                 # XXX DEBUG
            msg = "Plugin %s raised an exception:\n%s"
            msg = msg % (plugin.__class__.__name__, format_exc())
            ##Logger.log_error(msg)
            print msg   # it's safer to print, avoids possible infinite loops


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this notifier.
        """
        self.__orchestrator = None
        super(OrchestratorNotifier, self).close()
