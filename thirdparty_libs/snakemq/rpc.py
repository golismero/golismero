# -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})

Picklers must have functions C{loads()}, C{dumps()} and base exception
C{PickleError}.
"""

import traceback
import pickle
import threading
import uuid
import warnings
import logging
import time
import sys
from binascii import b2a_hex

from snakemq.message import Message

###############################################################################
###############################################################################
# constants
###############################################################################

REQUEST_PREFIX = b"rpcreq"
REPLY_PREFIX = b"rpcrep"

METHOD_RPC_AS_SIGNAL_ATTR = "__snakemw_rpc_as_signal"

# TODO differ between traceback and exception format
REMOTE_TRACEBACK_ATTR = "__remote_traceback__"

###############################################################################
###############################################################################
# exceptions and warnings
###############################################################################

class Error(Exception):
    pass

class NoInstanceError(Error):
    """ requested object not found """
    pass

class NoMethodError(Error):
    """ requested method not found """
    pass

class SignalCallWarning(Warning):
    """ signal method called normally or regular method called as signal """
    pass

class CallError(Error):
    pass

class NotConnected(CallError):
    """ timeouted call - peer is not connected in the time of the call """
    pass

class PartialCall(CallError):
    """ tiemouted call - client did send a request but peer disconnected
    before proper response """
    pass

###############################################################################
###############################################################################
# functions
###############################################################################

def as_signal(method):
    """
    Decorate method as a signal on the server side. On the client side it must
    be marked with L{RpcInstProxy.as_signal} method. This decorator must be "on
    top" because it marks the method with a special attribute. If the method is
    "overdecorated" then the attribute will not be visible.
    """
    setattr(method, METHOD_RPC_AS_SIGNAL_ATTR, True)
    return method

# for better mock patching
get_time = time.time

###############################################################################
###############################################################################
# server
###############################################################################

class RpcServer(object):
    """
    Registering and unregistering objects is NOT thread safe.

    Methods of registered objects are called in a different thread other
    than the link loop.
    """

    def __init__(self, receive_hook, pickler=pickle):
        self.log = logging.getLogger("snakemq.rpc.server")
        self.receive_hook = receive_hook
        self.pickler = pickler
        receive_hook.register(REQUEST_PREFIX, self.on_recv)
        self.instances = {}
        #: transfer call exception back to client (only for non-signal calls)
        self.transfer_exceptions = True

    ######################################################

    def register_object(self, instance, name):
        self.instances[name] = instance

    ######################################################

    def unregister_object(self, name):
        del self.instances[name]

    ######################################################

    def get_registered_objects(self):
        return self.instances

    ######################################################

    def on_recv(self, dummy_conn_id, ident, message):
        try:
            params = self.pickler.loads(message.data[len(REQUEST_PREFIX):])
        except self.pickler.PickleError as exc:
            self.log.error("on_recv unpickle: %r" % exc)
            return

        cmd = params["command"]
        if cmd in ("call", "signal"):
            # method must not block link loop
            thr = threading.Thread(target=self.call_method,
                    name="mqrpc_call;%s;%s" % (params["object"], params["method"]),
                    args=(ident, params))
            thr.setDaemon(True)
            thr.start()

    ######################################################

    def call_method(self, ident, params):
        # TODO timeout for reply

        if __debug__:
            self.log.debug("%s method ident=%r obj=%r method=%r req_id=%r" %
                   (params["command"], ident, params["object"], params["method"],
                   b2a_hex(params["req_id"])))

        has_signal_attr = True  # implicit is no reply on exception
        try:
            objname = params["object"]
            try:
                instance = self.instances[objname]
            except KeyError:
                raise NoInstanceError(objname)

            try:
                method = getattr(instance, params["method"])
            except KeyError:
                raise NoMethodError(params["method"])

            has_signal_attr = hasattr(method, METHOD_RPC_AS_SIGNAL_ATTR)
            if ((params["command"] == "signal" and not has_signal_attr) or
                (params["command"] == "call" and has_signal_attr)):
                warnings.warn("wrong command match for %r" % method,
                              SignalCallWarning)

            ret = method(*params["args"], **params["kwargs"])

            # signals have no return value
            if params["command"] == "call":
                self.send_return(ident, params["req_id"], ret)
        except Exception as exc:
            if self.transfer_exceptions and not has_signal_attr:
                self.send_exception(ident, params["req_id"], exc)
            else:
                raise

    ######################################################

    def send_exception(self, ident, req_id, exc):
        if __debug__:
            self.log.debug("send_exception ident=%r" % ident)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback is None:
            exc_format = ""
        else:
            exc_format = "".join(traceback.format_exception(exc_type, exc_value,
                                                    exc_traceback))
        data = {"req_id": req_id, "ok": False,
                "exception": exc, "exception_format": exc_format}
        try:
            self.send(ident, data)
        except self.pickler.PickleError:
            # raise the original exception and not the pickler's
            raise exc

    ######################################################

    def send_return(self, ident, req_id, res):
        if __debug__:
            self.log.debug("send_return ident=%r req_id=%r" % (ident, b2a_hex(req_id)))
        data = {"ok": True, "return": res, "req_id": req_id}
        self.send(ident, data)

    ######################################################

    def send(self, ident, data):
        try:
            data = self.pickler.dumps(data)
        except TypeError as exc:
            # TypeError is raised if the object is unpickable
            raise self.pickler.PickleError(exc)
        message = Message(data=REPLY_PREFIX + data)
        self.receive_hook.messaging.send_message(ident, message)

###############################################################################
###############################################################################
# client
###############################################################################

class RemoteMethod(object):
    def __init__(self, iproxy, name):
        self.iproxy = iproxy
        self.name = name
        self.call_timeout = None
        self.signal_timeout = None

    ######################################################

    def __call__(self, *args, **kwargs):
        # pylint: disable=W0212
        if self.signal_timeout is None:
            command = "call"
        else:
            command = "signal"

        try:
            params = {
                  "command": command,
                  "object": self.iproxy._name,
                  "method": self.name,
                  "args": args,
                  "kwargs": kwargs
                }
            ident = self.iproxy._remote_ident
            return self.iproxy._client.remote_request(ident, self, params)
        except CallError:
            raise
        except Exception as exc:
            ehandler = self.iproxy._client.exception_handler
            if ehandler is None:
                raise
            else:
                ehandler(exc)

    ######################################################

    def as_signal(self, timeout=0):
        """
        Mark the method as a signal method and set timeout. Setting timeout
        to None marks the method back as regular.
        @param timeout: in seconds
        """
        self.signal_timeout = timeout
    
    ######################################################

    def set_timeout(self, timeout):
        """
        Timeout of a regular (not signal) method call.
        @param timeout: in seconds
        """
        self.call_timeout = timeout

    ######################################################

    def clone(self):
        method = RemoteMethod(self.iproxy, self.name)
        method.call_timeout = self.call_timeout
        method.signal_timeout = self.signal_timeout
        return method

#########################################################################
#########################################################################

class RpcInstProxy(object):
    def __init__(self, client, remote_ident, name):
        self._client = client
        self._remote_ident = remote_ident
        self._name = name
        self._methods = {}
        client.log.debug("new proxy %r" % self)

    ######################################################

    def __getattr__(self, name):
        with self._client.lock:
            method = self._methods.get(name)
            if method is None:
                self._client.log.debug("new method %r name=%r" % (self, name))
                method = RemoteMethod(self, name)
                self._methods[name] = method
            return method

    ######################################################

    def __repr__(self):
        return ("<%s 0x%x remote_ident=%r name=%r>" %
                (self.__class__.__name__, id(self), self._remote_ident, self._name))

#########################################################################
#########################################################################

class Wait(object):
    # helper for condition.wait() with reducing timeout
    # raises exception if the timeout is exceeded

    def __init__(self, client, timeout, remote_ident, req_id):
        self.client = client
        self.timeout = timeout
        self.remote_ident = remote_ident
        self.req_id = req_id

    def __call__(self, exc):
        if self.timeout is None:
            self.client.cond.wait()
        else:
            assert self.timeout > 0
            start_time = get_time()
            self.client.cond.wait(self.timeout)
            self.timeout -= get_time() - start_time
            if self.timeout <= 0:
                self.client.waiting_for_result.discard(self.req_id)
                raise exc

#########################################################################
#########################################################################

class RpcClient(object):
    def __init__(self, receive_hook, pickler=pickle):
        self.log = logging.getLogger("snakemq.rpc.client")
        self.receive_hook = receive_hook
        self.pickler = pickler
        self.method_proxies = {}
        self.exception_handler = None
        self.results = {}  #: req_id: result
        self.waiting_for_result = set()  # req_ids
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.connected = {}  #: remote_ident:bool

        receive_hook.register(REPLY_PREFIX, self.on_recv)
        receive_hook.messaging.on_connect.add(self.on_connect)
        receive_hook.messaging.on_disconnect.add(self.on_disconnect)

    ######################################################

    def send_params(self, remote_ident, params, ttl):
        raw = self.pickler.dumps(params)
        message = Message(data=REQUEST_PREFIX + raw, ttl=ttl)
        self.receive_hook.messaging.send_message(remote_ident, message)

    ######################################################

    def store_result(self, result):
        req_id = result["req_id"]
        try:
            self.waiting_for_result.remove(req_id)
        except KeyError:
            # this result is no longer needed
            pass
        else:
            self.results[req_id] = result

    ######################################################

    def get_result(self, req_id):
        assert req_id not in self.waiting_for_result
        return self.results.pop(req_id)

    ######################################################

    def on_connect(self, dummy_conn_id, ident):
        with self.cond:
            self.connected[ident] = True
            self.cond.notify_all()

    ######################################################

    def on_disconnect(self, dummy_conn_id, ident):
        with self.cond:
            self.connected[ident] = False
            self.cond.notify_all()

    ######################################################

    def on_recv(self, dummy_conn_id, dummy_ident, message):
        res = self.pickler.loads(message.data[len(REPLY_PREFIX):])
        if __debug__:
            self.log.debug("reply req_id=%r" % b2a_hex(res["req_id"]))
        with self.cond:
            self.store_result(res)
            self.cond.notify_all()

    ######################################################

    def call_regular(self, remote_ident, method, params):
        req_id = params.get("req_id")
        if req_id is None:
            req_id = bytes(uuid.uuid4().bytes)
            params["req_id"] = req_id

        if __debug__:
            self.log.debug("call_regular ident=%r obj=%r method=%r req_id=%s" %
                (remote_ident, params["object"], params["method"],
                b2a_hex(req_id)))

        wait = Wait(self, method.call_timeout, remote_ident, req_id)

        # repeat request until it is replied
        with self.cond:
            while True:
                # TODO check also message send failure (disconnect before msg dispatch)
                # for both with-timeout and without-timeout calls
                if self.connected.get(remote_ident):
                    self.waiting_for_result.add(req_id)
                    self.send_params(remote_ident, params, 0)
                    while ((req_id not in self.results) and
                              self.connected.get(remote_ident)):
                        wait(PartialCall)

                if self.connected.get(remote_ident):
                    res = self.get_result(req_id)
                    break
                else:
                    # "if" for this "else" serves 2 purposes
                    # - if the first "if" in the loop fails then this will
                    #   fail as well - peer is not connected, nothing was sent
                    # - if params were sent and then peer disconnected
                    wait(NotConnected)  # for signal from connect/di

        if res["ok"]:
            return res["return"]
        else:
            self.raise_remote_exception(res["exception"],
                                        res["exception_format"])

    ######################################################

    def call_signal(self, remote_ident, method, params):
        if __debug__:
            self.log.debug("call_signal ident=%r obj=%r method=%r" %
                (remote_ident, params["object"], params["method"]))
        self.send_params(remote_ident, params, method.signal_timeout)

    ######################################################

    def remote_request(self, remote_ident, method, params):
        if method.signal_timeout is None:
            return self.call_regular(remote_ident, method, params)
        else:
            self.call_signal(remote_ident, method, params)
            return None

    ######################################################

    def raise_remote_exception(self, exc, traceb):
        setattr(exc, REMOTE_TRACEBACK_ATTR, traceb)
        raise exc

    ######################################################

    def get_proxy(self, remote_ident, name):
        """
        @return: instance registered with register_object()
        """
        return RpcInstProxy(self, remote_ident, name)
