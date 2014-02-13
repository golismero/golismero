#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Network cache API.
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

__all__ = ["NetworkCache"]

from ..config import Config
from ...common import Singleton
from ...messaging.codes import MessageCode

from collections import defaultdict
from functools import partial


#------------------------------------------------------------------------------
class _NetworkCache(Singleton):
    """
    Cache for network resources, separated by protocol.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        self._clear_local_cache()


    #--------------------------------------------------------------------------
    def _clear_local_cache(self):
        """
        .. warning: Do not call!
        """

        # This method is called from the plugin bootstrap.

        # During the lifetime of the plugin,
        # results from the centralized cache
        # are also stored in memory here.
        #
        # audit -> protocol -> key -> data
        #
        self.__cache = defaultdict( partial(defaultdict, dict) )


    #--------------------------------------------------------------------------
    def get(self, key, protocol):
        """
        Get a network resource from the cache.

        :param key: Key to reference the network resource.
        :type key: str

        :param protocol: Network protocol.
        :type protocol: str

        :returns: Resource from the cache, None if not found.
        :rtype: object | None
        """

        # First, try to get the resource from the local cache.
        data = self.__cache[Config.audit_name][protocol].get(key, None)
        if data is None:

            # If not found locally, query the global cache.
            data = Config._context.remote_call(
                                MessageCode.MSG_RPC_CACHE_GET, key, protocol)

            # Store the global cache result locally.
            if data is not None:
                self.__cache[Config.audit_name][protocol][key] = data

        # Return the cached data.
        return data


    #--------------------------------------------------------------------------
    def set(self, key, data, protocol, timestamp=None, lifespan=None):
        """
        Store a network resource in the cache.

        :param key: Key to reference the network resource.
        :type key: str

        :param data: Data to store in the cache.
        :type data: object

        :param protocol: Network protocol.
        :type protocol: str

        :param timestamp: Timestamp for this network resource.
        :type timestamp: int

        :param lifespan: Time to live in the cache.
        :type lifespan: int
        """

        # Store the resource in the local cache.
        self.__cache[Config.audit_name][protocol][key] = data

        # Send the resource to the global cache.
        Config._context.async_remote_call(
                            MessageCode.MSG_RPC_CACHE_SET, key, protocol, data)


    #--------------------------------------------------------------------------
    def remove(self, key, protocol):
        """
        Remove a network resource from the cache.

        :param key: Key to reference the network resource.
        :type key: str

        :param protocol: Network protocol.
        :type protocol: str
        """

        # Remove the resource from the local cache.
        try:
            del self.__cache[Config.audit_name][protocol][key]
        except KeyError:
            pass

        # Remove the resource from the global cache.
        Config._context.async_remote_call(
                            MessageCode.MSG_RPC_CACHE_REMOVE, key, protocol)


    #--------------------------------------------------------------------------
    def exists(self, key, protocol):
        """
        Verify if the given key exists in the cache.

        :param key: Key to reference the network resource.
        :type key: str

        :returns: True if the resource is in the cache, False otherwise.
        :rtype: bool
        """

        # First, check if it's in the local cache.
        found = key in self.__cache[Config.audit_name][protocol]

        # If not found, check the global cache.
        if not found:
            found = Config._context.remote_call(
                                MessageCode.MSG_RPC_CACHE_CHECK, key, protocol)
            found = bool(found)

        # Return the status.
        return found


#------------------------------------------------------------------------------

# Singleton pattern.
NetworkCache = _NetworkCache()
