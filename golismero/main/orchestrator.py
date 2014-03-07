#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Orchestrator, the manager of everything, core of GoLismero.

All messages go through here before being dispatched to their destinations.
Most other tasks are delegated from here to other managers.
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

__all__ = ["Orchestrator"]

from .console import Console
from .scope import DummyScope
from ..api.config import Config
from ..api.logger import Logger
from ..database.cachedb import PersistentNetworkCache, VolatileNetworkCache
from ..managers.auditmanager import AuditManager
from ..managers.pluginmanager import PluginManager
from ..managers.uimanager import UIManager
from ..managers.rpcmanager import RPCManager
from ..managers.processmanager import ProcessManager, PluginContext
from ..managers.networkmanager import NetworkManager
from ..messaging.codes import MessageType, MessageCode, MessagePriority
from ..messaging.message import Message
from ..messaging.manager import MessageManager

from os import getpid
from thread import get_ident
from traceback import format_exc, print_exc
from signal import signal, SIGINT, SIG_DFL


#------------------------------------------------------------------------------
class Orchestrator (object):
    """
    Orchestrator, the manager of everything, core of GoLismero.

    All messages go through here before being dispatched to
    their destinations. Most other tasks are delegated from
    here to other managers.
    """


    #--------------------------------------------------------------------------
    def __init__(self, config):
        """
        Start the Orchestrator.

        :param config: configuration of orchestrator.
        :type config: OrchestratorConfig
        """

        # Save the configuration.
        self.__config = config

        # Instance the Queue message manager.
        self.__messageManager = MessageManager(is_rpc = False)
        self.__messageManager.listen()
        self.__messageManager.start()

        # Instance the RPC message manager.
        self.__rpcMessageManager = MessageManager(is_rpc = True)
        self.__rpcMessageManager.listen()
        self.__rpcMessageManager.start()

        # Set the Orchestrator context.
        self.__context = PluginContext(
            orchestrator_pid = getpid(),
            orchestrator_tid = get_ident(),
                   msg_queue = self.messageManager.name,
                     address = self.messageManager.address,
                audit_config = self.config )
        Config._context = self.__context

        # Withing the main process, keep a
        # static reference to the Orchestrator.
        PluginContext._orchestrator = self

        # Create the RPC manager.
        self.__rpcManager = RPCManager(self)

        # Load the plugin manager.
        self.__pluginManager = PluginManager(self)

        # Set the console configuration.
        Console.level = self.config.verbose
        Console.use_colors = self.config.color

        # Search for plugins.
        success, failure = self.pluginManager.find_plugins(self.config)
        if not success:
            raise RuntimeError("Failed to find any plugins!")

        # Load the UI plugin.
        ui_plugin_id = "ui/%s" % self.config.ui_mode
        try:
            self.pluginManager.get_plugin_by_id(ui_plugin_id)
        except KeyError:
            raise ValueError(
                "No plugin found for UI mode: %r" % self.config.ui_mode)
        self.pluginManager.load_plugin_by_id(ui_plugin_id)

        # Set the user-defined arguments for the plugins.
        for plugin_id, plugin_args in self.config.plugin_args.iteritems():
            self.pluginManager.set_plugin_args(plugin_id, plugin_args)

        # Create the UI manager.
        self.__ui = UIManager(self)

        # Network connection manager.
        self.__netManager = NetworkManager(self.__config)

        # Network cache.
        if (self.__config.use_cache_db or
            self.__config.use_cache_db is None
        ):
            self.__cache = PersistentNetworkCache()
        else:
            self.__cache = VolatileNetworkCache()

        # Create the process manager.
        self.__processManager = ProcessManager(self)
        self.__processManager.start()

        # Create the audit manager.
        self.__auditManager = AuditManager(self)

        # Log the plugins that failed to load.
        # XXX FIXME: this won't work until the UI was started!
        ##Logger.log_more_verbose("Loaded %d plugins" % len(success))
        ##if failure:
        ##    Logger.log_error("Failed to load %d plugins" % len(failure))
        ##    for plugin_id in failure:
        ##        Logger.log_error_verbose("\t%s" % plugin_id)


    #--------------------------------------------------------------------------
    # Context support.

    def __enter__(self):
        return self
    def __exit__(self, type, value, tb):
        self.close()


    #--------------------------------------------------------------------------
    # Getters (mostly used by RPC implementors).

    @property
    def config(self):
        """
        :returns: Orchestrator config.
        :rtype: Orchestratorconfig
        """
        return self.__config

    @property
    def messageManager(self):
        """
        :returns: Message manager.
        :rtype: MessageManager
        """
        return self.__messageManager

    @property
    def rpcMessageManager(self):
        """
        :returns: RPC message manager.
        :rtype: MessageManager
        """
        return self.__rpcMessageManager

    @property
    def pluginManager(self):
        """
        :returns: Plugin manager.
        :rtype: PluginManager
        """
        return self.__pluginManager

    @property
    def netManager(self):
        """
        :returns: Network manager.
        :rtype: NetworkManager
        """
        return self.__netManager

    @property
    def cacheManager(self):
        """
        :returns: Cache manager.
        :rtype: AbstractNetworkCache
        """
        return self.__cache

    @property
    def rpcManager(self):
        """
        :returns: RPC manager.
        :rtype: RPCManager
        """
        return self.__rpcManager

    @property
    def processManager(self):
        """
        :returns: Process manager.
        :rtype: ProcessManager
        """
        return self.__processManager

    @property
    def auditManager(self):
        """
        :returns: Audit manager.
        :rtype: AuditManager
        """
        return self.__auditManager

    @property
    def uiManager(self):
        """
        :returns: UI manager.
        :rtype: UIManager
        """
        return self.__ui


    #--------------------------------------------------------------------------
    def __control_c_handler(self, signum, frame):
        """
        Signal handler to catch Control-C interrupts.
        """

        try:

            # Tell the user the message has been sent.
            Console.display("User cancel requested, stopping all audits...")

            # Send a stop message to the Orchestrator.
            message = Message(message_type = MessageType.MSG_TYPE_CONTROL,
                              message_code = MessageCode.MSG_CONTROL_STOP,
                              message_info = False,
                                  priority = MessagePriority.MSG_PRIORITY_HIGH)
            try:
                self.messageManager.put(message)
            except:
                print_exc()
                exit(1)

        finally:

            # Only do this once, the next time just PANIC.
            signal(SIGINT, self.__panic_control_c_handler)


    #--------------------------------------------------------------------------
    def __panic_control_c_handler(self, signum, frame):
        """
        Emergency signal handler to catch Control-C interrupts.
        """
        try:

            # Kill all subprocesses.
            try:
                self.processManager.stop()
            except Exception:
                print_exc()
                exit(1)

        finally:

            # Only do this once, the next time raise KeyboardInterrupt.
            try:
                action, self.__old_signal_action = \
                    self.__old_signal_action, SIG_DFL
            except AttributeError:
                action = SIG_DFL
            signal(SIGINT, action)


    #--------------------------------------------------------------------------
    def dispatch_msg(self, message):
        """
        Process messages from audits or from the message queue, and send them
        forward to the plugins through the Message Manager when appropriate.

        :param message: Incoming message.
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError(
                "Expected Message, got %r instead" % type(message))

        try:

            # Check the audit exists, drop the message otherwise.
            if (
                message.audit_name and
                not self.auditManager.has_audit(message.audit_name)
            ):
                print (
                    "Internal error: dropped message for audit %r: %r"
                    % (message.audit_name, message))
                return

            # If it's an RPC message...
            if message.message_type == MessageType.MSG_TYPE_RPC:

                # Execute the call.
                self.__rpcManager.execute_rpc(message.audit_name,
                                              message.message_code,
                                              * message.message_info)

            # If it's a stop audit message, dispatch it first to the UI,
            # then to the audit manager (the opposite to the normal order).
            elif (
                message.message_type == MessageType.MSG_TYPE_CONTROL and
                message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT
            ):
                self.uiManager.dispatch_msg(message)
                self.auditManager.dispatch_msg(message)
                Logger.log_verbose("Audit finished: %s" % message.audit_name)

            # For all other messages...
            else:

                # Dispatch it to the audits.
                self.auditManager.dispatch_msg(message)

                # Dispatch it to the UI plugins.
                self.uiManager.dispatch_msg(message)

        finally:

            # If it's a quit message...
            if  message.message_type == MessageType.MSG_TYPE_CONTROL and \
                message.message_code == MessageCode.MSG_CONTROL_STOP:

                # Stop the program execution.
                if message.message_info:
                    exit(0)                   # Planned shutdown.
                else:
                    raise KeyboardInterrupt() # User cancel.


    #--------------------------------------------------------------------------
    def enqueue_msg(self, message):
        """
        Put messages into the message queue.

        :param message: incoming message
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError(
                "Expected Message, got %r instead" % type(message))

        if (
            message.priority == MessagePriority.MSG_PRIORITY_HIGH and
            Config._has_context and getpid() == Config._context._orchestrator_pid
        ):
            self.dispatch_msg(message)
        else:
            try:
                self.messageManager.put(message)
            except Exception:
                print_exc()
                exit(1)


    #--------------------------------------------------------------------------
    def build_plugin_context(self, audit_name, plugin, ack_identity):
        """
        Prepare a PluginContext object to pass to the plugins.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin: Plugin instance.
        :type plugin: Plugin

        :param ack_identity: Identity hash of the current input data.
        :type ack_identity: str

        :returns: OOP plugin execution context.
        :rtype: PluginContext
        """

        # Get the audit configuration and scope.
        if audit_name:
            audit = self.auditManager.get_audit(audit_name)
            audit_config  = audit.config
            audit_scope   = audit.scope
            pluginManager = audit.pluginManager
        else:
            audit_config  = self.config
            audit_scope   = DummyScope()
            pluginManager = self.pluginManager

        # Get the plugin information.
        info = pluginManager.get_plugin_info_from_instance(plugin)[1]

        # Return the context instance.
        return PluginContext(
                     address = self.messageManager.address,
                   msg_queue = self.messageManager.name,
                ack_identity = ack_identity,
                 plugin_info = info,
                  audit_name = audit_name,
                audit_config = audit_config,
                 audit_scope = audit_scope,
            orchestrator_pid = self.__context._orchestrator_pid,
            orchestrator_tid = self.__context._orchestrator_tid,
        )


    #--------------------------------------------------------------------------
    def run(self, *audits):
        """
        Message loop.

        Optionally start new audits passed as positional arguments.
        """

        try:

            # Start the UI.
            self.uiManager.start()

            # If we have initial audits, start them.
            for audit_config in audits:
                message = Message(
                    message_type = MessageType.MSG_TYPE_CONTROL,
                    message_code = MessageCode.MSG_CONTROL_START_AUDIT,
                    message_info = audit_config,
                        priority = MessagePriority.MSG_PRIORITY_HIGH,
                )
                self.enqueue_msg(message)

            # Signal handler to catch Ctrl-C.
            self.__old_signal_action = signal(
                SIGINT, self.__control_c_handler)

            # Message loop.
            while True:
                try:

                    # Wait for a message to arrive.
                    try:
                        message = self.messageManager.get()
                    except Exception:
                        # If this fails, kill the Orchestrator.
                        # But let KeyboardInterrupt and SystemExit through.
                        print_exc()
                        exit(1)

                    # Dispatch the message.
                    self.dispatch_msg(message)

                # If an exception is raised during message processing,
                # just log the exception and continue.
                except Exception:
                    Logger.log_error(
                        "Error processing message!\n%s" % format_exc())
                    ##raise   # XXX FIXME

        finally:

            # Stop the UI.
            try:
                self.uiManager.stop()
            except Exception:
                print_exc()


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by the Orchestrator.
        """
        # This looks horrible, I know :(
        try:
            try:
                try:
                    try:
                        try:
                            try:

                                # Stop the process manager.
                                self.processManager.stop()

                            finally:

                                # Stop the audit manager.
                                self.auditManager.close()

                        finally:

                            # Compact the cache database.
                            self.cacheManager.compact()

                    finally:

                        # Close the cache database.
                        self.cacheManager.close()

                finally:

                    # Close the plugin manager.
                    self.pluginManager.close()

            finally:

                # Close the message manager.
                try:
                    self.messageManager.close()
                finally:
                    if Config._has_context and \
                                    Config._context._msg_manager is not None:
                        Config._context._msg_manager.close()

        finally:

            # Reset the execution context.
            Config._context = None

            # Break circular references.
            self.__auditManager   = None
            self.__cache          = None
            self.__config         = None
            self.__netManager     = None
            self.__pluginManager  = None
            self.__processManager = None
            self.__rpcManager     = None
            self.__ui             = None
