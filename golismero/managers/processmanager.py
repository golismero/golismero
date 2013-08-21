#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Process manager.

Here's where the process pool is prepared and plugins are launched.
The bootstrapping code for plugins is also here.

Lots of black magic going on, beware of dragons! :)
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

__all__ = ["ProcessManager", "PluginContext"]

from ..api.config import Config
from ..api.data import LocalDataCache
from ..api.file import FileManager
from ..api.net.cache import NetworkCache
from ..api.net.http import HTTP
from ..messaging.codes import MessageType, MessageCode, MessagePriority
from ..messaging.message import Message

from imp import load_source
from multiprocessing import Manager
from multiprocessing import Process as _Original_Process
from multiprocessing.pool import Pool as _Original_Pool
from os import getpid
from warnings import catch_warnings, simplefilter
from thread import get_ident
from traceback import format_exc, print_exc, format_exception_only, format_list
from signal import signal, SIGINT

import sys


#------------------------------------------------------------------------------
class Process(_Original_Process):
    """
    A customized process that forces the 'daemon' property to False.

    This means we have to take care of killing our own subprocesses.
    """

    @property
    def daemon(self):
        return False

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
    """
    Process = Process


#------------------------------------------------------------------------------

# Plugin class per-process cache. Used by the bootstrap() function.
plugin_class_cache = dict()   # tuple(class, module) -> class object

# Do-nothing function for "warming up" the process pool.
# This increases startup time, but results in a speedup later on.
def do_nothing(*args, **kwargs):
    return

# Serializable function to run plugins in subprocesses.
# This is required for Windows support, since we don't have os.fork() there.
# See: http://docs.python.org/2/library/multiprocessing.html#windows
def launcher(queue, max_process, refresh_after_tasks):
    return _launcher(queue, max_process, refresh_after_tasks)
def _launcher(queue, max_process, refresh_after_tasks):

    # Instance the pool manager.
    pool = PluginPoolManager(max_process, refresh_after_tasks)

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
                # If we reached this point we can assume the parent process is dead.
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
            # If we reached this point we can assume the parent process is dead.
            exit(1)

# Serializable bootstrap function to run plugins in subprocesses.
# This is required for Windows support, since we don't have os.fork() there.
# See: http://docs.python.org/2/library/multiprocessing.html#windows
def bootstrap(context, func, args, kwargs):
    return _bootstrap(context, func, args, kwargs)
def _bootstrap(context, func, args, kwargs):
    try:
        try:
            try:
                plugin_warnings = []
                try:

                    # Catch all warnings.
                    with catch_warnings(record=True) as plugin_warnings:
                        simplefilter("always")

                        # Configure the plugin.
                        Config._context = context

                        # If the plugin receives a Data object...
                        if func == "recv_info":

                            # Get the data sent to the plugin.
                            try:
                                input_data = kwargs["info"]
                            except KeyError:
                                input_data = args[0]

                            # Abort if the data is out of scope for the current audit.
                            if not input_data.is_in_scope():
                                return

                        # TODO: hook stdout and stderr to catch print statements

                        # Clear the HTTP connection pool.
                        HTTP._initialize()

                        # Clear the local network cache for this process.
                        NetworkCache._clear_local_cache()

                        # Initialize the local data cache for this run.
                        LocalDataCache.on_run()

                        # Initialize the private file API.
                        FileManager._update_plugin_path()

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

                        # Call the callback method.
                        result = None
                        try:
                            result = getattr(instance, func)(*args, **kwargs)
                        finally:

                            # Return value is a list of data for recv_info().
                            if func == "recv_info":

                                # Validate and sanitize the result data.
                                result = LocalDataCache.on_finish(result)

                                # Always send back the input data as a result.
                                if input_data not in result:
                                    result.insert(0, input_data)

                                # Send the result data to the Orchestrator.
                                if result:
                                    try:
                                        context.send_msg(message_type = MessageType.MSG_TYPE_DATA,
                                                         message_code = MessageCode.MSG_DATA,
                                                         message_info = result)
                                    except Exception, e:
                                        context.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                                                         message_code = MessageCode.MSG_CONTROL_ERROR,
                                                         message_info = (str(e), format_exc()),
                                                             priority = MessagePriority.MSG_PRIORITY_HIGH)

                # Send plugin warnings to the Orchestrator.
                finally:
                    if plugin_warnings:
                        try:
                            context.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                                             message_code = MessageCode.MSG_CONTROL_WARNING,
                                             message_info = plugin_warnings,
                                                 priority = MessagePriority.MSG_PRIORITY_HIGH)
                        except Exception, e:
                            context.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                                             message_code = MessageCode.MSG_CONTROL_ERROR,
                                             message_info = (str(e), format_exc()),
                                                 priority = MessagePriority.MSG_PRIORITY_HIGH)

            # Tell the Orchestrator there's been an error.
            except Exception, e:
                context.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                                 message_code = MessageCode.MSG_CONTROL_ERROR,
                                 message_info = (str(e), format_exc()),
                                     priority = MessagePriority.MSG_PRIORITY_HIGH)

        # Send back an ACK.
        finally:
            context.send_ack()

    # On keyboard interrupt or fatal error, tell the Orchestrator we need to stop.
    except:

        # Send a message to the Orchestrator to stop.
        try:
            context.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                             message_code = MessageCode.MSG_CONTROL_STOP,
                             message_info = False)
        except SystemExit:
            raise
        except:
            try:
                print_exc()
            except:
                pass

        # If we reached this point we can assume the parent process is dead.
        exit(1)


#------------------------------------------------------------------------------
class PluginContext (object):
    """
    Serializable execution context for the plugins.
    """

    def __init__(self, msg_queue, ack_identity = None, plugin_info = None,
                 audit_name = None, audit_config = None, audit_scope = None,
                 orchestrator_pid = None, orchestrator_tid = None):
        """
        Serializable execution context for the plugins.

        :param msg_queue: Message queue where to send the responses.
            This argument is mandatory.
        :type msg_queue: Queue

        :param ack_identity: Identity hash of the current input data, or None if not running a plugin.
        :type ack_identity: str | None

        :param plugin_info: Plugin information, or None if not running a plugin.
        :type plugin_info: PluginInfo | None

        :param audit_name: Name of the audit, or None if not running an audit.
        :type audit_name: str | None

        :param audit_config: Parameters of the audit, or None if not running an audit.
        :type audit_config: AuditConfig | None

        :param audit_scope: Scope of the audit, or None if not running an audit.
        :type audit_scope: AuditScope | None

        :param orchestrator_pid: Process ID of the Orchestrator.
        :type orchestrator_pid: int | None

        :param orchestrator_tid: Main thread ID of the Orchestrator.
        :type orchestrator_tid: int | None
        """
        self.__msg_queue        = msg_queue
        self.__ack_identity     = ack_identity
        self.__plugin_info      = plugin_info
        self.__audit_name       = audit_name
        self.__audit_config     = audit_config
        self.__audit_scope      = audit_scope
        self.__orchestrator_pid = orchestrator_pid
        self.__orchestrator_tid = orchestrator_tid

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
        return self.__ack_identity

    @property
    def plugin_info(self):
        """"
        :returns: Plugin information, or None if not running a plugin.
        :rtype: str | None
        """
        return self.__plugin_info

    @property
    def plugin_name(self):
        """"
        :returns: Plugin name, or None if not running a plugin.
        :rtype: str | None
        """
        if self.__plugin_info:
            return self.__plugin_info.plugin_name

    @property
    def plugin_module(self):
        """"
        :returns: Module where the plugin is to be loaded from, or None if not running a plugin.
        :rtype: str | None
        """
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


    #----------------------------------------------------------------------
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


    #----------------------------------------------------------------------
    def send_ack(self):
        """
        Send ACK messages from the plugins to the Orchestrator.
        """
        self.send_msg(message_type = MessageType.MSG_TYPE_CONTROL,
                      message_code = MessageCode.MSG_CONTROL_ACK,
                      message_info = self.ack_identity,
                          priority = MessagePriority.MSG_PRIORITY_LOW)


    #----------------------------------------------------------------------
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
                raise TypeError("Expected float, got %s instead", type(progress))
            if progress < 0.0:
                progress = 0.0
            elif progress > 100.0:
                progress = 100.0

        # Send the status message to the Orchestrator.
        self.send_msg(message_type = MessageType.MSG_TYPE_STATUS,
                      message_code = MessageCode.MSG_STATUS_PLUGIN_STEP,
                      message_info = (self.ack_identity, progress),
                          priority = MessagePriority.MSG_PRIORITY_MEDIUM)


    #----------------------------------------------------------------------
    def send_msg(self, message_type = 0,
                       message_code = 0,
                       message_info = None,
                           priority = MessagePriority.MSG_PRIORITY_MEDIUM):
        """
        Send messages from the plugins to the Orchestrator.

        :param message_type: Message type. Must be one of the constants from MessageType.
        :type mesage_type: int

        :param message_code: Message code. Must be one of the constants from MessageCode.
        :type message_code: int

        :param message_info: The payload of the message. Its type depends on the message type and code.
        :type message_info: \\*

        :param priority: Priority level. Must be one of the constants from MessagePriority.
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

        # Send the raw message.
        message = Message(message_type = message_type,
                          message_code = message_code,
                          message_info = message_info,
                            audit_name = self.audit_name,
                           plugin_name = self.plugin_name,
                              priority = priority)
        self.send_raw_msg(message)


    #----------------------------------------------------------------------
    def send_raw_msg(self, message):
        """
        Send raw messages from the plugins to the Orchestrator.

        :param message: Message to send.
        :type message: Message
        """

        # Hack for urgent messages: if we're in the same process
        # as the Orchestrator, skip the queue and dispatch them now.
        if (message.priority >= MessagePriority.MSG_PRIORITY_HIGH and
            self.is_local()
        ):
            self._orchestrator.dispatch_msg(message)
            return

        # Put the message in the queue.
        try:
            self.msg_queue.put_nowait(message)

        # If we reached this point we can assume the parent process is dead.
        except IOError:
            exit(1)


    #----------------------------------------------------------------------
    def remote_call(self, rpc_code, *args, **kwargs):
        """
        Make synchronous remote procedure calls on the Orchestrator.

        :param rpc_code: RPC code.
        :type rpc_code: int

        :returns: Depends on the call.
        :rtype: \\*
        """

        # Create the response queue.
        response_queue = Manager().Queue()

        # Send the RPC message.
        self.send_msg(message_type = MessageType.MSG_TYPE_RPC,
                      message_code = rpc_code,
                      message_info = (response_queue, args, kwargs),
                          priority = MessagePriority.MSG_PRIORITY_HIGH)

        # Get the response.
        try:
            raw_response = response_queue.get()  # blocking call

        # If the above fails we can assume the parent process is dead.
        except:
            exit(1)

        # Return the response, or raise an exception on error.
        success, response = raw_response
        if not success:
            exc_type, exc_value, tb_list = response
            try:
                sys.stderr.writelines( format_exception_only(exc_type, exc_value) )
                sys.stderr.writelines( format_list(tb_list) )
            except Exception:
                pass
            raise response[0], response[1]
        return response


    #----------------------------------------------------------------------
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


    #----------------------------------------------------------------------
    def bulk_remote_call(self, rpc_code, *arguments):
        """
        Make synchronous bulk remote procedure calls on the Orchestrator.

        The interface and behavior mimics that of the built-in map() function.
        For more details see: http://docs.python.org/2/library/functions.html#map

        :param rpc_code: RPC code.
        :type rpc_code: int

        :returns: List contents depend on the call.
        :rtype: list
        """

        # Convert all the iterables to tuples to make sure they're serializable.
        arguments = tuple( tuple(x) for x in arguments )

        # Send the MSG_RPC_BULK call and return the response.
        return self.remote_call(MessageCode.MSG_RPC_BULK, rpc_code, *arguments)


    #----------------------------------------------------------------------
    def async_bulk_remote_call(self, rpc_code, *arguments):
        """
        Make asynchronous bulk remote procedure calls on the Orchestrator.

        The interface and behavior mimics that of the built-in map() function.
        For more details see: http://docs.python.org/2/library/functions.html#map

        There's no return value, since we're not waiting for a response.

        :param rpc_code: RPC code.
        :type rpc_code: int
        """

        # Convert all the iterables to tuples to make sure they're serializable.
        arguments = tuple( tuple(x) for x in arguments )

        # Send the MSG_RPC_BULK call.
        self.async_remote_call(MessageCode.MSG_RPC_BULK, rpc_code, *arguments)


#------------------------------------------------------------------------------
class PluginPoolManager (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #----------------------------------------------------------------------
    def __init__(self, max_process, refresh_after_tasks):
        """
        :param max_process: Maximum number of processes to create.
        :type max_process: int

        :param refresh_after_tasks: Maximum number of function calls to make before refreshing a subprocess.
        :type refresh_after_tasks: int
        """
        self.__max_processes       = max_process
        self.__refresh_after_tasks = refresh_after_tasks

        self.__pool = None


    #----------------------------------------------------------------------
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


    #----------------------------------------------------------------------
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
                    processes = self.__max_processes,
                    maxtasksperchild = self.__refresh_after_tasks)

                # Force the pool to start all its processes.
                self.__pool.map_async(do_nothing, "A" * self.__max_processes)

            # Are we running the plugins in single process mode?
            else:

                # No process pool then!
                self.__pool = None


    #----------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the process manager.

        :param wait: True to wait for the subprocesses to finish, False to kill them.
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
class PluginLauncher (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #----------------------------------------------------------------------
    def __init__(self, max_process, refresh_after_tasks):
        """
        :param max_process: Maximum number of processes to create.
        :type max_process: int

        :param refresh_after_tasks: Maximum number of function calls to make before refreshing a subprocess.
        :type refresh_after_tasks: int
        """

        # Initialize the launcher process, but do not start it yet.
        self.__manager = Manager()
        self.__queue = self.__manager.Queue()
        self.__process = Process(
            target = launcher,
            args   = (self.__queue, max_process, refresh_after_tasks),
        )
        self.__alive = True


    #----------------------------------------------------------------------
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
        self.__queue.put_nowait( (context, func, args, kwargs) )


    #----------------------------------------------------------------------
    def start(self):
        """
        Start the plugin launcher.
        """

        # Raise an exception if the launcher had been stopped.
        if not self.__alive:
            raise RuntimeError("Plugin launcher was stopped")

        # Start the launcher process.
        self.__process.start()


    #----------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the plugin launcher.

        :param wait: True to wait for the subprocesses to finish, False to kill them.
        :type wait: bool
        """

        # Raise an exception if the launcher was already stopped.
        if not self.__alive:
            raise RuntimeError("Plugin launcher was stopped")

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

        # Clean up.
        self.__alive   = False
        self.__process = None
        self.__queue   = None
        self.__manager = None


#------------------------------------------------------------------------------
class ProcessManager (object):
    """
    Manages a pool of subprocesses to run plugins in them.
    """


    #----------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Orchestrator to send messages to.
        :type orchestrator: Orchestrator
        """

        self.__launcher = None

        config = orchestrator.config

        # Maximum number of processes to create
        self.__max_processes       = getattr(config, "max_process",         None)

        # Maximum number of function calls to make before refreshing a subprocess
        self.__refresh_after_tasks = getattr(config, "refresh_after_tasks", None)


    #----------------------------------------------------------------------
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
            return bootstrap(context, func, args, kwargs)
        finally:
            Config._context = old_context


    #----------------------------------------------------------------------
    def start(self):
        """
        Start the process manager.
        """

        # If we already have a process pool, do nothing.
        if self.__launcher is None:

            # Are we running the plugins in multiprocessing mode?
            if self.__max_processes is not None and self.__max_processes > 0:

                # Create the process pool.
                #launcher_class = PluginPoolManager
                launcher_class = PluginLauncher
                self.__launcher = launcher_class(
                    self.__max_processes, self.__refresh_after_tasks)

                # Start it
                self.__launcher.start()

            # Are we running the plugins in single process mode?
            else:

                # No process pool then!
                self.__launcher = None


    #----------------------------------------------------------------------
    def stop(self, wait = True):
        """
        Stop the process manager.

        :param wait: True to wait for the subprocesses to finish, False to kill them.
        :type wait: bool
        """

        # If we have a process pool...
        if self.__launcher is not None:

            # Stop it.
            self.__launcher.stop(wait)

            # Clean up.
            self.__launcher = None


#----------------------------------------------------------------------
def _suicide(signum, frame):
    """
    Child processes Control-C handler.

    .. warning: Do not call!
    """

    # Kill the process. This should trigger a chain reaction.
    exit(1)

if __name__ == "__parents_main__":
    signal(SIGINT, _suicide)
