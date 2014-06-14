#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager of RPC calls from plugins.
"""
from golismero.api.config import Config

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

__all__ = ["RPCManager"]

from ..common import pickle
from ..messaging.codes import MessageCode, MSG_RPC_CODES
from ..messaging.manager import MessageManager

from functools import partial
from threading import Thread

import sys
import traceback


#------------------------------------------------------------------------------
# Decorators to automatically register RPC implementors at import time.

# Global map of RPC codes to implementors.
# dict( int -> tuple(callable, bool) )
rpcMap = {}

def implementor(rpc_code, blocking=False):
    """
    RPC implementation function.
    """
    return partial(_add_implementor, rpc_code, blocking)

def _add_implementor(rpc_code, blocking, fn):

    # Validate the argument types.
    if type(rpc_code) is not int:
        raise TypeError("Expected int, got %r instead" % type(rpc_code))
    if type(blocking) is not bool:
        raise TypeError("Expected bool, got %r instead" % type(blocking))
    if not callable(fn):
        raise TypeError("Expected callable, got %r instead" % type(fn))

    # Validate the RPC code.
    if rpc_code in rpcMap:
        try:
            msg = "Duplicated RPC implementors for code %d: %s and %s"
            msg %= (rpc_code, rpcMap[rpc_code][0].__name__, fn.__name__)
        except Exception:
            msg = "Duplicated RPC implementors for code: %d" % rpc_code
        raise SyntaxError(msg)

    # TODO: use introspection to validate the function signature

    # Register the implementor.
    rpcMap[rpc_code] = (fn, blocking)

    # Return the implementor. No wrapping is needed! :)
    return fn


#------------------------------------------------------------------------------
# Implementor for the special MSG_RPC_BULK code for bulk RPC calls.

@implementor(MessageCode.MSG_RPC_BULK)
def rpc_bulk(orchestrator, audit_name, rpc_code, *arguments):

    # Get the implementor for the RPC code.
    # Raise NotImplementedError if it's not defined.
    try:
        method, blocking = rpcMap[rpc_code]
    except KeyError:
        raise NotImplementedError("RPC code not implemented: %r" % rpc_code)

    # This can't be done with blocking implementors!
    if blocking:
        raise NotImplementedError(
            "Cannot run blocking RPC calls in bulk. Code: %r" % rpc_code)

    # Prepare a partial function call to the implementor.
    caller = partial(method, orchestrator, audit_name)

    # Use the built-in map() function to issue all the calls.
    # This ensures we support the exact same interface and functionality.
    return map(caller, *arguments)


#------------------------------------------------------------------------------
# Ensures the message is received by the Orchestrator.

@implementor(MessageCode.MSG_RPC_SEND_MESSAGE)
def rpc_send_message(orchestrator, audit_name, message):

    # Enqueue the ACK message.
    orchestrator.enqueue_msg(message)


#------------------------------------------------------------------------------
class RPCManager (object):
    """
    Executes remote procedure calls from plugins.
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator
        """

        # Keep a reference to the Orchestrator.
        self.__orchestrator = orchestrator

        # Keep a reference to the global RPC map (it's faster this way).
        self.__rpcMap = rpcMap

        # Check all RPC messages have been mapped at this point.
        missing = MSG_RPC_CODES.difference(self.__rpcMap.keys())
        if missing:
            msg  = "Missing RPC implementors for codes: %s"
            msg %= ", ".join(str(x) for x in sorted(missing))
            raise SyntaxError(msg)


    #--------------------------------------------------------------------------
    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__orchestrator


    #--------------------------------------------------------------------------
    def execute_rpc(self, audit_name, rpc_code, response_queue, args, kwargs):
        """
        Honor a remote procedure call request from a plugin.

        :param audit_name: Name of the audit requesting the call.
        :type audit_name: str

        :param rpc_code: RPC code.
        :type rpc_code: int

        :param response_queue: Response queue identity.
        :type response_queue: str

        :param args: Positional arguments to the call.
        :type args: tuple

        :param kwargs: Keyword arguments to the call.
        :type kwargs: dict
        """
        try:

            # Get the implementor for the RPC code.
            # Raise NotImplementedError if it's not defined.
            try:
                target, blocking = self.__rpcMap[rpc_code]
            except KeyError:
                raise NotImplementedError(
                    "RPC code not implemented: %r" % rpc_code)

            # If it's a blocking call...
            if blocking:

                # Run the implementor in a new thread.
                thread = Thread(
                    target = self._execute_rpc_implementor_background,
                    args = (
                        Config._context,
                        audit_name,
                        target,
                        response_queue,
                        args, kwargs),
                )
                thread.daemon = True
                thread.start()

            # If it's a non-blocking call...
            else:

                # Call the implementor directly.
                self.execute_rpc_implementor(
                    audit_name, target, response_queue, args, kwargs)

        # Catch exceptions and send them back.
        except Exception:
            if response_queue:
                error = self.prepare_exception(*sys.exc_info())
                try:
                    self.orchestrator.messageManager.send(
                        response_queue, (False, error))
                except IOError:
                    import warnings
                    warnings.warn("RPC caller died!")
                    pass


    #--------------------------------------------------------------------------
    def _execute_rpc_implementor_background(self, context, audit_name, target,
                                           response_queue, args, kwargs):
        """
        Honor a remote procedure call request from a plugin,
        from a background thread. Must only be used as the entry
        point for said background thread!

        :param context: Plugin execution context.
        :type context: PluginContext

        :param audit_name: Name of the audit requesting the call.
        :type audit_name: str

        :param target: RPC implementor function.
        :type target: callable

        :param response_queue: Response queue identity.
        :type response_queue: str

        :param args: Positional arguments to the call.
        :type args: tuple

        :param kwargs: Keyword arguments to the call.
        :type kwargs: dict
        """
        Config._context = context
        self.execute_rpc_implementor(
            audit_name, target, response_queue, args, kwargs)


    #--------------------------------------------------------------------------
    def execute_rpc_implementor(self, audit_name, target, response_queue,
                                args, kwargs):
        """
        Honor a remote procedure call request from a plugin.

        :param audit_name: Name of the audit requesting the call.
        :type audit_name: str

        :param target: RPC implementor function.
        :type target: callable

        :param response_queue: Response queue identity.
        :type response_queue: str

        :param args: Positional arguments to the call.
        :type args: tuple

        :param kwargs: Keyword arguments to the call.
        :type kwargs: dict
        """
        try:

            # Call the implementor and get the response.
            response = target(self.orchestrator, audit_name, *args, **kwargs)
            success  = True

        # Catch exceptions and prepare them for sending.
        except Exception:
            if response_queue:
                response = self.prepare_exception(*sys.exc_info())
                success  = False

        # If the call was synchronous,
        # send the response/error back to the plugin.
        if response_queue:
            self.orchestrator.messageManager.send(
                response_queue, (success, response))


    #--------------------------------------------------------------------------
    @staticmethod
    def prepare_exception(exc_type, exc_value, exc_traceback):
        """
        Prepare an exception for sending back to the plugins.

        :param exc_type: Exception type.
        :type exc_type: class

        :param exc_value: Exception value.
        :type exc_value:

        :returns: Exception type, exception value
            and formatted traceback. The exception value may be formatted too
            and the exception type replaced by Exception if it's not possible
            to serialize it for sending.
        :rtype: tuple(class, object, str)
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        try:
            pickle.dumps(exc_value, -1)
        except Exception:
            exc_value = traceback.format_exception_only(exc_type, exc_value)
        try:
            pickle.dumps(exc_type, -1)
        except Exception:
            exc_type = Exception
        exc_traceback = traceback.extract_tb(exc_traceback)
        return exc_type, exc_value, exc_traceback
