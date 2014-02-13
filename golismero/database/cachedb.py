#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Network cache implementations.
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

__all__ = ["PersistentNetworkCache", "VolatileNetworkCache"]

from .common import BaseDB, atomic, transactional

from ..common import get_user_settings_folder
from ..managers.rpcmanager import implementor
from ..messaging.codes import MessageCode

from collections import defaultdict
from functools import partial
from os.path import join

# Lazy imports
sqlite3 = None


#------------------------------------------------------------------------------
# Cache API implementors

@implementor(MessageCode.MSG_RPC_CACHE_GET)
def rpc_cache_get(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cacheManager.get(audit_name, *args, **kwargs)

@implementor(MessageCode.MSG_RPC_CACHE_SET)
def rpc_cache_set(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cacheManager.set(audit_name, *args, **kwargs)

@implementor(MessageCode.MSG_RPC_CACHE_CHECK)
def rpc_cache_check(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cacheManager.exists(audit_name, *args, **kwargs)

@implementor(MessageCode.MSG_RPC_CACHE_REMOVE)
def rpc_cache_remove(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cacheManager.remove(audit_name, *args, **kwargs)


#------------------------------------------------------------------------------
class BaseNetworkCache(BaseDB):
    """
    Abtract class for network cache databases.
    """


    #--------------------------------------------------------------------------
    @staticmethod
    def _sanitize_protocol(protocol):
        protocol = protocol.lower()
        if "://" in protocol:
            protocol = protocol[:protocol.find("://")]
        return protocol


    #--------------------------------------------------------------------------
    def get(self, audit, key, protocol="http"):
        """
        Get a network resource from the cache.

        :param key: key to reference the network resource
        :type key: str

        :param protocol: network protocol
        :type protocol: str

        :returns: object -- resource from the cache | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set(self, audit, key, data, protocol="http", timestamp=None, lifespan=None):
        """
        Store a network resource in the cache.

        :param key: key to reference the network resource
        :type key: str

        :param data: data to store in the cache
        :type data: object

        :param protocol: network protocol
        :type protocol: str

        :param timestamp: timestamp for this network resource
        :type timestamp: int

        :param lifespan: time to live in the cache
        :type lifespan: int
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove(self, audit, key, protocol="http"):
        """
        Remove a network resource from the cache.

        :param key: key to reference the network resource
        :type key: str

        :param protocol: network protocol
        :type protocol: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def exists(self, audit, key, protocol="http"):
        """
        Verify if the given key exists in the cache.

        :param key: key to reference the network resource
        :type key: str

        :returns: True if the resource is in the cache, False otherwise.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def clean(self, audit):
        """
        Delete all cache entries for the given audit.

        :param audit: Audit name.
        :type audit: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


#------------------------------------------------------------------------------
class VolatileNetworkCache(BaseNetworkCache):
    """
    In-memory cache for network resources, separated by protocol.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        # audit -> protocol -> key -> data
        self.__cache = defaultdict( partial(defaultdict, dict) )


    #--------------------------------------------------------------------------
    def get(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        return self.__cache[audit][protocol].get(key, None)


    #--------------------------------------------------------------------------
    def set(self, audit, key, data, protocol="http", timestamp=None, lifespan=None):
        protocol = self._sanitize_protocol(protocol)

        # FIXME: timestamp and lifespan not yet supported in volatile mode!
        self.__cache[audit][protocol][key] = data


    #--------------------------------------------------------------------------
    def remove(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        try:
            del self.__cache[audit][protocol][key]
        except KeyError:
            pass


    #--------------------------------------------------------------------------
    def exists(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        return key in self.__cache[audit][protocol]


    #--------------------------------------------------------------------------
    def clean(self, audit):
        self.__cache[audit] = defaultdict(dict)


    #--------------------------------------------------------------------------
    def close(self):
        self.__cache = defaultdict( partial(defaultdict, dict) )


    #--------------------------------------------------------------------------
    def dump(self, filename):
        pass


#------------------------------------------------------------------------------
class PersistentNetworkCache(BaseNetworkCache):
    """
    Network cache with a database backend.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        filename = join(get_user_settings_folder(), "cache.db")
        global sqlite3
        if sqlite3 is None:
            import sqlite3
        self.__db = sqlite3.connect(filename)
        self.__cursor = None
        self.__busy = False
        self.__create()


    #--------------------------------------------------------------------------
    def _atom(self, fn, args, kwargs):
        # this will fail for multithreaded accesses,
        # but sqlite is not multithreaded either
        if self.__busy:
            raise RuntimeError("The database is busy")
        try:
            self.__busy = True
            return fn(self, *args, **kwargs)
        finally:
            self.__busy = False


    #--------------------------------------------------------------------------
    def _transaction(self, fn, args, kwargs):
        # this will fail for multithreaded accesses,
        # but sqlite is not multithreaded either
        if self.__busy:
            raise RuntimeError("The database is busy")
        try:
            self.__busy = True
            self.__cursor = self.__db.cursor()
            try:
                retval = fn(self, *args, **kwargs)
                self.__db.commit()
                return retval
            except:
                self.__db.rollback()
                raise
        finally:
            self.__cursor = None
            self.__busy = False


    #--------------------------------------------------------------------------
    @transactional
    def __create(self):
        """
        Create the database schema if needed.
        """
        self.__cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                audit STRING NOT NULL,
                protocol STRING NOT NULL,
                key STRING NOT NULL,
                timestamp INTEGER NOT NULL
                          DEFAULT CURRENT_TIMESTAMP,
                lifespan INTEGER NOT NULL
                         DEFAULT 0,
                data BLOB NOT NULL,

                UNIQUE (audit, protocol, key) ON CONFLICT REPLACE
            );
        """)


    #--------------------------------------------------------------------------
    @transactional
    def get(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        self.__cursor.execute("""
            SELECT data FROM cache
            WHERE audit = ? AND key = ? AND protocol = ?
                AND (timestamp = 0 OR lifespan = 0 OR
                     timestamp + lifespan > CURRENT_TIMESTAMP
                )
            LIMIT 1;
        """, (audit, key, protocol) )
        row = self.__cursor.fetchone()
        if row is not None:
            return self.decode(row[0])


    #--------------------------------------------------------------------------
    @transactional
    def set(self, audit, key, data, protocol="http", timestamp=None, lifespan=None):
        protocol = self._sanitize_protocol(protocol)
        data = self.encode(data)
        data = sqlite3.Binary(data)
        if lifespan is None:
            lifespan = 0
        if timestamp is None:
            self.__cursor.execute("""
                INSERT INTO cache (audit, key, protocol, data, lifespan)
                VALUES            (  ?,    ?,     ?,       ?,     ?    );
            """,                  (audit, key, protocol, data, lifespan))
        else:
            self.__cursor.execute("""
                INSERT INTO cache (audit, key, protocol, data, timestamp, lifespan)
                VALUES            (  ?,    ?,     ?,       ?,      ?,        ?    );
            """,                  (audit, key, protocol, data, timestamp, lifespan))


    #--------------------------------------------------------------------------
    @transactional
    def remove(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        self.__cursor.execute("""
            DELETE FROM cache
            WHERE audit = ? AND key = ? AND protocol = ?;
        """,     (audit,        key,        protocol) )


    #--------------------------------------------------------------------------
    @transactional
    def exists(self, audit, key, protocol="http"):
        protocol = self._sanitize_protocol(protocol)
        self.__cursor.execute("""
            SELECT COUNT(id) FROM cache
            WHERE audit = ? AND key = ? AND protocol = ?
                AND (timestamp = 0 OR lifespan = 0 OR
                     timestamp + lifespan > CURRENT_TIMESTAMP
                )
            LIMIT 1;
        """, (audit, key, protocol))
        return bool(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def clean(self, audit):
        self.__cursor.execute("""
            DELETE FROM cache
            WHERE audit = ?;
        """, (audit,))


    #--------------------------------------------------------------------------
    def compact(self):
        try:
            self.__clear_old_entries()
            self.__vacuum()
        except sqlite3.Error:
            pass

    @transactional
    def __clear_old_entries(self):
        self.__cursor.execute("""
            DELETE FROM cache
                WHERE timestamp != 0 AND lifespan != 0 AND
                      timestamp + lifespan <= CURRENT_TIMESTAMP;
        """)

    @transactional
    def __vacuum(self):
        self.__cursor.execute("VACUUM;")


    #--------------------------------------------------------------------------
    @atomic
    def dump(self, filename):
        with open(filename, 'w') as f:
            for line in self.__db.iterdump():
                f.write(line + "\n")


    #--------------------------------------------------------------------------
    @atomic
    def close(self):
        try:
            self.__db.close()
        except Exception:
            pass
