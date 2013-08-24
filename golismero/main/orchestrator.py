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

from os import getpid
from thread import get_ident
from traceback import format_exc, print_exc
from signal import signal, SIGINT, SIG_DFL
from multiprocessing import Manager


#----------------------------------------------------------------------
class Orchestrator (object):
    """
    Orchestrator, the manager of everything, core of GoLismero.

    All messages go through here before being dispatched to their destinations.
    Most other tasks are delegated from here to other managers.
    """


    #----------------------------------------------------------------------
    def __init__(self, config):
        """
        Start the Orchestrator.

        :param config: configuration of orchestrator.
        :type config: OrchestratorConfig
        """

        # Configuration.
        self.__config = config

        # Incoming message queue.
        if getattr(config, "max_process", 0) <= 0:
            from Queue import Queue
            self.__queue = Queue(maxsize = 0)
        else:
            self.__queue_manager = Manager()
            self.__queue = self.__queue_manager.Queue()

        # Set the Orchestrator context.
        self.__context = PluginContext( orchestrator_pid = getpid(),
                                        orchestrator_tid = get_ident(),
                                               msg_queue = self.__queue,
                                            audit_config = self.__config )
        Config._context = self.__context

        # Withing the main process, keep a static reference to the Orchestrator.
        PluginContext._orchestrator = self

        # Set the console configuration.
        Console.level = config.verbose
        Console.use_colors = config.colorize

        # Search for plugins.
        self.__pluginManager = PluginManager()
        success, failure = self.pluginManager.find_plugins(self.__config)
        if not success:
            raise RuntimeError("Failed to find any plugins!")

        # Set the user-defined arguments for the plugins.
        for plugin_name, plugin_args in self.__config.plugin_args.iteritems():
            self.pluginManager.set_plugin_args(plugin_name, plugin_args)

        # Load the UI plugin.
        ui_plugin_name = "ui/%s" % self.__config.ui_mode
        try:
            self.pluginManager.get_plugin_by_name(ui_plugin_name)
        except KeyError:
            raise ValueError("No plugin found for UI mode: %r" % self.__config.ui_mode)
        self.pluginManager.load_plugin_by_name(ui_plugin_name)

        # Network connection manager.
        self.__netManager = NetworkManager(self.__config)

        # Network cache.
        if (self.__config.use_cache_db or
            self.__config.use_cache_db is None
        ):
            self.__cache = PersistentNetworkCache()
        else:
            self.__cache = VolatileNetworkCache()

        # RPC manager.
        self.__rpcManager = RPCManager(self)

        # Process manager.
        self.__processManager = ProcessManager(self)
        self.__processManager.start()

        # Audit manager.
        self.__auditManager = AuditManager(self)

        # UI manager.
        self.__ui = UIManager(self)

        # Signal handler to catch Ctrl-C.
        self.__old_signal_action = signal(SIGINT, self.__control_c_handler)

        # Log the plugins that failed to load.
        Logger.log_more_verbose("Loaded %d plugins" % len(success))
        if failure:
            Logger.log_error("Failed to load %d plugins" % len(failure))
            for plugin_name in failure:
                Logger.log_error_verbose("\t%s" % plugin_name)

    @property
    def config(self):
        """
        :returns: Orchestrator config.
        :rtype: Orchestratorconfig
        """
        return self.__config


    #----------------------------------------------------------------------
    # Context support.

    def __enter__(self):
        return self
    def __exit__(self, type, value, tb):
        self.close()


    #----------------------------------------------------------------------
    # Manager getters (mostly used by RPC implementors).

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


    #----------------------------------------------------------------------
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
                self.__queue.put_nowait(message)
            except:
                exit(1)

        finally:

            # Only do this once, the next time just PANIC.
            signal(SIGINT, self.__panic_control_c_handler)


    #----------------------------------------------------------------------
    def __panic_control_c_handler(self, signum, frame):
        """
        Emergency signal handler to catch Control-C interrupts.
        """
        try:

            # Kill all subprocesses.
            try:
                self.processManager.stop()
            except Exception:
                exit(1)

        finally:

            # Only do this once, the next time raise KeyboardInterrupt.
            try:
                action, self.__old_signal_action = self.__old_signal_action, SIG_DFL
            except AttributeError:
                action = SIG_DFL
            signal(SIGINT, action)


    #----------------------------------------------------------------------
    def add_audit(self, params):
        """
        Start a new audit.

        :param params: Audit settings
        :type params: AuditConfig
        """
        self.auditManager.new_audit(params)


    #----------------------------------------------------------------------
    def dispatch_msg(self, message):
        """
        Process messages from audits or from the message queue, and send them
        forward to the plugins through the Message Manager when appropriate.

        :param message: Incoming message.
        :type message: Message

        :returns: True if the message was sent, False if it was dropped.
        :rtype: bool
        """
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %s instead" % type(message))

        try:

            # If it's an RPC message...
            if message.message_type == MessageType.MSG_TYPE_RPC:

                # Execute the call.
                self.__rpcManager.execute_rpc(message.audit_name,
                                              message.message_code,
                                              * message.message_info)

                # The method now must return True because the message was sent.
                return True

            # If it's a stop audit message, dispatch it first to the UI,
            # then to the audit manager (the opposite to the normal order).
            if (message.message_type == MessageType.MSG_TYPE_CONTROL and \
                message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT
            ):
                self.uiManager.dispatch_msg(message)
                self.auditManager.dispatch_msg(message)
                Logger.log_verbose("Audit finished: %s" % message.audit_name)

                # The method now must return True because the message was sent.
                return True

            # If it's a control or info message, dispatch it to the audits.
            if self.auditManager.dispatch_msg(message):

                # If it wasn't dropped, send it to the UI plugins.
                self.uiManager.dispatch_msg(message)

                # The method now must return True because the message was sent.
                return True

            # The method now must return False because the message was dropped.
            return False

        finally:

            # If it's a quit message...
            if  message.message_type == MessageType.MSG_TYPE_CONTROL and \
                message.message_code == MessageCode.MSG_CONTROL_STOP:

                # Stop the program execution
                if message.message_info:
                    exit(0)                   # Planned shutdown
                else:
                    raise KeyboardInterrupt() # User cancel


    #----------------------------------------------------------------------
    def enqueue_msg(self, message):
        """
        Put messages into the message queue.

        :param message: incoming message
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %s instead" % type(message))
        try:
            self.__queue.put_nowait(message)
        except Exception:
            exit(1)


    #----------------------------------------------------------------------
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
        return PluginContext(orchestrator_pid = self.__context._orchestrator_pid,
                             orchestrator_tid = self.__context._orchestrator_tid,
                                    msg_queue = self.__queue,
                                 ack_identity = ack_identity,
                                  plugin_info = info,
                                   audit_name = audit_name,
                                 audit_config = audit_config,
                                  audit_scope = audit_scope)


    #----------------------------------------------------------------------
    def notify_plugin_status(self, audit_name, plugin_name, status_code, status_data):
        """
        Notify the Orchestrator of a change in a plugin execution state.

        :param audit_name: Name of the audit.
        :type audit_name: str

        :param plugin_name: Name of the plugin.
        :type plugin_name: str

        :param status_code: Status code. Must be one of the MessageCode.MSG_STATUS_* constants.
        :type status_code: int

        :param status_data: Status data.
        :type status_data: \\*
        """
        msg = Message(
            message_type = MessageType.MSG_TYPE_STATUS,
            message_code = status_code,
            message_info = status_data,
             plugin_name = plugin_name,
              audit_name = audit_name,
                priority = MessagePriority.MSG_PRIORITY_MEDIUM,
        )
        self.dispatch_msg(msg)


    #----------------------------------------------------------------------
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
                self.add_audit(audit_config)

            # Message loop.
            while True:
                try:

                    # Wait for a message to arrive.
                    try:
                        message = self.__queue.get()
                    except Exception:
                        # If this fails, kill the Orchestrator.
                        # But let KeyboardInterrupt and SystemExit through.
                        exit(1)

                    # Dispatch the message.
                    self.dispatch_msg(message)

                # If an exception is raised during message processing,
                # just log the exception and continue.
                except Exception:
                    Logger.log_error("Error processing message!\n%s" % format_exc())
                    raise   # XXX FIXME

        finally:

            # Stop the UI.
            try:
                self.uiManager.stop()
            except Exception:
                print_exc()


    #----------------------------------------------------------------------
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

                                # TODO: dump any pending messages and store the current state.
                                # See: http://stackoverflow.com/questions/1540822/dumping-a-multiprocessing-queue-into-a-list
                                pass

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
            self.__queue          = None
            self.__queue_manager  = None
            self.__ui             = None
