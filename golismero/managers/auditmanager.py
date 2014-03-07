#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager for audits.
"""

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

__all__ = ["AuditManager", "Audit", "AuditException"]

from .importmanager import ImportManager
from .processmanager import PluginContext
from .reportmanager import ReportManager
from .rpcmanager import implementor
from ..api.data import Data
from ..api.data.resource.domain import Domain
from ..api.data.resource.ip import IP
from ..api.data.resource.url import URL, FolderURL, BaseURL
from ..api.config import Config
from ..api.logger import Logger
from ..api.plugin import STAGES
from ..common import AuditConfig
from ..database.auditdb import AuditDB
from ..main.scope import AuditScope, DummyScope
from ..messaging.codes import MessageType, MessageCode, MessagePriority
from ..messaging.message import Message
from ..messaging.notifier import AuditNotifier

from collections import defaultdict
from warnings import catch_warnings, warn
from time import time
from traceback import format_exc


#------------------------------------------------------------------------------
# RPC implementors for the audit manager API.

@implementor(MessageCode.MSG_RPC_AUDIT_COUNT)
def rpc_audit_get_count(orchestrator, current_audit_name):
    return orchestrator.auditManager.get_audit_count()

@implementor(MessageCode.MSG_RPC_AUDIT_NAMES)
def rpc_audit_get_names(orchestrator, current_audit_name):
    return orchestrator.auditManager.get_audit_names()

@implementor(MessageCode.MSG_RPC_AUDIT_CONFIG)
def rpc_audit_get_config(orchestrator, current_audit_name, audit_name = None):
    if audit_name:
        return orchestrator.auditManager.get_audit(audit_name).config
    return orchestrator.config

@implementor(MessageCode.MSG_RPC_AUDIT_TIMES)
def rpc_audit_get_times(orchestrator, current_audit_name, audit_name = None):
    if not audit_name:
        audit_name = current_audit_name
    return orchestrator.auditManager.get_audit(audit_name).database.get_audit_times()

@implementor(MessageCode.MSG_RPC_AUDIT_STATS)
def rpc_audit_get_stats(orchestrator, current_audit_name, audit_name = None):
    if not audit_name:
        audit_name = current_audit_name
    return orchestrator.auditManager.get_audit(audit_name).get_runtime_stats()

@implementor(MessageCode.MSG_RPC_AUDIT_SCOPE)
def rpc_audit_get_scope(orchestrator, current_audit_name, audit_name = None):
    if audit_name:
        return orchestrator.auditManager.get_audit(audit_name).scope
    return DummyScope()


#------------------------------------------------------------------------------
class AuditException(Exception):
    """Exception for audits"""


#------------------------------------------------------------------------------
class AuditManager (object):
    """
    Manage and control audits.
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Core to send messages to.
        :type orchestrator: Orchestrator
        """

        # Create the dictionary where we'll store the Audit objects.
        self.__audits = dict()

        # Keep a reference to the Orchestrator.
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
    def new_audit(self, audit_config):
        """
        Creates a new audit.

        :param audit_config: Parameters of the audit.
        :type audit_config: AuditConfig

        :returns: Newly created audit.
        :rtype: Audit
        """
        if not isinstance(audit_config, AuditConfig):
            raise TypeError(
                "Expected AuditConfig, got %r instead" % type(audit_config))

        # Check the audit config against the UI plugin.
        self.orchestrator.uiManager.check_params(audit_config)

        # Create the audit.
        audit = Audit(audit_config, self.orchestrator)

        # Store it.
        self.__audits[audit.name] = audit

        # Log the event.
        if audit.is_new:
            Logger.log("Audit name: %s" % audit.name)
        else:
            Logger.log_verbose("Audit name: %s" % audit.name)
        if (hasattr(audit.database, "filename") and
            audit.database.filename != ":memory:"
        ):
            Logger.log_verbose("Audit database: %s" % audit.database.filename)

        # Run!
        try:
            audit.run()

            # Return it.
            return audit

        # On error, abort.
        except Exception, e:
            tb = format_exc()
            try:
                self.remove_audit(audit.name)
            except Exception:
                pass
            Logger.log_error(str(e))
            Logger.log_error_more_verbose(tb)
            raise AuditException("Failed to add new audit, reason: %s" % e)


    #--------------------------------------------------------------------------
    def get_audit_count(self):
        """
        Get the number of currently running audits.

        :returns: Number of currently running audits.
        :rtype: int
        """
        return len(self.__audits)


    #--------------------------------------------------------------------------
    def get_audit_names(self):
        """
        Get the names of the currently running audits.

        :returns: Audit names.
        :rtype: set(str)
        """
        return {audit.name for audit in self.__audits}


    #--------------------------------------------------------------------------
    def get_all_audits(self):
        """
        Get the currently running audits.

        :returns: Mapping of audit names to instances.
        :rtype: dict(str -> Audit)
        """
        return self.__audits


    #--------------------------------------------------------------------------
    def has_audit(self, name):
        """
        Check if there's an audit with the given name.

        :param name: Audit name.
        :type name: str

        :returns: True if the audit exists, False otherwise.
        :rtype: bool
        """
        return name in self.__audits


    #--------------------------------------------------------------------------
    def get_audit(self, name):
        """
        Get an instance of an audit by its name.

        :param name: Audit name.
        :type name: str

        :returns: Audit instance.
        :rtype: Audit

        :raises KeyError: No audit exists with that name.
        """
        return self.__audits[name]


    #--------------------------------------------------------------------------
    def remove_audit(self, name):
        """
        Delete an instance of an audit by its name.

        :param name: Audit name.
        :type name: str

        :raises KeyError: No audit exists with that name.
        """
        try:
            self.orchestrator.netManager.release_all_slots(name)
        finally:
            try:
                audit = self.__audits[name]
                try:
                    audit.close()
                finally:
                    del self.__audits[name]
            finally:
                self.orchestrator.cacheManager.clean(name)


    #--------------------------------------------------------------------------
    def dispatch_msg(self, message):
        """
        Process an incoming message from the Orchestrator.

        :param message: Incoming message.
        :type message: Message
        """

        # Type check.
        if not isinstance(message, Message):
            raise TypeError(
                "Expected Message, got %r instead" % type(message))

        # Send data messages to their target audit.
        if message.message_type == MessageType.MSG_TYPE_DATA:
            if not message.audit_name:
                raise ValueError("Data message with no target audit!")
            self.get_audit(message.audit_name).dispatch_msg(message)

        # Process control messages.
        elif message.message_type == MessageType.MSG_TYPE_CONTROL:

            # Send ACKs to their target audit.
            if message.message_code == MessageCode.MSG_CONTROL_ACK:
                if message.audit_name:
                    self.get_audit(message.audit_name).acknowledge(message)

            # Start an audit if requested.
            elif message.message_code == MessageCode.MSG_CONTROL_START_AUDIT:
                try:
                    self.new_audit(message.message_info)
                except AuditException, e:
                    tb = format_exc()
                    message = Message(
                        message_type = MessageType.MSG_TYPE_STATUS,
                        message_code = MessageCode.MSG_STATUS_AUDIT_ABORTED,
                        message_info = (message.message_info.audit_name,
                                        str(e), tb),
                            priority = MessagePriority.MSG_PRIORITY_HIGH,
                          audit_name = None,
                    )
                    self.orchestrator.enqueue_msg(message)

            # Stop an audit if requested.
            elif message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT:
                if not message.audit_name:
                    raise ValueError("I don't know which audit to stop...")
                self.get_audit(message.audit_name).close()
                self.remove_audit(message.audit_name)

            # Send log messages to their target audit.
            elif message.message_code == MessageCode.MSG_CONTROL_LOG:
                if message.audit_name:
                    self.get_audit(message.audit_name).dispatch_msg(message)


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by all audits.
        """
        self.__orchestrator = None
        for name in self.__audits.keys(): # not iterkeys, will be modified
            try:
                self.remove_audit(name)
            except:
                pass


#------------------------------------------------------------------------------
class Audit (object):
    """
    Instance of an audit, with its custom parameters,
    scope, target, plugins, etc.
    """


    #--------------------------------------------------------------------------
    def __init__(self, audit_config, orchestrator):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig

        :param orchestrator: Orchestrator instance that will receive messages
            sent by this audit.
        :type orchestrator: Orchestrator
        """

        if not isinstance(audit_config, AuditConfig):
            raise TypeError(
                "Expected AuditConfig, got %r instead" % type(audit_config))

        # Keep the audit settings.
        self.__audit_config = audit_config

        # Keep a reference to the Orchestrator.
        self.__orchestrator = orchestrator

        # Set the current stage to the first stage.
        self.__current_stage = orchestrator.pluginManager.min_stage

        # Initialize the "report started" flag.
        self.__is_report_started = False

        # Initialize the "ran new tests" flag.
        self.__must_update_stop_time = True

        # Maximum number of links to follow.
        self.__followed_links = 0
        self.__show_max_links_warning = True

        # Number of unacknowledged messages.
        self.__expecting_ack = 0

        # Counters used to collect runtime statistics.
        self.__stage_cycles = defaultdict(int) # stage -> counter
        self.__processed_count = 0
        self.__total_count = 0
        self.__stages_enabled = tuple()

        # Initialize the managers to None.
        self.__notifier = None
        self.__plugin_manager = None
        self.__import_manager = None
        self.__report_manager = None

        # Create or open the database.
        self.__is_new = not audit_config.audit_name or \
                        audit_config.audit_db == ":auto:"
        self.__database = AuditDB(audit_config)
        self.__database.append_log_line("Audit started.", Logger.MORE_VERBOSE)

        # Set the audit name.
        self.__name = self.__database.audit_name


    #--------------------------------------------------------------------------

    @property
    def name(self):
        """
        :returns: Name of the audit.
        :rtype: str
        """
        return self.__name

    @property
    def is_new(self):
        """
        :returns: True if the audit is new, False if it's a reopened audit.
        :rtype: bool
        """
        return self.__is_new

    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance that will receive messages
            sent by this audit.
        :rtype: Orchestrator
        """
        return self.__orchestrator

    @property
    def config(self):
        """
        :returns: Audit configuration.
        :rtype: AuditConfig
        """
        return self.__audit_config

    @property
    def scope(self):
        """
        :returns: Audit scope.
        :rtype: AuditScope
        """
        return self.__audit_scope

    @property
    def database(self):
        """
        :returns: Audit database.
        :rtype: AuditDB
        """
        return self.__database

    @property
    def pluginManager(self):
        """
        :returns: Audit plugin manager.
        :rtype: AuditPluginManager
        """
        return self.__plugin_manager

    @property
    def importManager(self):
        """
        :returns: Import manager.
        :rtype: ImportManager
        """
        return self.__import_manager

    @property
    def reportManager(self):
        """
        :returns: Report manager.
        :rtype: ReportManager
        """
        return self.__report_manager


    #--------------------------------------------------------------------------

    @property
    def expecting_ack(self):
        """
        :returns: Number of ACKs expected by this audit.
        :rtype: int
        """
        return self.__expecting_ack

    @property
    def current_stage(self):
        """
        :returns: Current execution stage.
        :rtype: int
        """
        return self.__current_stage

    @property
    def is_report_started(self):
        """
        :returns: True if report generation has started, False otherwise.
        :rtype: bool
        """
        return self.__is_report_started


    #--------------------------------------------------------------------------
    def inc_expected_ack(self, count = 1):
        """
        Increase the number of expected ACK messages.

        :param count: How many new messages to expect.
        :type count: int
        """
        self.__expecting_ack += count

        # XXX DEBUG
        if self.orchestrator.messageManager.DEBUG:
            print "EXPECTING ACK %d => %s" % (
                self.__expecting_ack - count, self.__expecting_ack)


    #--------------------------------------------------------------------------
    def dec_expected_ack(self, count = 1):
        """
        Decrease the number of expected ACK messages.

        :param count: How many ACK messages have arrived.
        :type count: int
        """
        self.__expecting_ack -= count

        # XXX DEBUG
        if self.orchestrator.messageManager.DEBUG:
            print "EXPECTING ACK %d => %s" % (
                self.__expecting_ack + count, self.__expecting_ack)


    #--------------------------------------------------------------------------
    def get_runtime_stats(self):
        """
        Returns a dictionary with runtime statistics with at least the
        following keys:

         - "current_stage": [int]
           Current stage number.
         - "total_count": [int]
           Total number of data objects to process in this stage.
         - "processed_count": [int]
           Number of data objects already processed in this stage.
         - "stage_cycles": [dict(int -> int)]
           Map of stage numbers and times each stage ran.
         - "stages_enabled": [tuple(int)]
           Stages enabled for this audit.

        Future versions of GoLismero may include more keys.

        :returns: Runtime statistics.
        :rtype: dict(str -> \\*)
        """
        return {
            "current_stage":     self.__current_stage,
            "total_count":       self.__total_count,
            "processed_count":   self.__processed_count,
            "stage_cycles":      dict(self.__stage_cycles),
            "stages_enabled":    self.__stages_enabled,
        }


    #--------------------------------------------------------------------------
    def run(self):
        """
        Start execution of an audit.
        """

        # Tentative audit start time.
        start_time = time()

        # Reset the number of unacknowledged messages.
        self.__expecting_ack = 0

        # Keep the original execution context.
        old_context = Config._context

        try:

            # Create a dummy scope.
            self.__audit_scope = DummyScope()

            # Update the execution context for this audit.
            Config._context = PluginContext(
                       msg_queue = old_context.msg_queue,
                         address = old_context.address,
                      audit_name = self.name,
                    audit_config = self.config,
                     audit_scope = self.scope,
                orchestrator_pid = old_context._orchestrator_pid,
                orchestrator_tid = old_context._orchestrator_tid)

            # Create the plugin manager for this audit.
            self.__plugin_manager = \
                self.orchestrator.pluginManager.get_plugin_manager_for_audit(
                    self)
            self.__plugin_manager.initialize(self.config)

            # Load the testing plugins.
            testing_plugins = self.pluginManager.load_plugins("testing")

            # Create the notifier.
            self.__notifier = AuditNotifier(self)

            # Register the testing plugins with the notifier.
            self.__notifier.add_multiple_plugins(testing_plugins)

            # Determine which stages are enabled for this run.
            self.__stages_enabled = sorted(
                stage_num
                for stage, stage_num in STAGES.iteritems()
                if self.pluginManager.get_plugins(stage)
            )

            # Create the import manager.
            self.__import_manager = ImportManager(self.orchestrator, self)

            # Create the report manager.
            self.__report_manager = ReportManager(self.orchestrator, self)

            # (Re)calculate the audit scope. Some DNS queries may be made.
            audit_scope = self.database.get_audit_scope()
            if audit_scope is None:
                if self.config.targets:
                    audit_scope = AuditScope(self.config)
            else:
                audit_scope.add_targets(self.config)
            if audit_scope is not None:
                self.__audit_scope = audit_scope
                self.database.save_audit_scope(self.scope)
                Config._context = PluginContext(
                                    msg_queue = old_context.msg_queue,
                                      address = old_context.address,
                                   audit_name = self.name,
                                 audit_config = self.config,
                                  audit_scope = self.scope,
                             orchestrator_pid = old_context._orchestrator_pid,
                             orchestrator_tid = old_context._orchestrator_tid)

            # If the audit database doesn't have a start time, set the new one.
            if not self.database.get_audit_times()[0]:
                self.database.set_audit_start_time(start_time)

            # Log the number of objects previously in the database.
            count = self.database.get_data_count()
            if count:
                Logger.log_verbose("Found %d objects in database" % count)

            # Add the targets to the database, but only if they're new.
            # (Makes sense when resuming a stopped audit).
            target_data = self.scope.get_targets()
            targets_added_count = 0
            for data in target_data:
                if not self.database.has_data_key(data.identity):
                    self.database.add_data(data)
                    targets_added_count += 1
            if targets_added_count:
                Logger.log_verbose(
                    "Added %d new targets to the database." %
                    targets_added_count)

            # Mark all data as having completed no stages.
            # This is needed because the plugin list may have changed.
            # Note that if a plugin already processed the data, this WON'T
            # cause the same data to be processed again by the same plugin.
            self.database.clear_all_stage_marks()

            # However, if the user requested a rescan, we do need to
            # reset the plugin history as well.
            if self.config.redo:
                self.database.clear_all_plugin_history()

            # Do we have any active importers?
            imported_count = 0
            if self.importManager.is_enabled:

                # Tell the UI we're about to run the import plugins.
                self.send_msg(
                    message_type = MessageType.MSG_TYPE_STATUS,
                    message_code = MessageCode.MSG_STATUS_STAGE_UPDATE,
                    message_info = "import",
                        priority = MessagePriority.MSG_PRIORITY_HIGH,
                )

                # Import external results.
                # This is done after storing the targets, so the importers
                # can overwrite the targets with new information if available.
                # If we had no scope, build one based on the imported data.
                if not target_data:
                    target_types = (
                        BaseURL.data_subtype,
                        FolderURL.data_subtype,
                        URL.data_subtype,
                        IP.data_subtype,
                        Domain.data_subtype,
                    )
                    old_data = set()
                    for data_subtype in target_types:
                        old_data.update(
                            self.database.get_data_keys(
                                Data.TYPE_RESOURCE, data_subtype) )
                imported_count = self.importManager.import_results()
                if not target_data:
                    new_data = set()
                    for data_subtype in target_types:
                        new_data.update(
                            self.database.get_data_keys(
                                Data.TYPE_RESOURCE, data_subtype) )
                    new_data.difference_update(old_data)
                    old_data.clear()
                    self.config.targets = [
                        str( self.database.get_data(identity) )
                        for identity in new_data
                    ]
                    new_data.clear()
                    self.__audit_scope = AuditScope(self.config) # uses DNS
                    self.database.save_audit_scope(self.scope)
                    Config._context = PluginContext(
                                    msg_queue = old_context.msg_queue,
                                      address = old_context.address,
                                   audit_name = self.name,
                                 audit_config = self.config,
                                  audit_scope = self.scope,
                             orchestrator_pid = old_context._orchestrator_pid,
                             orchestrator_tid = old_context._orchestrator_tid)
                    target_data = self.scope.get_targets()
                    targets_added_count = 0
                    for data in target_data:
                        if not self.database.has_data_key(data.identity):
                            self.database.add_data(data)
                            targets_added_count += 1
                    if targets_added_count:
                        Logger.log_verbose(
                            "Added %d new targets to the database." %
                            targets_added_count)

            # Show the scope. Abort if the scope is wrong.
            Logger.log_more_verbose(str(self.scope))
            assert not isinstance(self.scope, DummyScope), "Internal error!"
            if not self.scope.targets:
                raise ValueError(
                    "No targets selected for audit, aborting execution.")

            # Discover new data from the data already in the database.
            # Only add newly discovered data, to avoid overwriting anything.
            # XXX FIXME performance
            # XXX FIXME what about links?
            existing = self.database.get_data_keys()
            stack = list(existing)
            visited = set()
            while stack:
                identity = stack.pop()
                if identity not in visited:
                    visited.add(identity)
                    data = self.database.get_data(identity)
                    if data.is_in_scope(): # just in case...
                        for data in data.discovered:
                            identity = data.identity
                            if identity not in existing and data.is_in_scope():
                                self.database.add_data(data)
                                existing.add(identity)
                                stack.append(identity)
            del existing
            del visited

        finally:

            # Restore the original execution context.
            Config._context = old_context

        # The audit stop time must be updated if:
        # 1) Testing plugins were run, or
        # 2) There was new data added to the database.
        self.__must_update_stop_time = imported_count or targets_added_count

        # If there are testing plugins enabled, move to stage 1.
        if testing_plugins:
            Logger.log_verbose("Launching tests...")
            self.update_stage()

        # If not, go straight to the report stage.
        else:
            self.__current_stage = self.__plugin_manager.max_stage + 1
            self.generate_reports()


    #--------------------------------------------------------------------------
    def send_msg(self, message_type = MessageType.MSG_TYPE_DATA,
                       message_code = MessageCode.MSG_DATA_REQUEST,
                       message_info = None,
                       priority = MessagePriority.MSG_PRIORITY_MEDIUM):
        """
        Send messages to the Orchestrator.

        :param message_type: Message type.
            Must be one of the constants from MessageType.
        :type mesage_type: int

        :param message_code: Message code.
            Must be one of the constants from MessageCode.
        :type message_code: int

        :param message_info: The payload of the message.
            Its type depends on the message type and code.
        :type message_info: *

        :param priority: Priority level.
            Must be one of the constants from MessagePriority.
        :type priority: int
        """
        m = Message(message_type = message_type,
                    message_code = message_code,
                    message_info = message_info,
                      audit_name = self.name,
                        priority = priority)
        self.orchestrator.enqueue_msg(m)


    #--------------------------------------------------------------------------
    def acknowledge(self, message):
        """
        Got an ACK for a message sent from this audit to the plugins.

        :param message: The message with the ACK.
        :type message: Message
        """

        try:

            # Decrease the expected ACK count.
            # The audit manager will check when this reaches zero.
            self.dec_expected_ack()

            # Tell the notifier about this ACK.
            self.__notifier.acknowledge(message)

        finally:

            # Check for audit stage termination.
            #
            # NOTE: This check assumes messages always arrive in order,
            #       and ACKs are always sent AFTER responses from plugins.
            #
            if not self.expecting_ack:

                # Update the current stage.
                self.update_stage()


    #--------------------------------------------------------------------------
    def update_stage(self):
        """
        Sets the current stage to the minimum needed to process pending data.
        When the last stage is completed, sends the audit stop message.
        """

        # Get the database and the plugin manager.
        database = self.database
        pluginManager = self.pluginManager

        # If the reports are finished...
        if self.__is_report_started:

            #
            # Run the magic plugin "report/text" here, after all other
            # report plugins have finished running. This is needed so
            # the output from the screen report doesn't get mixed with
            # the log messages and errors from the other reporters.
            #
            # The text report plugin is run by the UI notifier instead
            # of the normal plugin notifier, so it runs in-process and
            # waits until the plugin is finished before returning.
            #
            # Note that for output text files the text report plugin is
            # run again normally.
            #
            self.__report_manager.generate_screen_report(
                self.orchestrator.uiManager.notifier)

            # Send the audit end message.
            self.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                          message_code = MessageCode.MSG_CONTROL_STOP_AUDIT,
                          message_info = True)   # True for finished,
                                                 # False for user cancel

        # If the reports are not yet launched...
        else:

            # Look for the earliest stage with pending data.
            for stage in xrange(pluginManager.min_stage,
                                pluginManager.max_stage + 1):
                self.__current_stage = stage
                pending = database.get_pending_data(stage)
                if not pending:
                    continue

                # If the stage is empty...
                if not pluginManager.stages[stage]:

                    # Mark all data as having finished this stage.
                    database.mark_stage_finished_many(pending, stage)

                    # Skip to the next stage.
                    continue

                # Process the pending data in batches.
                # This reduces the memory footprint for large databases.
                candidates = list(pending)
                pending.clear()
                for i in xrange(0, len(candidates), 10):

                    # Get this batch.
                    batch_ids = set(candidates[i:i+10])
                    batch = database.get_many_data(batch_ids)
                    if not batch:
                        database.mark_stage_finished_many(batch_ids, stage)
                        continue

                    # Filter out data out of scope.
                    data_ok = []
                    ids_ok = set()
                    ids_not_ok = set()
                    for data in batch:
                        if data.is_in_scope(self.scope):
                            ids_ok.add(data.identity)
                            data_ok.append(data)
                        else:
                            ids_not_ok.add(data.identity)
                    if ids_not_ok:
                        database.mark_stage_finished_many(ids_not_ok, stage)
                    batch_ids = ids_ok
                    batch = data_ok
                    if not batch:
                        continue

                    # Filter out data that won't be processed in this stage.
                    # FIXME: this should sieve the data, not return a bool
                    if not self.__notifier.is_runnable_stage(batch, stage):
                        database.mark_stage_finished_many(batch_ids, stage)
                        continue

                    # Keep the filtered IDs.
                    pending.update(batch_ids)
                    batch = []

                # If no data survived the filter, skip to the next stage.
                if not pending:
                    continue

                # Update the stage statistics.
                self.__stage_cycles[self.__current_stage] += 1
                self.__processed_count = 0
                self.__total_count = len(pending)

                # We're going to run testing plugins,
                # so we need to update the audit stop time.
                self.__must_update_stop_time = True

                # Tell the Orchestrator we just moved to another stage.
                stage_name = pluginManager.get_stage_name_from_value(stage)
                self.send_msg(
                    message_type = MessageType.MSG_TYPE_STATUS,
                    message_code = MessageCode.MSG_STATUS_STAGE_UPDATE,
                    message_info = stage_name,
                )

                # Send the pending data to the Orchestrator.
                to_send = list(pending)
                for i in xrange(0, len(to_send), 10):
                    datalist = database.get_many_data(to_send[i:i+10])
                    self.send_msg(
                        message_type = MessageType.MSG_TYPE_DATA,
                        message_code = MessageCode.MSG_DATA_REQUEST,
                        message_info = datalist,
                    )

                # We're done, return.
                return

            # If we reached this point, we finished the last stage.
            # Launch the report generation.
            self.__current_stage = pluginManager.max_stage + 1
            self.generate_reports()


    #--------------------------------------------------------------------------
    def dispatch_msg(self, message):
        """
        Send messages to the plugins of this audit.

        :param message: The message to send.
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %r instead" % type(message))

        # Keep the original execution context.
        old_context = Config._context

        try:

            # Update the execution context for this audit.
            Config._context = PluginContext(
                       msg_queue = old_context.msg_queue,
                         address = old_context.address,
                      audit_name = self.name,
                    audit_config = self.config,
                     audit_scope = self.scope,
                    ack_identity = message.ack_identity,
                orchestrator_pid = old_context._orchestrator_pid,
                orchestrator_tid = old_context._orchestrator_tid)

            # Dispatch the message.
            self.__dispatch_msg(message)

        finally:

            # Restore the original execution context.
            Config._context = old_context

    def __dispatch_msg(self, message):

        # Get the database and the plugin manager.
        database = self.database
        pluginManager = self.pluginManager

        # Is it a log message?
        if message.message_type == MessageType.MSG_TYPE_CONTROL and \
           message.message_code == MessageCode.MSG_CONTROL_LOG:

            # Get the log line.
            (text, level, is_error) = message.message_info

            # Get the plugin instance.
            plugin_id = message.plugin_id
            ack_id    = message.ack_identity

            # Get the timestamp.
            timestamp = message.timestamp

            # Append the log line.
            database.append_log_line(
                text, level, is_error, plugin_id, ack_id, timestamp)

            # We're done.
            return

        # Is it data?
        if message.message_type == MessageType.MSG_TYPE_DATA:

            # Sanitize the message, the info should always be a list.
            if isinstance(message.message_info, Data):
                message.message_info = [message.message_info]

            # Is it data meant to be sent to the plugins?
            if message.message_code == MessageCode.MSG_DATA_REQUEST:

                # Send the message to the plugins, and track the expected ACKs.
                launched = self.__notifier.notify(message)
                if launched:
                    self.inc_expected_ack(launched)
                else:
                    self.inc_expected_ack()
                    self.send_msg(
                        message_type = MessageType.MSG_TYPE_CONTROL,
                        message_code = MessageCode.MSG_CONTROL_ACK,
                            priority = MessagePriority.MSG_PRIORITY_LOW)

                # Increment the count of processed objects.
                self.__processed_count += len(message.message_info)

                # We're done.
                return

            # Is it data received from the plugins?
            elif message.message_code == MessageCode.MSG_DATA_RESPONSE:

                # Here we'll store the data to be resent to the plugins.
                data_for_plugins = []

                # For each data object sent...
                for data in message.message_info:

                    # Check the type.
                    if not isinstance(data, Data):
                        warn(
                            "TypeError: Expected Data, got %r instead"
                            % type(data), RuntimeWarning, stacklevel=3)
                        continue

                    # Is the data new?
                    if not database.has_data_key(data.identity):

                        # Increase the number of links followed.
                        if data.is_instance(URL):
                            self.__followed_links += 1

                            # Maximum number of links reached?
                            if (
                                self.config.max_links > 0 and
                                self.__followed_links >= self.config.max_links
                            ):

                                # Show a warning, but only once.
                                if self.__show_max_links_warning:
                                    self.__show_max_links_warning = False
                                    w = "Maximum number of links (%d) reached! Audit: %s"
                                    w = w % (self.config.max_links, self.name)
                                    with catch_warnings(record=True) as wlist:
                                        warn(w, RuntimeWarning)
                                    self.send_msg(
                                        message_type = MessageType.MSG_TYPE_CONTROL,
                                        message_code = MessageCode.MSG_CONTROL_WARNING,
                                        message_info = wlist,
                                        priority = MessagePriority.MSG_PRIORITY_HIGH)

                                # Skip this data object.
                                continue

                    # Add the data to the database.
                    # This automatically merges the data if it already exists.
                    database.add_data(data)

                    # If the data is in scope...
                    if data.is_in_scope():

                        # If the plugin is not recursive,
                        # mark the data as already processed by it.
                        plugin_id = message.plugin_id
                        if plugin_id:
                            plugin_info = pluginManager.get_plugin_by_id(
                                                                    plugin_id)
                            if not plugin_info.recursive:
                                database.mark_plugin_finished(data.identity,
                                                              plugin_id)

                        # The data will be sent to the plugins.
                        data_for_plugins.append(data)

                    # If the data is NOT in scope...
                    else:

                        # Mark the data as having completed all stages.
                        database.mark_stage_finished(data.identity,
                                                     pluginManager.max_stage)

                # Recursively process newly discovered data, if any.
                # Discovered data already in the database is ignored.
                visited = {data.identity for data in data_for_plugins}  # Skip original data.
                for data in list(data_for_plugins):       # Can't iterate and modify!
                    links = set(data.links)               # Get the original links.
                    queue = list(data.discovered)         # Make sure it's a copy.
                    links = set(data.links).difference(links) # Get the new links.
                    while queue:
                        data = queue.pop(0)
                        if (data.identity not in visited and
                            not database.has_data_key(data.identity)
                        ):
                            database.add_data(data)       # No merging because it's new.
                            visited.add(data.identity)    # Prevents infinite loop.
                            queue.extend(data.discovered) # Recursive.
                            if data.is_in_scope():        # If in scope, send it to plugins.
                                data_for_plugins.append(data)
                            else:                         # If not, mark as completed.
                                database.mark_stage_finished(data.identity,
                                                    pluginManager.max_stage)
                    if links:                             # If we have new links...
                        database.add_data(data)           # Refresh the data object.

                # If we have data to be sent and we're in the first stage...
                if (
                    data_for_plugins and
                    self.current_stage == self.pluginManager.min_stage
                ):

                    # Increment the total data count for this stage.
                    self.__total_count += len(data_for_plugins)

                    # Send a data request message to the Orchestrator.
                    # This optimization saves on database accesses.
                    self.send_msg(message_type = MessageType.MSG_TYPE_DATA,
                                  message_code = MessageCode.MSG_DATA_REQUEST,
                                  message_info = data_for_plugins)


    #--------------------------------------------------------------------------
    def generate_reports(self):
        """
        Start the generation of reports for the audit.
        """

        # Check if the report generation is already started.
        if self.__is_report_started:
            raise RuntimeError("Why are you asking for the report twice?")

        # An ACK is expected after launching the report plugins.
        self.inc_expected_ack()
        try:

            # Mark the report generation as started for this audit.
            self.__is_report_started = True

            # Before generating the reports, set the audit stop time.
            # This is needed so the report can print the start and stop times.
            if self.__must_update_stop_time:
                self.database.set_audit_stop_time( time() )

            # Are any report plugins active?
            launched = 0
            if self.__report_manager.plugin_count > 0:

                # Tell the UI we've started generating the reports.
                self.send_msg(
                    message_type = MessageType.MSG_TYPE_STATUS,
                    message_code = MessageCode.MSG_STATUS_STAGE_UPDATE,
                    message_info = "report",
                )

                # Start the report generation.
                launched = self.__report_manager.generate_reports(
                    self.__notifier)

            # Handle the ACK messages.
            if launched:
                self.inc_expected_ack(launched)
            else:
                self.inc_expected_ack()
                self.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                              message_code = MessageCode.MSG_CONTROL_ACK,
                                  priority = MessagePriority.MSG_PRIORITY_LOW)

        # Send the ACK after launching the report plugins.
        finally:
            self.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                          message_code = MessageCode.MSG_CONTROL_ACK,
                              priority = MessagePriority.MSG_PRIORITY_LOW)


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this audit.
        """
        # This looks horrible, I know :(
        try:
            try:
                try:
                    try:
                        try:
                            if self.database is not None:
                                try:
                                    self.database.append_log_line(
                                        "Audit started.", Logger.MORE_VERBOSE)
                                finally:
                                    try:
                                        self.database.compact()
                                    finally:
                                        self.database.close()
                        finally:
                            if self.__notifier is not None:
                                self.__notifier.close()
                    finally:
                        if self.__plugin_manager is not None:
                            self.__plugin_manager.close()
                finally:
                    if self.__import_manager is not None:
                        self.__import_manager.close()
            finally:
                if self.__report_manager is not None:
                    self.__report_manager.close()
        finally:
            self.__database       = None
            self.__orchestrator   = None
            self.__notifier       = None
            self.__audit_config   = None
            self.__audit_scope    = None
            self.__plugin_manager = None
            self.__import_manager = None
            self.__report_manager = None
