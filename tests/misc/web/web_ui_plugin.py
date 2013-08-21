#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: https://github.com/golismero
Golismero project mail: golismero.project<@>gmail.com

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

from golismero.api.audit import start_audit, stop_audit, \
     get_audit_names, get_audit_config
from golismero.api.data import Data
from golismero.api.data.db import Database
from golismero.api.config import Config, get_orchestrator_config
from golismero.api.logger import Logger
from golismero.api.plugin import UIPlugin, get_plugin_info, get_plugin_names
from golismero.common import AuditConfig
from golismero.messaging.message import Message
from golismero.messaging.codes import MessageType, MessageCode, \
     MessagePriority

import collections
import multiprocessing
import time
import threading
import warnings

# Import the Django <-> GoLismero bridge.
from imp import load_source
from os.path import abspath, join, split
django_bridge = load_source(
    "django_bridge",
    abspath(join(split(__file__)[0], "django_bridge.py")))
)


#------------------------------------------------------------------------------
class WebUIPlugin(UIPlugin):
    """
    Web UI plugin.
    """


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        "This method tells the Orchestrator we don't want to receive any Data."
        return []


    #--------------------------------------------------------------------------
    def recv_info(self, info):
        "This method won't be called, because we don't receive any Data."
        pass


    #--------------------------------------------------------------------------
    def recv_msg(self, message):
        """
        This method receives messages from the Orchestrator, parses them, and
        calls the appropriate notification methods defined below.

        :param message: Message received from the Orchestrator.
        :type message: Message
        """

        # Control messages.
        if message.message_type == MessageType.MSG_TYPE_CONTROL:

            # This UI plugin must be started.
            if message.message_code == MessageCode.MSG_CONTROL_START_UI:
                self.start_ui()

            # This UI plugin must be shut down.
            elif message.message_code == MessageCode.MSG_CONTROL_STOP_UI:
                self.stop_ui()

            # An audit has started.
            elif message.message_code == MessageCode.MSG_CONTROL_START_AUDIT:
                self.notify_stage(message.audit_name, "start")

            # An audit has finished.
            elif message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT:
                self.notify_stage(message.audit_name,
                    "finish" if message.message_info else "cancel")

            # A plugin has sent a log message.
            elif message.message_code == MessageCode.MSG_CONTROL_LOG:
                plugin_name = self.get_plugin_name(message)
                (text, level, is_error) = message.message_info
                if is_error:
                    self.notify_error(message.audit_name, plugin_name, text, level)
                else:
                    self.notify_log(message.audit_name, plugin_name, text, level)

            # A plugin has sent an error message.
            elif message.message_code == MessageCode.MSG_CONTROL_ERROR:
                plugin_name = self.get_plugin_name(message)
                (description, traceback) = message.message_info
                text = "Error: " + description
                self.notify_error(message.audit_name, plugin_name, text, Logger.STANDARD)
                text = "Exception raised: %s\n%s" % (description, traceback)
                self.notify_error(message.audit_name, plugin_name, text, Logger.MORE_VERBOSE)

            # A plugin has sent a warning message.
            elif message.message_code == MessageCode.MSG_CONTROL_WARNING:
                plugin_name = self.get_plugin_name(message)
                for w in message.message_info:
                    formatted = warnings.formatwarning(w.message, w.category, w.filename, w.lineno, w.line)
                    text = "Warning: " + w.message
                    self.notify_warning(message.audit_name, plugin_name, text, Logger.STANDARD)
                    text = "Warning details: " + formatted
                    self.notify_warning(message.audit_name, plugin_name, text, Logger.MORE_VERBOSE)

        # Status messages.
        elif message.message_type == MessageType.MSG_TYPE_STATUS:

            # A plugin has started processing a Data object.
            if message.message_type == MessageCode.MSG_STATUS_PLUGIN_BEGIN:
                plugin_name = self.get_plugin_name(message)
                self.notify_progress(message.audit_name, plugin_name, message.message_info, 0.0)

            # A plugin has finished processing a Data object.
            elif message.message_type == MessageCode.MSG_STATUS_PLUGIN_END:
                plugin_name = self.get_plugin_name(message)
                self.notify_progress(message.audit_name, plugin_name, message.message_info, 100.0)

            # A plugin is currently processing a Data object.
            elif message.message_code == MessageCode.MSG_STATUS_PLUGIN_STEP:
                plugin_name = self.get_plugin_name(message)
                identity, progress = message.message_info
                self.notify_progress(message.audit_name, plugin_name, identity, progress)

            # An audit has switched to another execution stage.
            elif message.message_code == MessageCode.MSG_STATUS_STAGE_UPDATE:
                self.notify_stage(message.audit_name, message.message_info)


    #--------------------------------------------------------------------------
    @staticmethod
    def get_plugin_name(message):
        """
        Helper method to get a user-friendly name
        for the plugin that sent a given message.

        :param message: Message sent by a plugin.
        :type message: Message

        :returns: User-friendly name for the plugin.
        :rtype: str
        """
        if message.plugin_name:
            plugin_info = get_plugin_info(message.plugin_name)
            if plugin_info:
                return plugin_info.display_name
        return "GoLismero"


    #--------------------------------------------------------------------------
    def start_ui(self):
        """
        This method is called when the UI start message arrives.
        It reads the plugin configuration, starts the consumer thread, and
        launches the Django web application.
        """

        # Initialize the audit and plugin state caches.
        self.state_lock   = threading.RLock()
        self.audit_state  = {}  # audit -> stage
        self.plugin_state = collections.defaultdict(
            collections.defaultdict(dict)
        )  # audit -> (plugin, identity) -> progress

        # Create the consumer thread object.
        self.thread_continue = True
        self.thread = threading.Thread(
            target = self.consumer_thread,
            kwargs = {"context" : Config._context}
        )
        self.thread.daemon = True

        # Get the configuration.
        orchestrator_config = get_orchestrator_config().to_dictionary()
        plugin_config       = Config.plugin_config
        plugin_extra_config = Config.plugin_extra_config

        # Launch the Django web application.
        self.bridge = django_bridge.launch_django()

        # Start the consumer thread.
        self.thread.start()


    #--------------------------------------------------------------------------
    def stop_ui(self):
        """
        This method is called when the UI stop message arrives.
        It shuts down the web UI.
        """

        # Tell the consumer thread to stop.
        self.thread_continue = False

        # Tell the Django application to stop.
        try:
            self.bridge.send( ("stop",) )
        except:
            pass

        # Shut down the communication pipe.
        # This should wake up the consumer thread.
        self.bridge.close()

        # Wait for the consumer thread to stop.
        if self.thread.isAlive():
            self.thread.join(2.0)

        # If a timeout occurs...
        if self.thread.isAlive():

            # Forcefully kill the thread. Ignore errors.
            # http://stackoverflow.com/a/15274929/426293
            import ctypes
            exc = ctypes.py_object(KeyboardInterrupt)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.thread.ident), exc)
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(self.thread.ident), None)

            # Wait again.
            try:
                self.thread.join(2.0)
            except:
                pass

        # Clear the state cache.
        self.state_lock = threading.RLock()
        self.audit_state.clear()
        self.plugin_state.clear()


    #--------------------------------------------------------------------------
    def consumer_thread(self, context):
        """
        This method implements the consumer thread code: it reads data sent by
        the Django application though a pipe, and sends the appropriate
        messages to the Orchestrator.
        """

        try:

            # Initialize the plugin execution context.
            Config._context = context

            # Loop until they tell us to quit.
            while self.thread_continue:

                # Read the next packet from the pipe.
                try:
                    packet = self.parent_conn.recv()
                except Exception:
                    continue

                # Success responses start with "ok",
                # failure responses start with "fail".
                response = ("ok",)

                try:

                    # The first field is always the command.
                    # The rest are the arguments.
                    command   = packet[0]
                    arguments = packet[1:]

                    # Special command "fail" means the Django app died.
                    if command == "fail":

                        # Stop GoLismero.
                        self.do_admin_service_stop()

                        # Kill the consumer thread.
                        break

                    # Parse the command to get the method name.
                    # The command is the path to the webservice.
                    while "//" in command:
                        command = command.replace("//", "/")
                    if command.startswith("/"):
                        command = command[1:]
                    if command.endswith("/"):
                        command = command[:-1]
                    command = "do_" + command.replace("/", "_")

                    # Get the method that implements the command.
                    # Fail if it doesn't exist.
                    try:
                        method = getattr(self, command)
                    except AttributeError:
                        raise NotImplementedError()

                    # Run the command and get the response.
                    retval = method( *arguments )
                    if retval:
                        if type(retval) is tuple:
                            response = response + retval
                        else:
                            response = response + (retval,)

                # On error send an failure response.
                except Exception, e:
                    self.bridge.send( ("fail", str(e)) )
                    continue

                # On success send the response.
                self.bridge.send(response)

        # This catch prevents exceptions from being shown in stderr.
        except:
            raise # XXX DEBUG
            pass


    #--------------------------------------------------------------------------
    #
    # Notification methods
    # ====================
    #
    # They run in the context of the main thread, invoked from recv_msg().
    #
    #--------------------------------------------------------------------------


    #--------------------------------------------------------------------------
    def notify_log(self, audit_name, plugin_name, text, level):
        """
        This method is called when a plugin sends a log message.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin_name: Name of the plugin.
        :type plugin_name: str

        :param text: Log text.
        :type text: str

        :param level: Log level (0 through 3).
        :type level: int
        """
        packet = ("log", audit_name, plugin_name, text, level)
        self.bridge.send(packet)


    #--------------------------------------------------------------------------
    def notify_error(self, audit_name, plugin_name, text, level):
        """
        This method is called when a plugin sends an error message.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin_name: Name of the plugin.
        :type plugin_name: str

        :param text: Log text.
        :type text: str

        :param level: Log level (0 through 3).
        :type level: int
        """
        packet = ("error", audit_name, plugin_name, text, level)
        self.bridge.send(packet)


    #--------------------------------------------------------------------------
    def notify_warning(self, audit_name, plugin_name, text, level):
        """
        This method is called when a plugin sends a warning message.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin_name: Name of the plugin.
        :type plugin_name: str

        :param text: Log text.
        :type text: str

        :param level: Log level (0 through 3).
        :type level: int
        """
        packet = ("warn", audit_name, plugin_name, text, level)
        self.bridge.send(packet)


    #--------------------------------------------------------------------------
    def notify_progress(self, audit_name, plugin_name, identity, progress):
        """
        This method is called when a plugin sends a status update.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin_name: Name of the plugin.
        :type plugin_name: str

        :param identity: Identity hash of the Data object being processed.
        :type identity: str

        :param progress: Progress percentage (0.0 through 100.0).
        :type progress: float
        """

        # Save the plugin state.
        self.plugin_state[audit_name][(plugin_name, identity)] = progress

        # Send the plugin state.
        packet = ("progress", audit_name, plugin_name, identity, progress)
        self.bridge.send(packet)


    #--------------------------------------------------------------------------
    def notify_stage(self, audit_name, stage):
        """
        This method is called when an audit moves to another execution stage.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param stage: Name of the execution stage.
            Must be one of the following:
             - "start" - The audit has just started.
             - "import" - Importing external data into the database.
             - "recon" - Performing reconnaisance on the targets.
             - "scan" - Scanning the targets for vulnerabilities.
             - "attack" - Attacking the target using the vulnerabilities found.
             - "intrude" - Gathering information after a successful attack.
             - "cleanup" - Cleaning up after an attack.
             - "report" - Generating a report for the audit.
             - "finish" - The audit has finished.
             - "cancel" - The audit has been canceled by the user.
        :type stage: str
        """

        # Save the audit state.
        self.audit_state[audit_name] = stage

        # Send the audit state.
        packet = ("stage", audit_name, stage)
        self.bridge.send(packet)


    #--------------------------------------------------------------------------
    #
    # Command methods
    # ===============
    #
    # They run in background, invoked by consumer_thread().
    #
    #--------------------------------------------------------------------------


    #--------------------------------------------------------------------------
    def do_scan_create(self, audit_config):
        """
        Implementation of: /scan/create

        :param audit_config: Audit configuration.
        :type audit_config: dict(str -> \\*)
        """

        # Load the audit configuration from the dictionary.
        o_audit_config = AuditConfig()
        o_audit_config.from_dictionary(audit_config)

        # Create the new audit.
        start_audit(o_audit_config)


    #--------------------------------------------------------------------------
    def do_scan_cancel(self, audit_name):
        """
        Implementation of: /scan/cancel

        :param audit_name: Name of the audit to cancel.
        :type audit_name: str
        """

        # Stop the audit.
        stop_audit(audit_name)


    #--------------------------------------------------------------------------
    def do_scan_list(self):
        """
        Implementation of: /scan/list

        :returns: Dictionary mapping audit names to their configurations.
        :rtype: dict(str -> dict(str -> \\*))
        """
        result = {}
        for audit_name in get_audit_names():
            audit_config = get_audit_config(audit_name)
            result[audit_name] = audit_config.to_dictionary()
        return result


    #--------------------------------------------------------------------------
    def do_scan_state(self, audit_name):
        """
        Implementation of: /scan/state

        :param audit_name: Name of the audit to query.
        :type audit_name: str

        :returns: Current audit stage, followed by the progress status of
            every plugin (plugin name, data identity, progress percentage).
        :rtype: tuple(int, tuple( tuple(str, str, float) ... ))
        """

        # Return the current stage and the status of every plugin.
        return (
            self.audit_state[audit_name],
            tuple(
                (plugin_name, identity, progress)
                for ((plugin_name, identity), progress)
                in self.plugin_state[audit_name].iteritems()
            )
        )


    #--------------------------------------------------------------------------
    def do_scan_results(self, data_type = "all"):
        """
        Implementation of: /scan/results

        :param data_type: Data type to request. Case insensitive.
            Must be one of the following values:
             - "all": All data types.
             - "information": Information type.
             - "resource": Resource type.
             - "vulnerability": Vulnerability type.
        :type data_type: str

        :returns: Result IDs.
        :rtype: list(str)

        :raises KeyError: Data type unknown.
        """
        i_data_type = {
                      "all": None,
              "information": Data.TYPE_INFORMATION,
                 "resource": Data.TYPE_RESOURCE,
            "vulnerability": Data.TYPE_VULNERABILITY,
        }[data_type.strip().lower()]
        return sorted( Database.keys(i_data_type) )


    #--------------------------------------------------------------------------
    def do_scan_details(self, id_list):
        """
        Implementation of: /scan/details

        :param id_list: List of result IDs.
        :type id_list: list(str)
        """
        return Database.get_many(id_list)


    #--------------------------------------------------------------------------
    def do_plugin_list(self):
        """
        Implementation of: /plugin/list

        :returns: List of plugin names.
        :rtype: list(str)
        """
        return sorted( get_plugin_names() )


    #--------------------------------------------------------------------------
    def do_plugin_details(self, plugin_name):
        """
        Implementation of: /plugin/details

        :param plugin_name: Name of the plugin to query.
        :type plugin_name: str

        :returns: Plugin information.
        :rtype: PluginInfo
        """
        return get_plugin_info(plugin_name)    # XXX TODO encode as JSON


    #--------------------------------------------------------------------------
    def do_admin_service_stop(self):
        """
        Implementation of: /admin/service/stop
        """
        Config._context.send_msg(
            message_type = MessageType.MSG_TYPE_CONTROL,
            message_code = MessageCode.MSG_CONTROL_STOP,
            message_info = False,    # True for finished, False for user cancel
                priority = MessagePriority.MSG_PRIORITY_LOW
        )


    #--------------------------------------------------------------------------
    def do_admin_config_details(self):
        """
        Implementation of: /admin/config/details

        :returns: Orchestrator configuration.
        :rtype: dict(str -> \\*)
        """
        return get_orchestrator_config().to_dictionary()
