#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Process manager.

Here's where the process pool is prepared and plugins are launched.
The bootstrapping code for plugins is also here.

Lots of black magic going on, beware of dragons! :)
"""
import os

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

__all__ = ["ProcessManager", "PluginContext"]

from ..api.config import Config
from ..api.data import LocalDataCache
from ..api.localfile import LocalFile
from ..api.logger import Logger
from ..api.net.cache import NetworkCache
from ..api.net.http import HTTP
from ..messaging.codes import MessageType, MessageCode, MessagePriority
from ..messaging.message import Message
from ..messaging.manager import MessageManager

from imp import load_source
from os import getpid
from thread import get_ident
from threading import Timer
from traceback import format_exc, print_exc, format_exception_only, format_list
from warnings import catch_warnings, simplefilter

import socket
import sys

# Make some runtime patches to the multiprocessing module.
# Just importing this submodule does the magic!
from ..patches import mp  # noqa

# Imports needed to override the multiprocessing Process and Pool classes.
from multiprocessing import Process as _Original_Process
from multiprocessing.pool import Pool as _Original_Pool


#------------------------------------------------------------------------------
class Process(_Original_Process):
    """
    A customized process that forces the 'daemon' property to False.

    This means we have to take care of killing our own subprocesses.

    This only affects Windows platforms.
    """

    @property
    def daemon(self):
        return os.path.sep == "/"

    @daemon.setter
    def daemon(self, value):
        pass

    @daemon.deleter
    def daemon(self, value):
        pass


#------------------------------------------------------------------------------
class Pool(_Original_Pool):
    """
    A customized process pool that forces the 'daemon' property to False.

    This means we have to take care of killing our own subprocesses.

    This only affects Windows platforms.
    """
    Process = Process


#------------------------------------------------------------------------------

# Timeout for RPC calls, in seconds. Use None for no timeout.
RPC_TIMEOUT = None #10.0

# Plugin class per-process cache. Used by the bootstrap() function.
plugin_class_cache = dict()   # tuple(class, module) -> class object

# Message manager for the plugin workers.
msgManager = None

# Do-nothing function for "warming up" the process pool.
# This increases startup time, but results in a speedup later on.
def do_nothing(*args, **kwargs):
    return
# Serializable function to run plugins in subprocesses.
# This is required for Windows support, since we don't have os.fork() there.
# See: http://docs.python.org/2/library/multiprocessing.html#windows
def launcher(
        queue, max_concurrent, refresh_after_tasks, orchestrator_address):
    return _launcher(
        queue, max_concurrent, refresh_after_tasks, orchestrator_address)

def _launcher(
        queue, max_concurrent, refresh_after_tasks, orchestrator_address):

    # Initialize this worker process.
    _init_worker()

    # Instance the pool manager.
    pool = PluginPoolManager(
        max_concurrent, refresh_after_tasks, orchestrator_address)

    # Start the pool manager.
    wait = True
    pool.start()
    try:

        # Consumer loop.
        while True:

            # Get the next plugin call to issue.
            try:
                item = queue.get()
            except:
                # If we reached this point we can assume
                # the parent process is dead.
                wait = False
                exit(1)

            # Handle the message to quit.
            if item is True or item is False:
                wait = item
                return

            # Handle the message to call a plugin.
            pool.run_plugin(*item)

    finally:

        # Stop the pool manager.
        try:
            pool.stop(wait)
        except:
            # If we reached this point we can assume
            # the parent process is dead.
            exit(1)

# Serializable bootstrap function to run plugins in subprocesses.
# This is required for Windows support, since we don't have os.fork() there.
# See: http://docs.python.org/2/library/multiprocessing.html#windows
def bootstrap(context, func, args, kwargs):
    return _bootstrap(context, func, args, kwargs)

_do_notify_end = False

def _bootstrap(context, func, args, kwargs):
    global _do_notify_end
    try:
        _do_notify_end = False
        try:
            try:
                plugin_warnings = []
                try:

                    # Catch all warnings.
                    # TODO: hook stdout and stderr to catch prints.
                    with catch_warnings(record=True) as plugin_warnings:
                        simplefilter("always")

                        # Connect to the Orchestrator.
                        global msgManager
                        msgManager = MessageManager(is_rpc = True)
                        msgManager.connect(context._orchestrator_address)
                        msgManager.start()

                        # Configure the plugin.
                        Config._context = context

                        # Set the plugin execution timeout, if any.
                        kill_timer = None
                        if Config.audit_config.plugin_timeout:
                            kill_timer = Timer(
                                Config.audit_config.plugin_timeout,
                                _plugin_killer, (context,)
                            )
                            kill_timer.start()

                        try:

                            # Run the plugin.
                            _bootstrap_inner(context, func, args, kwargs)

                        finally:

                            # Cancel the plugin execution timeout, if any.
                            if kill_timer is not None:
                                kill_timer.cancel()

                finally:

                    # Send plugin warnings to the Orchestrator.
                    if plugin_warnings:
                        try:
                            context.send_msg(
                                message_type = MessageType.MSG_TYPE_CONTROL,
                                message_code = MessageCode.MSG_CONTROL_WARNING,
                                message_info = plugin_warnings,
                                    priority = MessagePriority.MSG_PRIORITY_HIGH,
                            )
                        except Exception, e:
                            context.send_msg(
                                message_type = MessageType.MSG_TYPE_CONTROL,
                                message_code = MessageCode.MSG_CONTROL_ERROR,
                                message_info = (str(e), format_exc()),
                                    priority = MessagePriority.MSG_PRIORITY_HIGH,
                            )

            except Exception, e:

                # Tell the Orchestrator there's been an error.
                context.send_msg(
                    message_type = MessageType.MSG_TYPE_CONTROL,
                    message_code = MessageCode.MSG_CONTROL_ERROR,
                    message_info = (str(e), format_exc()),
                        priority = MessagePriority.MSG_PRIORITY_HIGH,
                )

        finally:

            # Send back an ACK.
            context.send_ack(_do_notify_end)

            # Reset the current crawling depth.
            context._depth = -1

            # Close the message manager.
            if context._orchestrator_pid != getpid():
                try:
                    msgManager.close()
                finally:
                    msgManager = None

    # On keyboard interrupt or fatal error,
    # tell the Orchestrator we need to stop.
    except:
        print_exc()

        # Send a message to the Orchestrator to stop.
        try:
            if msgManager is not None:
                context.send_msg(
                    message_type = MessageType.MSG_TYPE_CONTROL,
                    message_code = MessageCode.MSG_CONTROL_STOP,
                    message_info = False,
                )
        except SystemExit:
            raise
        except:
            print_exc()

        # If we reached this point we can assume the parent process is dead.
        exit(1)

def _bootstrap_inner(context, func, args, kwargs):
    global _do_notify_end

    # If the plugin receives a Data object...
    if func == "run":

        # Get the data sent to the plugin.
        try:
            input_data = kwargs["info"]
        except KeyError:
            input_data = args[0]

        # Abort if the data is out of scope
        # for the current audit.
        if not input_data.is_in_scope():
            ##Logger.log_error_more_verbose(
            ##    "Skipped data out of scope: %s" % input_data.identity)
            return

        # Save the current crawling depth.
        if hasattr(input_data, "depth"):
            context._depth = input_data.depth

            # Check we didn't exceed the maximum depth.
            max_depth = context.audit_config.depth
            if max_depth is not None and max_depth < context._depth:
                Logger.log_error_more_verbose(
                    "Maximum crawling depth exceeded! Skipped: %s" %
                    input_data.identity)
                return

    # Set the default socket timeout.
    # Note: due to a known bug in Python versions prior to 2.7.5 we can't set
    # a default timeout because it makes the multiprocessing module misbehave.
    # See: http://hg.python.org/cpython/rev/4e85e4743757
    if sys.version_info[:3] >= (2,7,5):
        socket.setdefaulttimeout(5.0)

    # Initialize the private file API.
    LocalFile._update_plugin_path()

    # Clear the HTTP connection pool.
    HTTP._initialize()

    # Clear the local network cache for this process.
    NetworkCache._clear_local_cache()

    # Initialize the local data cache for this run.
    LocalDataCache.on_run()
    if func == "run":
        LocalDataCache.on_create(input_data)

    # Try to get the plugin from the cache.
    cache_key = (context.plugin_module, context.plugin_class)
    try:
        cls = plugin_class_cache[cache_key]

    # If not in the cache, load the class.
    except KeyError:

        # Load the plugin module.
        mod = load_source(
            "_plugin_tmp_" + context.plugin_class.replace(".", "_"),
            context.plugin_module)

        # Get the plugin class.
        cls = getattr(mod, context.plugin_class)

        # Cache the plugin class.
        plugin_class_cache[cache_key] = cls

    # Instance the plugin.
    instance = cls()

    # Notify the Orchestrator of the plugin start.
    context.send_msg(
        message_type = MessageType.MSG_TYPE_STATUS,
        message_code = MessageCode.MSG_STATUS_PLUGIN_BEGIN,
    )
    _do_notify_end = True

    # Call the callback method.
    result = None
    try:
        result = getattr(instance, func)(*args, **kwargs)
    finally:

        # Return value is a list of data for run().
        if func == "run":

            # Validate and sanitize the result data.
            result = LocalDataCache.on_finish(result, input_data)

            # Send the result data to the Orchestrator.
            if result:
                try:
                    context.send_msg(
                        message_type = MessageType.MSG_TYPE_DATA,
                        message_code = MessageCode.MSG_DATA_RESPONSE,
                        message_info = result,
                    )
                except Exception, e:
                    context.send_msg(
                        message_type = MessageType.MSG_TYPE_CONTROL,
                        message_code = MessageCode.MSG_CONTROL_ERROR,
                        message_info = (str(e), format_exc()),
                            priority = MessagePriority.MSG_PRIORITY_HIGH,
                    )


#------------------------------------------------------------------------------
def _plugin_killer(context):
    """
    Internally used function that kills a plugin
    when the execution timeout has been reached.

    :param context: Plugin execution context.
    :type context: PluginContext
    """

    try:

        try:

            # Tell the Orchestrator there's been an error.
            context.send_msg(
                message_type = MessageType.MSG_TYPE_CONTROL,
                message_code = MessageCode.MSG_CONTROL_ERROR,
                message_info = ("Execution timeout reached.", ""),
                    priority = MessagePriority.MSG_PRIORITY_HIGH,
            )

        finally:

            # Send back an ACK.
            context.send_ack(_do_notify_end)

            # Reset the current crawling depth.
            context._depth = -1

    finally:

        # Kill the current process.
        exit(1)


#------------------------------------------------------------------------------
def _init_worker():
    """
    Initializer for pooled processes.
    """

    # Try to lower the CPU usage priority as much as possible.
    try:
        import posix
        posix.nice(99)
    except Exception:
        pass


#------------------------------------------------------------------------------
class PluginContext (object):
    """
    Serializable execution context for the plugins.
    """

    # Current crawling depth, set automatically by the plugin bootstrap.
    _depth = -1

    def __init__(self, address, msg_queue,
                 ack_identity = None, plugin_info = None,
                 audit_name = None, audit_config = None, audit_scope = None,
                 orchestrator_pid = None, orchestrator_tid = None):
        """
        Serializable execution context for the plugins.

        :param address: Host and port to send messages to the Orchestrator.
        :type address: tuple(str, int)

        :param msg_queue: Identity of the message queue to send messages
            to the Orchestrator.
        :type msg_queue: str

        :param ack_identity: Identity hash of the current input data,
            or None if not running a plugin.
        :type ack_identity: str | None

        :param plugin_info: Plugin information,
            or None if not running a plugin.
        :type plugin_info: PluginInfo | None

        :param audit_name: Name of the audit,
            or None if not running an audit.
        :type audit_name: str | None

        :param audit_config: Parameters of the audit,
            or None if not running an audit.
        :type audit_config: AuditConfig | None

        :param audit_scope: Scope of the audit,
            or None if not running an audit.
        :type audit_scope: AuditScope | None

        :param orchestrator_pid: Process ID of the Orchestrator.
        :type orchestrator_pid: int | None

        :param orchestrator_tid: Main thread ID of the Orchestrator.
        :type orchestrator_tid: int | None

        """
        self.__address          = address
        self.__msg_queue        = msg_queue
        self.__ack_identity     = ack_identity
        self.__plugin_info      = plugin_info
        self.__audit_name       = audit_name
        self.__audit_config     = audit_config
        self.__audit_scope      = audit_scope
        self.__orchestrator_pid = orchestrator_pid
        self.__orchestrator_tid = orchestrator_tid

    @property
    def address(self):
        """"
        :returns: Host and port to send messages to the Orchestrator.
        :rtype: tuple(str, int)
        """
        return self.__address

    @property
    def msg_queue(self):
        """"
        :returns: Message queue where to send the responses.
        :rtype: str
        """
        return self.__msg_queue

    @property
    def audit_name(self):
        """"
        :returns: Name of the audit, or None if not running an audit.
        :rtype: str | None
        """
        return self.__audit_name

    @property
    def audit_config(self):
        """"
        :returns: Parameters of the audit, or None if not running an audit.
        :rtype: AuditConfig | None
        """
        return self.__audit_config

    @property
    def audit_scope(self):
        """"
        :returns: Scope of the audit, or None if not running an audit.
        :rtype: AuditScope | None
        """
        return self.__audit_scope

    @property
    def ack_identity(self):
        """"
        :returns: Identity hash of the current input data, or None if not running a plugin.
        :rtype: str | None
        """
        # do not break the line in this docstring: due to a bug in Sphinx,
        # we can't break lines in a :returns: tag.
        return self.__ack_identity

    @property
    def plugin_info(self):
        """"
        :returns: Plugin information, or None if not running a plugin.
        :rtype: str | None
        """
        return self.__plugin_info

    @property
    def plugin_id(self):
        """"
        :returns: Plugin ID, or None if not running a plugin.
        :rtype: str | None
        """
        if self.__plugin_info:
            return self.__plugin_info.plugin_id

    @property
    def plugin_module(self):
        """"
        :returns: Module where the plugin is to be loaded from, or None if not running a plugin.
        :rtype: str | None
        """
        # do not break the line in this docstring: due to a bug in Sphinx,
        # we can't break lines in a :returns: tag.
        if self.__plugin_info:
            return self.__plugin_info.plugin_module

    @property
    def plugin_class(self):
        """"
        :returns: Class name of the plugin, or None if not running a plugin.
        :rtype: str | None
        """
        if self.__plugin_info:
            return self.__plugin_info.plugin_class

    @property
    def plugin_config(self):
        """"
        :returns: Plugin configuration, or None if not running a plugin.
        :rtype: str | None
        """
        if self.__plugin_info:
            return self.__plugin_info.plugin_config

    @property
    def depth(self):
        """"
        :returns: Current analysis depth.
        :rtype: int
        """
        return self._depth

    @property
    def _orchestrator_pid(self):
        """"
        .. warning: This property is internally used by GoLismero.

        :returns: Process ID of the Orchestrator.
        :rtype: int | None
        """
        return self.__orchestrator_pid

    @property
    def _orchestrator_tid(self):
        """"
        .. warning: This property is internally used by GoLismero.

        :returns: Main thread ID of the Orchestrator.
        :rtype: int | None
        """
        return self.__orchestrator_tid

    @property
    def _msg_manager(self):
        """"
        .. warning: This property is internally used by GoLismero.

        :returns: Message manager.
        :rtype: MessageManager
        """
        global msgManager

        # For some reason tonight I have no time for figuring out,
        # this only works well on Windows (and fails without it),
        # but on Linux it's exactly the other way around. My guess
        # is the difference is related to Windows starting new
        # processes from scratch and Linux forking them instead.
        if os.path.sep == "\\":
            if hasattr(self, "_orchestrator"):
                msgManager = self._orchestrator.rpcMessageManager

        # I think this code may actually leak file descriptors, so
        # the sooner I can figure this out and fix it, the better. :(
        if msgManager is None:
            msgManager = MessageManager(is_rpc = True)
            msgManager.connect(self.address)
            msgManager.start()
            if hasattr(self, "_orchestrator"):
                self._orchestrator._Orchestrator__rpcMessageManager = \
                    msgManager

        # Return the message manager.
        return msgManager


    #--------------------------------------------------------------------------
    def is_local(self):
        """
        :returns: True if we're running inside the Orchestrator's
                  main thread, False otherwise.
        :rtype: bool
        """
        return (
            self.__orchestrator_pid == getpid()    and
            self.__orchestrator_tid == get_ident()
        )


    #--------------------------------------------------------------------------
    def send_ack(self, do_notify_end):
        """
        Send ACK messages from the plugins to the Orchestrator.

        :param do_notify_end: True to send the plugin end notification to
            the UI plugin, False otherwise.
        :type do_notify_end: bool
        """
        self.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                      message_code = MessageCode.MSG_CONTROL_ACK,
                      message_info = do_notify_end,
                          priority = MessagePriority.MSG_PRIORITY_LOW)


    #--------------------------------------------------------------------------
    def send_status(self, progress = None):
        """
        Send status updates from the plugins to the Orchestrator.

        :param text: Optional status text.
        :type text: str | None

        :param progress: Progress percentage [0, 100] as a float,
                         or None to indicate progress can't be measured.
        :type progress: float | None
        """

        # Validate the progress.
        if progress is not None:
            if type(progress) in (int, long):
                progress = float(progress)
            elif type(progress) is not float:
                raise TypeError(
                    "Expected float, got %r instead", type(progress))
            if progress < 0.0:
                progress = 0.0
            elif progress > 100.0:
                progress = 100.0

        # Send the status message to the Orchestrator.
        self.send_msg(message_type = MessageType.MSG_TYPE_STATUS,
                      message_code = MessageCode.MSG_STATUS_PLUGIN_STEP,
                      message_info = progress,
                          priority = MessagePriority.MSG_PRIORITY_MEDIUM)


    #--------------------------------------------------------------------------
    def send_msg(self, message_type = 0,
                       message_code = 0,
                       message_info = None,
                           priority = MessagePriority.MSG_PRIORITY_MEDIUM):
        """
        Send messages from the plugins to the Orchestrator.

        :param message_type: Message type.
            Must be one of the constants from MessageType.
        :type mesage_type: int

        :param message_code: Message code.
            Must be one of the constants from MessageCode.
        :type message_code: int

        :param message_info: The payload of the message.
            Its type depends on the message type and code.
        :type message_info: \\*

        :param priority: Priority level.
            Must be one of the constants from MessagePriority.
        :type priority: int
        """

        # Special case if we're in the same process
        # as the Orchestrator: we can't implement RPC
        # calls using messages, because we'd deadlock
        # against ourselves, since the producer and
        # the consumer would be the same process.
        if message_type == MessageType.MSG_TYPE_RPC and self.is_local():
            self._orchestrator.rpcManager.execute_rpc(
                        self.audit_name, message_code, *message_info)
            return

        # Build the raw message.
        message = Message(message_type = message_type,
                          message_code = message_code,
                          message_info = message_info,
                            audit_name = self.audit_name,
                             plugin_id = self.plugin_id,
                          ack_identity = self.ack_identity,
                              priority = priority)

        # Special case for ACKs, we want to ensure they're processed
        # before returning.
        if message_type == MessageType.MSG_TYPE_CONTROL and \
                        message_code == MessageCode.MSG_CONTROL_ACK:
            self.remote_call(MessageCode.MSG_RPC_SEND_MESSAGE, message)
            return

        # Build the message normally.
        self.send_raw_msg(message)


    #--------------------------------------------------------------------------
    def send_raw_msg(self, message):
        """
        Send raw messages from the plugins to the Orchestrator.

        :param message: Message to send.
        :type message: Message
        """

        ### XXX DEBUG
        ##with open("message-%d.log" % getpid(), "a") as f:
        ##    f.write("[%s] Got %r\n\n" % (ctime(), message))

        # Hack for urgent messages: if we're in the same process
        # as the Orchestrator, skip the queue and dispatch them now.
        if (message.priority >= MessagePriority.MSG_PRIORITY_HIGH and
            self.is_local()
        ):
            self._orchestrator.dispatch_msg(message)
            return

        # Put the message in the queue.
        try:
            self._msg_manager.send(self.msg_queue, message)

        # If we reached this point we can assume the parent process is dead.
        except:
            print_exc()
            exit(1)


    #--------------------------------------------------------------------------
    def remote_call(self, rpc_code, *args, **kwargs):
        """
        Make synchronous remote procedure calls on the Orchestrator.

        :param rpc_code: RPC code.
        :type rpc_code: int

        :returns: Depends on the call.
        :rtype: \\*
        """

        # Send the RPC message.
        self.send_msg(message_type = MessageType.MSG_TYPE_RPC,
                      message_code = rpc_code,
                      message_info = (self._msg_manager.name, args, kwargs),
                          priority = MessagePriority.MSG_PRIORITY_HIGH)

        # Get the response.
        try:
            raw_response = self._msg_manager.get(RPC_TIMEOUT)  # blocking call

        # If the above fails we can assume the parent process is dead.
        except:
            print_exc()
            exit(1)

        # Return the response, or raise an exception on error.
        success, response = raw_response
        if not success:
            exc_type, exc_value, tb_list = response
            try:
                sys.stderr.writelines(
                    format_exception_only(exc_type, exc_value) )
                sys.stderr.writelines(
                    format_list(tb_list) )
            except Exception:
                pass
            raise response[0], response[1]
        return response


    #--------------------------------------------------------------------------
    def async_remote_call(self, rpc_code, *args, **kwargs):
        """
        Make asynchronous remote procedure calls on the Orchestrator.

        There's no return value, since we're not waiting for a response.

        :param rpc_code: RPC code.
        :type rpc_code: int
        """
        # Send the RPC message.
        self.send_msg(message_type = MessageType.MSG_TYPE_RPC,
                      message_code = rpc_code,
                      message_info = (None, args, kwargs),
                          priority = MessagePriority.MSG_PRIORITY_HIGH)


    #--------------------------------------------------------------------------
    def bulk_remote_call(self, rpc_code, *arguments):
        """
        Make synchronous bulk remote procedure calls on the Orchestrator.

        The interface and behavior mimics that of the built-in map() function.
        For more details see:
        http://docs.python.org/2/library/functions.html#map

        :param rpc_code: RPC code.
        :type rpc_code: int

        :returns: List contents depend on the call.
        :rtype: list
        """

        # Convert all the iterables to tuples
        # to make sure they're serializable.
        arguments = tuple( tuple(x) for x in arguments )

        # Send the MSG_RPC_BULK call and return the response.
        return self.remote_call(MessageCode.MSG_RPC_BULK, rpc_code, *arguments)


    #--------------------------------------------------------------------------
    def async_bulk_remote_call(self, rpc_code, *arguments):
        """
        Make asynchronous bulk remote procedure calls on the Orchestrator.

        The interface and behavior mimics that of the built-in map() function.
        For more details see:
        http://docs.python.org/2/library/functions.html#map

        There's no return value, since we're not waiting for a response.

        :param rpc_code: RPC code.
        :type rpc_code: int
        """

        # Convert all the iterables to tuples
        # to make sure they're serializable.
        arguments = tuple( tuple(x) for x in arguments )

        # Send the MSG_RPC_BULK call.
        self.async_remote_call(MessageCode.MSG_RPC_BULK, rpc_code, *arguments)


#------------------------------------------------------------------------------
class PluginLauncher (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #--------------------------------------------------------------------------
    def __init__(self, max_process, refresh_after_tasks, orchestrator_address):
        """
        :param max_process: Maximum number of processes to create.
        :type max_process: int

        :param refresh_after_tasks:
                Maximum number of function calls to make
                before refreshing a subprocess.
        :type refresh_after_tasks: int

        :param orchestrator_address:
            Host and port for the Orchestrator message queue.
        :type orchestrator_address: tuple(str, int)
        """

        # Initialize the launcher process, but do not start it yet.
        try:
            from multiprocessing import Manager
            self.__manager = Manager()
            self.__queue = self.__manager.Queue()

        # If the above fails we can assume the parent process is dead.
        except:
            exit(1)

        self.__process = Process(
            target = launcher,
            args   = (
                self.__queue,
                max_process,
                refresh_after_tasks,
                orchestrator_address
            ),
        )
        self.__alive = True


    #--------------------------------------------------------------------------
    def run_plugin(self, context, func, args, kwargs):
        """
        Run a plugin in a pooled process.

        :param context: Context for the OOP plugin execution.
        :type context: PluginContext

        :param func: Name of the method to execute.
        :type func: str

        :param args: Positional arguments to the function call.
        :type args: tuple

        :param kwargs: Keyword arguments to the function call.
        :type kwargs: dict
        """

        # Raise an exception if the launcher had been stopped.
        if not self.__alive:
            raise RuntimeError("Plugin launcher was stopped")

        # Send the plugin run request to the launcher process.
        try:
            self.__queue.put_nowait( (context, func, args, kwargs) )

        # If the above fails we can assume the parent process is dead.
        except:
            try:
                self.stop(wait = False)
            except:
                pass
            exit(1)


    #--------------------------------------------------------------------------
    def start(self):
        """
        Start the plugin launcher.
        """

        # Raise an exception if the launcher had been stopped.
        if not self.__alive:
            raise RuntimeError("Plugin launcher was stopped")

        # Start the launcher process.
        self.__process.start()


    #--------------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the plugin launcher.

        :param wait: True to wait for the subprocesses to finish,
            False to kill them.
        :type wait: bool
        """

        # Ignore the request if the launcher was already stopped.
        if not self.__alive:
            return

        try:

            # Signal the launcher process to stop.
            self.__queue.put_nowait(wait)

            # Wait for the launcher process to stop.
            if wait:
                self.__process.join()
            else:
                self.__process.join(3)
                try:
                    self.__process.terminate()
                except Exception:
                    pass

        # If the pipe is closed, terminate the process.
        except:
            self.__process.terminate()

        # Clean up.
        self.__alive   = False
        self.__process = None
        self.__queue   = None
        self.__manager = None


#------------------------------------------------------------------------------
class PluginPoolManager (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #--------------------------------------------------------------------------
    def __init__(self, max_process, refresh_after_tasks, orchestrator_address):
        """
        :param max_process: Maximum number of processes to create.
        :type max_process: int

        :param refresh_after_tasks:
            Maximum number of function calls to make
            before refreshing a subprocess.
        :type refresh_after_tasks: int

        :param orchestrator_address:
            Host and port for the Orchestrator message queue.
        :type orchestrator_address: tuple(str, int)
        """
        self.__max_processes        = max_process
        self.__refresh_after_tasks  = 1 #refresh_after_tasks
        self.__orchestrator_address = orchestrator_address

        self.__pool = None


    #--------------------------------------------------------------------------
    def run_plugin(self, context, func, args, kwargs):
        """
        Run a plugin in a pooled process.

        :param context: Context for the OOP plugin execution.
        :type context: PluginContext

        :param func: Name of the method to execute.
        :type func: str

        :param args: Positional arguments to the function call.
        :type args: tuple

        :param kwargs: Keyword arguments to the function call.
        :type kwargs: dict
        """

        # Make sure to pass the Orchestrator host and port.
        context._orchestrator_address = self.__orchestrator_address

        # If we have a process pool, run the plugin asynchronously.
        if self.__pool is not None:
            self.__pool.apply_async(bootstrap,
                    (context, func, args, kwargs))
            return

        # Otherwise just call the plugin directly.
        old_context = Config._context
        try:
            return bootstrap(context, func, args, kwargs)
        finally:
            Config._context = old_context


    #--------------------------------------------------------------------------
    def start(self):
        """
        Start the process manager.
        """

        # If we already have a process pool, do nothing.
        if self.__pool is None:

            # Are we running the plugins in multiprocessing mode?
            if self.__max_processes is not None and self.__max_processes > 0:

                # Create the process pool.
                self.__pool = Pool(
                    initializer = _init_worker,
                    processes = self.__max_processes,
                    maxtasksperchild = self.__refresh_after_tasks)

                # Force the pool to start all its processes.
                self.__pool.map_async(do_nothing, "A" * self.__max_processes)

            # Are we running the plugins in single process mode?
            else:

                # No process pool then!
                self.__pool = None


    #--------------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the process manager.

        :param wait: True to wait for the subprocesses to finish,
            False to kill them.
        :type wait: bool
        """

        # If we have a process pool...
        if self.__pool is not None:

            # Either wait patiently, or kill the damn things!
            if wait:
                self.__pool.close()
            else:
                self.__pool.terminate()
            self.__pool.join()

            # Destroy the process pool.
            self.__pool = None

        # Clear the plugin instance cache.
        plugin_class_cache.clear()


#------------------------------------------------------------------------------
class ProcessManager (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Orchestrator to send messages to.
        :type orchestrator: Orchestrator
        """

        self.__launcher = None

        config = orchestrator.config

        # Maximum number of processes to create.
        self.__max_processes = getattr(config, "max_concurrent", None)

        # Maximum number of function calls to make
        # before refreshing a subprocess.
        self.__refresh_after_tasks = getattr(
            config, "refresh_after_tasks", None)

        # Host and port to connect to in order to talk to the Orchestrator.
        self.__orchestrator_address = orchestrator.messageManager.address


    #--------------------------------------------------------------------------
    def run_plugin(self, context, func, args, kwargs):
        """
        Run a plugin in a pooled process.

        :param context: Context for the OOP plugin execution.
        :type context: PluginContext

        :param func: Name of the method to execute.
        :type func: str

        :param args: Positional arguments to the function call.
        :type args: tuple

        :param kwargs: Keyword arguments to the function call.
        :type kwargs: dict
        """

        # If we have a dispatcher, run the plugin asynchronously.
        if self.__launcher is not None:
            return self.__launcher.run_plugin(context, func, args, kwargs)

        # Otherwise just call the plugin directly.
        old_context = Config._context
        try:
            if not hasattr(context, "_orchestrator_address"):
                context._orchestrator_address = self.__orchestrator_address
            return bootstrap(context, func, args, kwargs)
        finally:
            Config._context = old_context


    #--------------------------------------------------------------------------
    def start(self):
        """
        Start the process manager.
        """

        # If we already have a process pool, do nothing.
        if self.__launcher is None:

            # Are we running the plugins in multiprocessing mode?
            if self.__max_processes is not None and self.__max_processes > 0:

                # Create the process pool.
                ##launcherClass = PluginPoolManager
                launcherClass = PluginLauncher
                self.__launcher = launcherClass(
                    self.__max_processes,
                    self.__refresh_after_tasks,
                    self.__orchestrator_address,
                )

                # Start it
                self.__launcher.start()

            # Are we running the plugins in single process mode?
            else:

                # No process pool then!
                self.__launcher = None


    #--------------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the process manager.

        :param wait: True to wait for the subprocesses to finish,
            False to kill them.
        :type wait: bool
        """

        # If we have a process pool...
        if self.__launcher is not None:

            # Stop it.
            self.__launcher.stop(wait)

            # Clean up.
            self.__launcher = None
