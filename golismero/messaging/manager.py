#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Message transport.
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

__all__ = ["MessageManager"]

from ..common import pickle
from ..api.config import Config

from os import getpid
from Queue import Queue
from thread import get_ident
from threading import Thread, RLock, Condition
from traceback import print_exc

import snakemq
import snakemq.link
import snakemq.packeter
import snakemq.messaging
import snakemq.message


#------------------------------------------------------------------------------
class MessageManager(Thread):
    DEBUG = False
    ##DEBUG = True    # uncomment for debugging


    #--------------------------------------------------------------------------
    def __init__(self, is_rpc = True):
        super(MessageManager, self).__init__()
        self.setDaemon(True)

        if self.DEBUG:
            import logging
            snakemq.init_logging(open("snakemq-%s.log" % getpid(), "w"))
            logger = logging.getLogger("snakemq")
            logger.setLevel(logging.DEBUG)

        self.__pid = getpid()
        self.__rpc_name = "golismero-rpc-%d" % self.__pid
        self.__queue_name = "golismero-queue-%d" % self.__pid
        if is_rpc:
            self.__name = self.__rpc_name
        else:
            self.__name = self.__queue_name
        self.debug("__init__(%r)" % self.name)

        self.__link = snakemq.link.Link()
        self.__packeter = snakemq.packeter.Packeter(self.__link)
        self.__messaging = snakemq.messaging.Messaging(
            self.__name, "", self.__packeter)
        self.__messaging.on_message_recv.add(self.__callback)

        self.__address = None

        self.__queue = Queue()
        ##self.__queue.mutex = RLock()
        ##self.__queue.not_empty = Condition(self.__queue.mutex)
        ##self.__queue.not_full = Condition(self.__queue.mutex)
        ##self.__queue.all_tasks_done = Condition(self.__queue.mutex)

        self.debug("__init__(%r) => completed" % self.name)


    #--------------------------------------------------------------------------
    @property
    def address(self):
        return self.__address


    #--------------------------------------------------------------------------
    @property
    def name(self):
        return self.__name


    #--------------------------------------------------------------------------
    def run(self):
        self.debug("run()")
        try:
            self.__link.loop()
            self.debug("run() => finished")
        except:
            self.debug("run() => ERROR")
            if self.DEBUG:
                print_exc()
        self.__link.cleanup()
        self.debug("run() => cleanup")


    #--------------------------------------------------------------------------
    def __callback(self, conn, name, message):
        self.debug("__callback(%r, %r, %r)", conn, name, message)
        data = pickle.loads(message.data)
        self.put(data)


    #--------------------------------------------------------------------------
    def listen(self, address = ("127.0.0.1", 0)):
        self.debug("listen(%r)", address)
        self.__address = self.__link.add_listener(address)
        return self.__address


    #--------------------------------------------------------------------------
    def connect(self, address):
        self.debug("connect(%r)", address)
        self.__link.add_connector(address)


    #--------------------------------------------------------------------------
    def close(self):
        if self.DEBUG:
            self.debug("close( pid=%s, tid=%s ) <= from pid %s, tid %s" %
                       (self.__pid, self.ident, getpid(), get_ident()))
        try:
            ##import time
            ##time.sleep(1.5)
            self.__link.stop()
        except:
            if self.DEBUG:
                import traceback
                traceback.print_exc()


    #--------------------------------------------------------------------------
    def send(self, name, data):
        if name == self.name:
            self.put(data)
        elif name == self.__rpc_name and Config._has_context:
            Config._context._msg_manager.put(data)
        else:
            ##if not Config._has_context:
            ##    import traceback
            ##    traceback.print_stack()
            self.debug("send(%r, %r)", name, data)
            raw = pickle.dumps(data)
            message = snakemq.message.Message(raw)
            self.__messaging.send_message(name, message)


    #--------------------------------------------------------------------------
    def put(self, data):
        self.debug("put(%r)", data)
        raw = pickle.dumps(data)
        self.__queue.put_nowait(raw)


    #--------------------------------------------------------------------------
    def get(self, timeout = None):
        self.debug("get()")
        raw = self.__queue.get(timeout = timeout)
        data = pickle.loads(raw)
        self.debug("get() => %r", data)
        return data


    #--------------------------------------------------------------------------
    def debug(self, msg, *vars):
        if self.DEBUG:
            with open("%s.log" % self.name, "a") as f:
                f.write((str(msg) + "\n") % vars)
