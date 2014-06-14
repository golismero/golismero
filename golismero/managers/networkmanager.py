#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager for network connections.
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

__all__ = ["NetworkManager"]

from .rpcmanager import implementor
from ..common import random
from ..messaging.codes import MessageCode

from collections import defaultdict
from threading import BoundedSemaphore, RLock


#------------------------------------------------------------------------------
# RPC implementors for the network connection manager API.

@implementor(MessageCode.MSG_RPC_REQUEST_SLOT, blocking=True)
def rpc_netdb_request_slot(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.netManager.request_slot(audit_name, *args, **kwargs)

@implementor(MessageCode.MSG_RPC_RELEASE_SLOT)
def rpc_netdb_release_slot(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.netManager.release_slot(audit_name, *args, **kwargs)


#------------------------------------------------------------------------------
class NetworkManager (object):
    """
    Manager for network connections.
    """


    #--------------------------------------------------------------------------
    def __init__(self, config):
        """
        :param config: Global configuration object.
        :type config: OrchestratorConfig
        """

        # Keep a reference to the global configuration.
        self.__config = config

        # Lock to access the internal structures.
        self.__rlock = RLock()

        # Map of hosts to global connection count.
        self.__counts = defaultdict(int)   # host -> int

        # Map of hosts to global connection semaphores.
        self.__semaphores = defaultdict(self.__create_semaphore) # host -> sem

        # Map of audit tokens.
        self.__tokens = defaultdict(dict) # audit -> token -> (host, number)


    #--------------------------------------------------------------------------
    @property
    def max_connections(self):
        """
        :returns: Maximum allowed number of connection slots per host.
        :rtype: int
        """
        return self.__config.max_connections


    #--------------------------------------------------------------------------
    def __create_semaphore(self):
        return BoundedSemaphore(self.max_connections)


    #--------------------------------------------------------------------------
    def request_slot(self, audit_name, host, number = 1):
        """
        Request the given number of connection slots for a host.
        Blocks until the requested slots become available.

        .. warning: Currently requesting more than one slot is not supported.
            There's a good reason for this, so don't try calling this method
            multiple times to work around the limitation!

        :param audit_name: Audit name.
        :type audit_name: str

        :param host: Host to connect to.
        :type host: str

        :param number: Number of connection slots to request.
        :type number: int

        :returns: Request token.
        :rtype: str
        """
        if number != 1:
            raise NotImplementedError()
        ##if number <= 0:
        ##    raise ValueError("Number of slots can't be negative")
        ##if number > self.max_connections:
        ##    raise ValueError("Requested too many slots")
        token = None
        host  = host.lower()

        with self.__rlock:
            sem = self.__semaphores[host]
            self.__tokens[audit_name] # make sure it exists
        sem.acquire()
        try:
            with self.__rlock:
                if audit_name not in self.__tokens:
                    raise RuntimeError("Audit is shutting down")
                token = "%.8X|%s" % (random.randint(0, 0x7FFFFFFF), host)
                self.__tokens[audit_name][token] = (host, number)
                self.__counts[host] += 1
                return token
        except:
            try:
                if token is not None:
                    with self.__rlock:
                        del self.__tokens[audit_name][token]
            finally:
                sem.release()
            raise


    #--------------------------------------------------------------------------
    def release_slot(self, audit_name, token):
        """
        Release a previously requested number of connection slots for a host.

        This method doesn't raise any exceptions.

        :param audit_name: Audit name.
        :type audit_name: str

        :param token: Request token.
        :type token: str
        """
        try:
            with self.__rlock:
                host, number = self.__tokens[audit_name].pop(token)
                sem = self.__semaphores[host]
                try:
                    self.__counts[host] -= number
                    if self.__counts[host] <= 0:
                        del self.__counts[host]
                        del self.__semaphores[host]
                finally:
                    sem.release()
        except Exception:
            pass


    #--------------------------------------------------------------------------
    def release_all_slots(self, audit_name):
        """
        Release all connection slots for the given audit.

        :param audit_name: Audit name.
        :type audit_name: str
        """
        with self.__rlock:
            for host, number in self.__tokens.pop(audit_name, {}).itervalues():
                try:
                    sem = self.__semaphores[host]
                    try:
                        self.__counts[host] -= number
                        if self.__counts[host] <= 0:
                            del self.__counts[host]
                            del self.__semaphores[host]
                    finally:
                        sem.release()
                except:
                    pass
