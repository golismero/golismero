#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Audit database support.

Here are the DAOs for all supported databases for audits.
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

__all__ = ["AuditDB"]

from .common import BaseDB, atomic, transactional
from ..api.data import Data, Relationship
##from ..api.shared import check_value   # FIXME do server-side checks too!
from ..api.text.text_utils import generate_random_string
from ..messaging.codes import MessageCode
from ..managers.rpcmanager import implementor

from os import path, makedirs

import md5
import sqlite3
import threading
import time
import warnings

# Lazy imports
pymongo  = None
binary   = None
objectid = None
Error    = None


#------------------------------------------------------------------------------
# RPC implementors for the database API.

@implementor(MessageCode.MSG_RPC_DATA_ADD)
def rpc_data_db_add(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.add_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_ADD_MANY)
def rpc_data_db_add_many(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.add_many_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_REMOVE)
def rpc_data_db_remove(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.remove_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_REMOVE_MANY)
def rpc_data_db_remove_many(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.remove_many_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_CHECK)
def rpc_data_db_check(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_data_key(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_GET)
def rpc_data_db_get(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_GET_MANY)
def rpc_data_db_get_many(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_many_data(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_KEYS)
def rpc_data_db_keys(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_data_keys(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_COUNT)
def rpc_data_db_count(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_data_count(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_DATA_PLUGINS)
def rpc_data_db_plugins(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_past_plugins(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_GET)
def rpc_shared_map_get(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_mapped_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_CHECK_ALL)
def rpc_shared_map_check_all(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_all_mapped_keys(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_CHECK_ANY)
def rpc_shared_map_check_any(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_any_mapped_key(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_CHECK_EACH)
def rpc_shared_map_check_each(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_each_mapped_key(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_POP)
def rpc_shared_map_pop(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.pop_mapped_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_PUT)
def rpc_shared_map_put(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.put_mapped_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_SWAP)
def rpc_shared_map_swap(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.swap_mapped_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_DELETE)
def rpc_shared_map_delete(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.delete_mapped_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_MAP_KEYS)
def rpc_shared_map_keys(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_mapped_keys(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_CHECK_ALL)
def rpc_shared_heap_check_all(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_all_shared_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_CHECK_ANY)
def rpc_shared_heap_check_any(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_any_shared_value(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_CHECK_EACH)
def rpc_shared_heap_check_each(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_each_shared_value(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_POP)
def rpc_shared_heap_pop(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.pop_shared_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_ADD)
def rpc_shared_heap_add(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.add_shared_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_SHARED_HEAP_REMOVE)
def rpc_shared_heap_remove(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.remove_shared_values(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_AUDIT_LOG)
def rpc_get_log_lines(orchestrator, current_audit_name, audit_name, *args, **kwargs):
    if not audit_name:
        audit_name = current_audit_name
    return orchestrator.auditManager.get_audit(audit_name).database.get_log_lines(*args, **kwargs)


#------------------------------------------------------------------------------
class BaseAuditDB (BaseDB):
    """
    Storage of Audit results.
    """


    #--------------------------------------------------------------------------
    def __init__(self, audit_config):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """
        if not audit_config.audit_name:
            audit_config.audit_name = self.generate_audit_name()
        self.__audit_name = audit_config.audit_name


    #--------------------------------------------------------------------------
    @classmethod
    def get_config_from_closed_database(cls, audit_db, audit_name = None):
        """
        Retrieve the audit configuration from a closed database.

        To get the configuration from an open database object, use the
        get_config() method instead.

        :param audit_db: Audit database connection string.
        :type audit_db: str

        :param audit_name: Optional, audit name.
        :type audit_name: str | None

        :returns: Audit configuration and scope.
        :rtype: AuditConfig, AuditScope

        :raises IOError: The database could not be opened.
        """
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def audit_name(self):
        """
        :returns: Audit name.
        :rtype: str
        """
        return self.__audit_name


    #--------------------------------------------------------------------------
    @staticmethod
    def generate_audit_name():
        """
        Generate a default name for a new audit.

        :returns: Generated name.
        :rtype: str
        """
        return "golismero-" + generate_random_string(length=8)


    #--------------------------------------------------------------------------
    def get_audit_times(self):
        """
        Get the audit start and stop times.

        :returns: Audit start time (None if it hasn't started yet)
            and audit stop time (None if it hasn't finished yet).
            Times are returned as POSIX timestamps.
        :rtype: tuple(float|None, float|None)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set_audit_times(self, start_time, stop_time):
        """
        Set the audit start and stop times.

        :param start_time: Audit start time (None if it hasn't started yet).
            Time is given as a POSIX timestamp.
        :type start_time: float | None

        :param stop_time: Audit stop time (None if it hasn't finished yet).
            Time is given as a POSIX timestamp.
        :type stop_time: float | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set_audit_start_time(self, start_time):
        """
        Set the audit start time.

        :param start_time: Audit start time (None if it hasn't started yet).
            Time is given as a POSIX timestamp.
        :type start_time: float | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set_audit_stop_time(self, stop_time):
        """
        Set the audit stop time.

        :param stop_time: Audit stop time (None if it hasn't finished yet).
            Time is given as a POSIX timestamp.
        :type stop_time: float | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_audit_config(self):
        """
        :returns: Audit configuration.
        :rtype: AuditConfig
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def save_audit_config(self, audit_config):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_audit_scope(self):
        """
        :returns: Audit scope.
        :rtype: AuditScope
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def save_audit_scope(self, audit_scope):
        """
        :param audit_scope: Audit scope.
        :type audit_scope: AuditScope
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def append_log_line(self, text, level,
                         is_error = False,
                        plugin_id = None,
                           ack_id = None,
                        timestamp = None):
        """
        Append a log line.

        :param text: Log line text.
        :type text: str

        :param level: Log level.
        :type level: int

        :param is_error: True if the message is an error, False otherwise.
        :type is_error: bool

        :param plugin_id: Plugin ID.
        :type plugin_id: str

        :param ack_id: Data ID.
        :type ack_id: str

        :param timestamp: Optional timestamp.
            If missing the current time is used.
        :type timestamp: float | int | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_log_lines(self, from_timestamp = None, to_timestamp = None,
                      filter_by_plugin = None, filter_by_data = None,
                      page_num = None, per_page = None):
        """
        Retrieve past log lines.

        :param from_timestamp: (Optional) Start timestamp.
        :type from_timestamp: float | None

        :param to_timestamp: (Optional) End timestamp.
        :type to_timestamp: float | None

        :param filter_by_plugin: (Optional) Filter log lines by plugin ID.
        :type filter_by_plugin: str

        :param filter_by_data: (Optional) Filter log lines by data ID.
        :type filter_by_data: str

        :param page_num: (Optional) Page number.
            Ignored unless per_page is used too.
        :type page_num: int

        :param per_page: (Optional) Amount of results per page.
            Ignored unless page_num is used too.
        :type per_page: int

        :returns: List of tuples.
            Each tuple contains the following elements:
             - Plugin ID.
             - Data object ID (plugin instance).
             - Log line text. May contain newline characters.
             - Log level.
             - True if the message is an error, False otherwise.
             - Timestamp.
        :rtype: list( tuple(str, str, str, int, bool, float) )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def add_data(self, data):
        """
        Add data to the database.

        :param data: Data to add.
        :type data: Data

        :returns: True if the data was new, False if it was updated.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def add_many_data(self, dataset):
        """
        Add multiple data objects to the database.

        :param dataset: Data to add.
        :type dataset: list(Data)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove_data(self, identity):
        """
        Remove data given its identity hash.

        :param identity: Identity hash.
        :type identity: str

        :returns: True if the object was removed, False if it didn't exist.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove_many_data(self, identities):
        """
        Remove multiple data objects given their identity hashes.

        :param identities: Identity hashes.
        :type identities: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_data_key(self, identity):
        """
        Check if a data object with the given
        identity hash is present in the database.

        :param identity: Identity hash.
        :type identity: str

        :returns: True if the object is present, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data(self, identity):
        """
        Get an object given its identity hash.

        :param identity: Identity hash.
        :type identity: str

        :returns: Data object.
        :rtype: Data | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_many_data(self, identities):
        """
        Get multiple objects given their identity hashes.

        :param identities: Identity hashes.
        :type identities: set(str)

        :returns: Data objects.
        :rtype: list(Data)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data_keys(self, data_type = None, data_subtype = None):
        """
        Get a list of identity hashes for all objects of the requested
        type, optionally filtering by subtype.

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int | None

        :param data_subtype: Optional data subtype.
        :type data_subtype: str | None

        :returns: Identity hashes.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data_count(self, data_type = None, data_subtype = None):
        """
        Count all objects of the requested type,
        optionally filtering by subtype.

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int | None

        :param data_subtype: Optional data subtype.
        :type data_subtype: str | None

        :returns: Identity hashes.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data_types(self, identities):
        """
        Get a set of data types and subtypes for all objects
        of the requested identities.

        :param identities: Identity hashes.
        :type identities: set(str)

        :returns: Set of data types and subtypes found.
        :rtype: set( (int, str) )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def mark_plugin_finished(self, identity, plugin_id):
        """
        Mark the data as having been processed by the plugin.

        :param identity: Identity hash.
        :type identity: str

        :param plugin_id: Plugin ID.
        :type plplugin_idstr
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def mark_stage_finished(self, identity, stage):
        """
        Mark the data as having completed the stage.

        :param identity: Identity hash.
        :type identity: str

        :param stage: Stage.
        :type stage: int
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def mark_stage_finished_many(self, identities, stage):
        """
        Mark the data as having completed the stage.

        :param identities: Identity hashes.
        :type identities: set(str)

        :param stage: Stage.
        :type stage: int
        """
        for identity in identities:
            self.mark_stage_finished(identity, stage)


    #--------------------------------------------------------------------------
    def clear_stage_mark(self, identity):
        """
        Clear the completed stages mark for the given data.

        :param identity: Identity hash.
        :type identity: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def clear_all_stage_marks(self):
        """
        Clear the completed stages mark for all the data.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_past_plugins(self, identity):
        """
        Get the plugins that have already processed the given data.

        :param identity: Identity hash.
        :type identity: str

        :returns: Set of plugin IDs.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def clear_plugin_history(self, identity):
        """
        Clear the past plugins history for the given data.

        :param identity: Identity hash.
        :type identity: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def clear_all_plugin_history(self):
        """
        Clear the past plugins history for all the data.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_pending_data(self, stage):
        """
        Get the identities of the data objects that haven't yet completed
        the requested stage.

        :param stage: Stage.
        :type stage: int

        :returns: Set of identities.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_mapped_values(self, shared_id, keys):
        """
        Get the values mapped in the requested shared map.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param key: Keys to look for.
        :type key: tuple( immutable, ... )

        :returns: Values mapped to the requested keys, in the same order.
        :rtype: tuple( immutable, ... )

        :raises KeyError: Not all keys were mapped.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_all_mapped_keys(self, shared_id, keys):
        """
        Check if all of the given keys has been defined.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: True if all keys were defined, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_any_mapped_key(self, shared_id, keys):
        """
        Check if any of the given keys has been defined.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: True if any of the keys was defined, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_each_mapped_key(self, shared_id, keys):
        """
        Check if each of the given keys has been defined.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: Tuple with the results, in the same order, for each key.
            True for each defined key, False for each undefined key.
        :rtype: tuple( bool, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def pop_mapped_values(self, shared_id, keys):
        """
        Get the values for the given keys and remove them from the map.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param keys: Keys to look for.
        :type keys: tuple(immutable, ...)

        :returns: Values mapped to the requested keys, in the same order.
        :rtype: tuple(immutable, ...)

        :raises KeyError: Not all keys were mapped.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def put_mapped_values(self, shared_id, items):
        """
        Map the given keys to the given values.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param items: Keys and values to map, in (key, value) tuples.
        :type items: tuple( tuple(immutable, immutable), ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def swap_mapped_values(self, shared_id, items):
        """
        Map the given keys to the given values, and return the previous values.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param items: Keys and values to map, in (key, value) tuples.
        :type items: tuple( tuple(immutable, immutable), ... )

        :returns: Previous mapped values, if any, in the same order.
            None for each missing key.
        :rtype: tuple( immutable | None, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def delete_mapped_values(self, shared_id, keys):
        """
        Delete the given keys from the map.

        .. note: If any of the keys was not defined, no error is raised.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :param keys: Keys to delete.
        :type keys: tuple( immutable, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_mapped_keys(self, shared_id):
        """
        Get the values mapped in the requested shared map.

        :param shared_id: Shared map ID.
        :type shared_id: str

        :returns: Keys defined in this shared map.
        :rtype: set(immutable)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_all_shared_values(self, shared_id, values):
        """
        Check if all of the given values are present in the shared container.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: True if all of the values were found, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_any_shared_value(self, shared_id, values):
        """
        Check if any of the given values are present in the shared container.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: True if any of the values was found, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_each_shared_value(self, shared_id, values):
        """
        Check if each of the given values is present in the shared container.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: Tuple with the results, in the same order, for each value.
            True for each value found, False for each not found.
        :rtype: tuple( bool, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def pop_shared_values(self, shared_id, maximum):
        """
        Get multiple random values from the shared container and remove them.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param maximum: Maximum number of values to retrieve.
            This method may return less than this number if there aren't enough
            values in the shared container.

        :returns: Values removed from the shared container, in any order.
            If the shared container was empty, returns an empty tuple.
        :rtype: tuple( immutable, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def add_shared_values(self, shared_id, values):
        """
        Add the given values to the shared container.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param values: Values to add.
        :type values: tuple( immutable, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove_shared_values(self, shared_id, values):
        """
        Remove the given values from the shared container.

        .. note: If any of the values was not found, no error is raised.

        :param shared_id: Shared container ID.
        :type shared_id: str

        :param values: Values to remove.
        :type values: tuple( immutable, ... )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


#------------------------------------------------------------------------------
class AuditSQLiteDB (BaseAuditDB):
    """
    Stores Audit results in a database file using SQLite.
    """

    # The current schema version.
    SCHEMA_VERSION = 3


    #--------------------------------------------------------------------------
    def __init__(self, audit_config):

        # Initialize the busy flag and the database cursor.
        self.__busy   = False
        self.__cursor = None

        # Create the lock to make this class thread safe.
        self.__lock = threading.RLock()

        # Create the data subtypes cache.
        self.__data_subtype_cache = {} # name -> id
        self.__data_subtype_reverse_cache = {} # id -> name

        # Get the filename from the connection string.
        filename = self.__parse_connection_string(
            audit_config.audit_db, audit_config.audit_name)

        # See if we have a filename, and an old database file.
        have_file = (
            filename and
            filename != ":memory:" and
            path.exists(filename)
        )

        # If we have a filename...
        if filename and filename != ":memory:":

            # If we have an old database...
            if have_file:

                # Open the database.
                self.__filename = filename
                self.__db = sqlite3.connect(filename)

                # Get the audit name from the database.
                audit_name = self.__get_audit_name_from_database()

                # If the database contains an audit name...
                if audit_name:

                    # If the user didn't set one, use this audit name.
                    if not audit_config.audit_name:
                        audit_config.audit_name = audit_name

                    # If the user did set one but they don't match, fail.
                    elif audit_config.audit_name != audit_name:
                        raise IOError(
                            "Database belongs to another audit:\n\t%r vs. %r" %
                            (self.audit_name, audit_config.audit_name)
                        )

            # Just the filename, no file.
            # If the user didn't set an audit name...
            elif not audit_config.audit_name:

                # Guess the audit name from the file name.
                audit_config.audit_name = path.splitext(
                    path.basename(filename))[0]

        # Call the superclass constructor.
        # This generates an audit name if we don't have any,
        # and updates the audit name in the config object.
        super(AuditSQLiteDB, self).__init__(audit_config)

        # If we don't have an old database...
        if not have_file:

            # If we don't have a filename, make one from the audit name.
            # (This is not redundant, the name may have been autogenerated).
            if not filename:
                filename = "".join(
                    (c if c in "-_~" or c.isalnum() else "_")
                    for c in self.audit_name
                )
                filename = filename + ".db"

            # Make sure the directory exists.
            if filename != ":memory:":
                directory = path.split(filename)[0]
                if directory and not path.exists(directory):
                    try:
                        makedirs(directory)
                    except Exception, e:
                        warnings.warn(
                            "Error creating directory %r: %s" %
                            (directory, str(e)),
                            RuntimeWarning
                        )

            # Save the filename.
            self.__filename = filename

            # Create the database file.
            self.__db = sqlite3.connect(filename)
            self.__db.text_factory = lambda x: unicode(x, "utf-8", "ignore")

        # Update the database filename.
        if self.__filename != ":memory:":
            audit_config.audit_db = self.__filename

        # Create or validate the database schema.
        # This raises an exception on error.
        self.__create(audit_config)

        # Load any existing data subtypes into the cache.
        self.__load_data_subtype_cache()


    #--------------------------------------------------------------------------
    @staticmethod
    def __parse_connection_string(audit_db, audit_name = None):
        """
        :param audit_db: Optional, database filename.
        :type audit_db: str | None

        :param audit_name: Optional, audit name.
        :type audit_name: str | None

        :returns: Database filename, or None on error.
        :rtype: str | None
        """

        # If we don't have a filename but we have an audit name...
        if not audit_db or audit_db == ":auto:":
            audit_db = None
            if audit_name:

                # Generate the filename from the audit name.
                audit_db = "".join(
                    (c if c in "-_~" or c.isalnum() else "_")
                    for c in audit_name
                )
                audit_db = audit_db + ".db"

        # Return the filename.
        return audit_db


    #--------------------------------------------------------------------------
    @classmethod
    def get_config_from_closed_database(cls, audit_db, audit_name = None):

        # Get the filename from the connection string.
        filename = cls.__parse_connection_string(audit_db, audit_name)

        # Fail if we didn't get a filename.
        if not filename:
            raise IOError("Missing database filename!")

        # Fail if the filename doesn't exist.
        if not path.exists(filename):
            raise IOError("Database file not found: %s" % filename)

        # Open the database.
        db = sqlite3.connect(filename)

        try:
            try:

                # Start a transaction.
                cursor = db.cursor()

                try:

                    # Read the config.
                    cursor.execute(
                        "SELECT audit_config, audit_scope"
                        " FROM golismero"
                        " LIMIT 1;")
                    row = cursor.fetchone()
                    if not row:
                        raise IOError("Missing data in database!")
                    try:
                        audit_config = cls.decode(row[0])
                        audit_scope  = cls.decode(row[1])
                    except Exception:
                        raise IOError("Corrupted database!")

                    # Finish the transaction.
                    db.commit()

                    # Return the config and scope.
                    return audit_config, audit_scope

                except:

                    # On error, roll back.
                    db.rollback()

                    # Re-raise the exception.
                    raise

            except sqlite3.Error, e:

                # Raise SQL errors as IO errors.
                raise IOError(str(e))

        finally:

            # Close the database.
            db.close()


    #--------------------------------------------------------------------------
    @property
    def filename(self):
        """
        :returns: SQLite file name.
        :rtype: str
        """
        return self.__filename


    #--------------------------------------------------------------------------
    def encode(self, data):

        # Encode the data.
        data = super(AuditSQLiteDB, self).encode(data)

        # Tell SQLite the encoded data is a BLOB and not a TEXT.
        return sqlite3.Binary(data)


    #--------------------------------------------------------------------------
    def get_hash(self, data):
        """
        Calculate a hash of the given data.
        """

        # Encode the data as raw bytes.
        data = super(AuditSQLiteDB, self).encode(data)

        # Return the MD5 hexadecimal digest of the data.
        h = md5.new()
        h.update(data)
        return h.hexdigest()


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
        """
        Execute a transactional operation.
        """
        with self.__lock:
            if self.__busy:
                raise RuntimeError("The database is busy")
            try:
                self.__busy   = True
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
                self.__busy   = False


    #--------------------------------------------------------------------------
    @transactional
    def __create(self, audit_config):
        """
        Create the database schema if needed.

        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """

        # Check if the schema is already created.
        self.__cursor.execute(
            "SELECT count(*) FROM sqlite_master"
            " WHERE type = 'table' AND name = 'golismero';"
        )

        # If it's already present...
        if self.__cursor.fetchone()[0]:

            # Check if the schema version and audit name match.
            self.__cursor.execute(
                "SELECT schema_version, audit_name FROM golismero LIMIT 1;")
            row = self.__cursor.fetchone()
            if not row:
                raise IOError("Broken database!")
            if row[0] != self.SCHEMA_VERSION:
                raise IOError(
                    "Incompatible schema version: %s != %s" % \
                    (row[0], self.SCHEMA_VERSION))
            if row[1] != self.audit_name:
                raise IOError(
                    "Database belongs to another audit:\n\t\"%s\" vs. \"%s\"" % \
                    (row[1], self.audit_name))

            # TODO: add a sanity check on the data

        # If not present...
        else:

            # Create the schema.
            self.__cursor.executescript(
            """

            -- Enable foreign keys support.
            PRAGMA foreign_keys = ON;

            ----------------------------------------------------------
            -- Table to store the file information.
            -- There must only be one row in it.
            ----------------------------------------------------------

            CREATE TABLE golismero (
                schema_version INTEGER NOT NULL,
                audit_name STRING NOT NULL,
                start_time REAL DEFAULT NULL,
                stop_time REAL DEFAULT NULL,
                audit_config BLOB NOT NULL,
                audit_scope BLOB DEFAULT NULL
            );

            ----------------------------------------------------------
            -- Tables to store the data.
            ----------------------------------------------------------

            CREATE TABLE types (
                rowid INTEGER PRIMARY KEY,
                name STRING UNIQUE NOT NULL
            );

            CREATE TABLE links (
                rowid INTEGER PRIMARY KEY,
                src_id STRING NOT NULL,
                dst_id STRING NOT NULL,
                src_family INTEGER NOT NULL,
                dst_family INTEGER NOT NULL,
                src_type INTEGER NOT NULL,
                dst_type INTEGER NOT NULL,
                FOREIGN KEY(src_type) REFERENCES types(rowid),
                FOREIGN KEY(dst_type) REFERENCES types(rowid),
                UNIQUE (src_id, dst_id) ON CONFLICT IGNORE,
                CHECK (src_id <= dst_id)
            );

            CREATE TABLE data (
                rowid INTEGER PRIMARY KEY,
                identity STRING UNIQUE NOT NULL,
                family INTEGER NOT NULL,
                type INTEGER NOT NULL,
                data BLOB NOT NULL,
                FOREIGN KEY(type) REFERENCES types(rowid)
            );

            ----------------------------------------------------------
            -- Tables to store the plugin history.
            ----------------------------------------------------------

            CREATE TABLE plugin (
                rowid INTEGER PRIMARY KEY,
                name STRING UNIQUE NOT NULL
            );

            CREATE TABLE history (
                rowid INTEGER PRIMARY KEY,
                plugin_id INTEGER NOT NULL,
                identity STRING NOT NULL,
                FOREIGN KEY(plugin_id) REFERENCES plugin(rowid),
                UNIQUE(plugin_id, identity) ON CONFLICT IGNORE
            );

            CREATE TABLE stages (
                rowid INTEGER PRIMARY KEY,
                identity STRING NOT NULL,
                stage INTEGER NOT NULL DEFAULT 0,
                UNIQUE(identity) ON CONFLICT REPLACE
            );

            CREATE TABLE log (
                rowid INTEGER PRIMARY KEY,
                plugin_id INTEGER,
                identity STRING,
                text STRING NOT NULL,
                level INTEGER NOT NULL,
                is_error BOOLEAN NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY(plugin_id) REFERENCES plugin(rowid)
            );

            ----------------------------------------------------------
            -- Tables to store the plugins shared data.
            ----------------------------------------------------------

            CREATE TABLE shared_map (
                rowid INTEGER PRIMARY KEY,
                shared_id STRING NOT NULL,
                key_hash STRING NOT NULL,
                key BLOB NOT NULL,
                value BLOB NOT NULL,
                UNIQUE(shared_id, key_hash) ON CONFLICT REPLACE
            );

            CREATE TABLE shared_heap (
                rowid INTEGER PRIMARY KEY,
                shared_id STRING NOT NULL,
                value_hash STRING NOT NULL,
                value BLOB NOT NULL,
                UNIQUE(shared_id, value_hash) ON CONFLICT IGNORE
            );

            """)

            # Insert the file information.
            self.__cursor.execute(
                "INSERT INTO golismero VALUES (?, ?, NULL, NULL, ?, NULL);",
                (self.SCHEMA_VERSION,
                 self.audit_name,
                 self.encode(audit_config))
            )


    #--------------------------------------------------------------------------
    @transactional
    def __load_data_subtype_cache(self):
        self.__cursor.execute("SELECT name, rowid FROM types;")
        self.__data_subtype_cache = {
            str(k): int(v) for k, v in self.__cursor.fetchall()
        }
        self.__data_subtype_reverse_cache = {
            v: k for k, v in self.__data_subtype_cache.iteritems()
        }


    #--------------------------------------------------------------------------
    @transactional
    def __get_audit_name_from_database(self):
        try:
            self.__cursor.execute("SELECT audit_name FROM golismero LIMIT 1;")
            return self.__cursor.fetchone()[0]
        except Exception:
            pass


    #--------------------------------------------------------------------------
    def __get_or_create_type(self, data_subtype):
        if data_subtype is not None:
            data_subtype = str(data_subtype)
            try:
                return self.__data_subtype_cache[data_subtype]
            except KeyError:
                rowid = self.__create_type(data_subtype)
                self.__data_subtype_cache[data_subtype]  = rowid
                self.__data_subtype_reverse_cache[rowid] = data_subtype
                return rowid


    #--------------------------------------------------------------------------
    def __create_type(self, data_subtype):
        self.__cursor.execute(
            "INSERT INTO types VALUES (NULL, ?)", (data_subtype,))
        return self.__cursor.lastrowid


    #--------------------------------------------------------------------------
    @transactional
    def get_audit_times(self):
        self.__cursor.execute(
            "SELECT start_time, stop_time FROM golismero LIMIT 1;")
        start_time, stop_time = self.__cursor.fetchone()
        return start_time, stop_time


    #--------------------------------------------------------------------------
    @transactional
    def set_audit_times(self, start_time, stop_time):
        self.__cursor.execute(
            "UPDATE golismero SET start_time = ?, stop_time = ?;",
            (start_time, stop_time)
        )


    #--------------------------------------------------------------------------
    @transactional
    def set_audit_start_time(self, start_time):
        self.__cursor.execute(
            "UPDATE golismero SET start_time = ?;",
            (start_time,)
        )


    #--------------------------------------------------------------------------
    @transactional
    def set_audit_stop_time(self, stop_time):
        self.__cursor.execute(
            "UPDATE golismero SET stop_time = ?;",
            (stop_time,)
        )


    #--------------------------------------------------------------------------
    @transactional
    def get_audit_config(self):
        self.__cursor.execute("SELECT audit_config FROM golismero LIMIT 1;")
        row = self.__cursor.fetchone()
        if row and row[0]:
            return self.decode(row[0])


    #--------------------------------------------------------------------------
    @transactional
    def save_audit_config(self, audit_config):
        if audit_config:
            self.__cursor.execute(
                "UPDATE golismero SET audit_config = ?;",
                (self.encode(audit_config),)
            )
        else:
            self.__cursor.execute("UPDATE golismero SET audit_config = NULL;")


    #--------------------------------------------------------------------------
    @transactional
    def get_audit_scope(self):
        self.__cursor.execute("SELECT audit_scope FROM golismero LIMIT 1;")
        row = self.__cursor.fetchone()
        if row and row[0]:
            return self.decode(row[0])


    #--------------------------------------------------------------------------
    @transactional
    def save_audit_scope(self, audit_scope):
        if audit_scope:
            self.__cursor.execute(
                "UPDATE golismero SET audit_scope = ?;",
                (self.encode(audit_scope),)
            )
        else:
            self.__cursor.execute("UPDATE golismero SET audit_scope = NULL;")


    #--------------------------------------------------------------------------
    @transactional
    def add_data(self, data):
        return self.__add_data(data)

    @transactional
    def add_many_data(self, dataset):
        for data in dataset:
            self.__add_data(data)

    def __add_data(self, data):
        if not isinstance(data, Data):
            raise TypeError("Expected Data, got %d instead" % type(data))

        # Merge with old data if it exists.
        old_data = self.__get_data(data.identity)
        is_new = old_data is None
        if not is_new:
            old_data.merge(data)
            data = old_data

        # Serialize the Data object, minus the links dictionary.
        old_linked = data._linked
        try:
            data._linked = None
            encoded_data = self.encode(data)
        finally:
            data._linked = old_linked

        # Store the data.
        data_subtype_id = self.__get_or_create_type(data.data_subtype)
        query  = "INSERT OR REPLACE INTO data VALUES (NULL, ?, ?, ?, ?);"
        values = (
            data.identity,
            data.data_type,
            data_subtype_id,
            encoded_data,
        )
        self.__cursor.execute(query, values)
        del encoded_data

        # Store the links.
        links = data._save_links()
        if not is_new:
            links.difference_update(self.__get_links(data.identity))
        for data_type, data_subtype, identity in links:
            if data.identity <= identity:
                link_id = data.identity + "-" + identity
                values = (data.identity, identity,
                          data.data_type, data_type,
                          data_subtype_id,
                          self.__get_or_create_type(data_subtype),
                )
            else:
                link_id = identity + "-" + data.identity
                values = (identity, data.identity,
                          data_type, data.data_type,
                          self.__get_or_create_type(data_subtype),
                          data_subtype_id,
                )
            self.__cursor.execute(
                "INSERT INTO links VALUES (NULL, ?, ?, ?, ?, ?, ?);",
                values)
            self.__cursor.execute(
                "INSERT INTO stages (identity) VALUES (?);",
                (link_id,))

        # If it's new data, add an entry in the stages history.
        if is_new:
            self.__cursor.execute(
                "INSERT INTO stages (identity) VALUES (?);",
                (data.identity,))

        # Return True if the data is new, False otherwise.
        return is_new


    #--------------------------------------------------------------------------
    @transactional
    def remove_data(self, identity):
        self.__remove_data(identity)

    @transactional
    def remove_many_data(self, identities):
        for identity in identities:
            self.__remove_data(identity)

    def __remove_data(self, identity):
        if "-" in identity:
            left_id, right_id = self.__split_rel_id(identity)
            self.__cursor.execute(
                "DELETE FROM links WHERE src_id = ? AND dst_id = ?;",
                (left_id, right_id)
            )
            self.__cursor.execute(
                "DELETE FROM links WHERE src_id = ? AND dst_id = ?;",
                (right_id, left_id)
            )
        else:
            self.__cursor.execute(
                "DELETE FROM data WHERE identity = ?;",
                (identity,)
            )
            self.__cursor.execute(
                "DELETE FROM links WHERE src_id = ?;",
                (identity,)
            )
            self.__cursor.execute(
                "DELETE FROM links WHERE dst_id = ?;",
                (identity,)
            )
        self.__cursor.execute(
            "DELETE FROM history WHERE identity = ?;",
            (identity,)
        )
        self.__cursor.execute(
            "DELETE FROM stages WHERE identity = ?;",
            (identity,)
        )


    #--------------------------------------------------------------------------
    @transactional
    def has_data_key(self, identity):
        if "-" in identity:
            left_id, right_id = self.__split_rel_id(identity)
            query = "SELECT COUNT(rowid)" \
                    "  FROM links" \
                    " WHERE (src_id = ? AND dst_id = ?)" \
                    "    OR (src_id = ? AND dst_id = ?)" \
                    " LIMIT 1;"
            values = (left_id, right_id, right_id, left_id)
        else:
            query = "SELECT COUNT(rowid)" \
                    "  FROM data" \
                    " WHERE identity = ?" \
                    " LIMIT 1;"
            values = (identity,)
        self.__cursor.execute(query, (identity,))
        return bool(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def get_data(self, identity):
        return self.__get_data(identity)

    @transactional
    def get_many_data(self, identities):
        result = (
            self.__get_data(identity)
            for identity in identities
        )
        return [ data for data in result if data ]

    def __split_rel_id(self, link_id):
        try:
            left_id, right_id = link_id.split("-")
            assert "-" not in left_id
            assert "-" not in right_id
        except Exception:
            raise ValueError("Invalid identity hash: %r" % link_id)
        return left_id, right_id

    def __get_data(self, identity, get_links = True):

        # Check the arguments.
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))

        # If it's a Relationship, get the two linked Data objects.
        if "-" in identity:
            left_id, right_id = self.__split_rel_id(identity)
            query = (
                "SELECT COUNT(rowid) FROM links"
                " WHERE (src_id = ? AND dst_id = ?)"
                "    OR (src_id = ? AND dst_id = ?)"
                " LIMIT 1;"
            )
            values = (left_id, right_id, right_id, left_id)
            self.__cursor.execute(query, values)
            row = self.__cursor.fetchone()
            if row and bool(row[0]):
                instance_l = self.__get_data(left_id, get_links)
                instance_r = self.__get_data(right_id, get_links)
                if instance_l is not None and instance_r is not None:
                    Rel = Relationship(
                        instance_l.__class__, instance_r.__class__)
                    return Rel(instance_l, instance_r)
            return

        # Get the Data object, without the links.
        data = None
        query = "SELECT data FROM data WHERE identity = ? LIMIT 1;"
        self.__cursor.execute(query, (identity,))
        row = self.__cursor.fetchone()
        if row and row[0]:
            data = self.decode(row[0])

            # Get the links if requested.
            links = set()
            if get_links:
                links = self.__get_links(data.identity)

            # Load the links into the Data object.
            data._load_links(links)

        # Return the Data object if found, None otherwise.
        return data

    def __get_links(self, identity):

        # Fetch the forward links.
        values = (identity,)
        query = (
            "SELECT dst_family, dst_type, dst_id FROM links"
            " WHERE src_id = ?;"
        )
        self.__cursor.execute(query, values)
        links = {
            (
                int(data_type),
                self.__data_subtype_reverse_cache[int(data_subtype)],
                str(identity),
            )
            for data_type, data_subtype, identity
            in self.__cursor.fetchall()
        }

        # Fetch the backward links.
        query = (
            "SELECT src_family, src_type, src_id FROM links"
            " WHERE dst_id = ?;"
        )
        self.__cursor.execute(query, values)
        links.update(
            (
                int(data_type),
                self.__data_subtype_reverse_cache[int(data_subtype)],
                str(identity),
            )
            for data_type, data_subtype, identity
            in self.__cursor.fetchall()
        )

        # Return all the links.
        return links


    #--------------------------------------------------------------------------
    @transactional
    def get_data_keys(self, data_type = None, data_subtype = None):

        # Trivial case, get all the keys.
        if data_type is None:
            if data_subtype is None or data_subtype == "data/abstract":
                query  = "SELECT identity FROM data;"
                self.__cursor.execute(query)
                return { str(row[0]) for row in self.__cursor.fetchall() }

            # We have data_subtype but no data_type.
            # Derive the second from the first.
            if data_subtype.startswith("resource/"):
                data_type = Data.TYPE_RESOURCE
            elif data_subtype.startswith("information/"):
                data_type = Data.TYPE_INFORMATION
            elif data_subtype.startswith("vulnerability/"):
                data_type = Data.TYPE_VULNERABILITY
            else:
                raise NotImplementedError(
                    "Unknown data subtype: %r" % data_subtype)

        # If we have data_subtype, validate it.
        if data_subtype is not None:
            if data_type == Data.TYPE_RESOURCE:
                if not data_subtype.startswith("resource/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_RESOURCE"
                        % data_subtype)
            elif data_type == Data.TYPE_INFORMATION:
                if not data_subtype.startswith("information/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_INFORMATION"
                        % data_subtype)
            elif data_type == Data.TYPE_VULNERABILITY:
                if not data_subtype.startswith("vulnerability/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_VULNERABILITY"
                        % data_subtype)
            else:
                raise NotImplementedError(
                    "Unknown data type %r!" % data_type)

        # Get keys filtered by type and subtype.
        if data_subtype is None:
            query  = "SELECT identity FROM data WHERE family = ?;"
            values = (data_type,)
        else:
            query  = "SELECT identity FROM data WHERE type = ?;"
            values = (self.__get_or_create_type(data_subtype),)
        self.__cursor.execute(query, values)
        return { str(row[0]) for row in self.__cursor.fetchall() }


    #--------------------------------------------------------------------------
    @transactional
    def get_data_types(self, identities):
        # TODO: optimize by checking multiple identities in the same query,
        #       but beware of the maximum SQL query length limit.
        #       See: http://www.sqlite.org/limits.html
        result = { self.__get_data_type(identity) for identity in identities }
        try:
            result.remove(None)
        except KeyError:
            pass
        return result

    def __get_data_type(self, identity):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        query = "SELECT family, type FROM data" \
                " WHERE data.identity = ?" \
                " LIMIT 1;"
        values = (identity,)
        self.__cursor.execute(query, values)
        row = self.__cursor.fetchone()
        if row:
            return int(row[0]), self.__data_subtype_reverse_cache[int(row[1])]


    #--------------------------------------------------------------------------
    @transactional
    def get_data_count(self, data_type = None, data_subtype = None):

        # Trivial case, count all the keys.
        if data_type is None:
            if data_subtype is None or data_subtype == "data/abstract":
                self.__cursor.execute("SELECT COUNT(rowid) FROM data;")
                return int(self.__cursor.fetchone()[0])

            # We have data_subtype but no data_type.
            # Derive the second from the first.
            if data_subtype.startswith("resource/"):
                data_type = Data.TYPE_RESOURCE
            elif data_subtype.startswith("information/"):
                data_type = Data.TYPE_INFORMATION
            elif data_subtype.startswith("vulnerability/"):
                data_type = Data.TYPE_VULNERABILITY
            else:
                raise NotImplementedError(
                    "Unknown data subtype: %r" % data_subtype)

        # If we have data_subtype, validate it.
        if data_subtype is not None:
            if data_type == Data.TYPE_RESOURCE:
                if not data_subtype.startswith("resource/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_RESOURCE"
                        % data_subtype)
            elif data_type == Data.TYPE_INFORMATION:
                if not data_subtype.startswith("information/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_INFORMATION"
                        % data_subtype)
            elif data_type == Data.TYPE_VULNERABILITY:
                if not data_subtype.startswith("vulnerability/"):
                    raise ValueError(
                        "Invalid data subtype %r for TYPE_VULNERABILITY"
                        % data_subtype)
            else:
                raise NotImplementedError(
                    "Unknown data type %r!" % data_type)

        # Count keys filtered by type and subtype.
        if data_subtype is None:
            query  = "SELECT COUNT(rowid) FROM data WHERE family = ?;"
            values = (data_type,)
        else:
            query  = "SELECT COUNT(rowid) FROM data WHERE type = ?;"
            values = (self.__get_or_create_type(data_subtype),)
        self.__cursor.execute(query, values)
        return int(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def mark_plugin_finished(self, identity, plugin_id):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        if type(plugin_id) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_id))

        # Fetch the plugin rowid, add it if missing.
        plugin_rowid = self.__get_or_create_plugin_rowid(plugin_id)

        # Mark the data as processed by this plugin.
        self.__cursor.execute(
            "INSERT INTO history VALUES (NULL, ?, ?);",
            (plugin_rowid, identity))

    def __get_or_create_plugin_rowid(self, plugin_id):
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_id,))
        rows = self.__cursor.fetchone()
        if rows:
            plugin_rowid = rows[0]
        else:
            self.__cursor.execute(
                "INSERT INTO plugin VALUES (NULL, ?);",
                (plugin_id,))
            plugin_rowid = self.__cursor.lastrowid
            if plugin_rowid is None:
                self.__cursor.execute(
                    "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
                    (plugin_id,))
                rows = self.__cursor.fetchone()
                plugin_rowid = rows[0]
        return plugin_rowid


    #--------------------------------------------------------------------------
    @transactional
    def mark_stage_finished(self, identity, stage):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        if type(stage) is not int:
            raise TypeError("Expected integer, got %s" % type(stage))
        self.__mark_stage_finished(identity, stage)

    @transactional
    def mark_stage_finished_many(self, identities, stage):
        if type(stage) is not int:
            raise TypeError("Expected integer, got %s" % type(stage))
        for identity in identities:
            if type(identity) is not str:
                raise TypeError("Expected string, got %s" % type(identity))
        for identity in identities:
            self.__mark_stage_finished(identity, stage)

    def __mark_stage_finished(self, identity, stage):

        # Get the previous value of the last completed stage for this data.
        self.__cursor.execute(
            "SELECT stage FROM stages WHERE identity = ? LIMIT 1;",
            (identity,)
            )
        row = self.__cursor.fetchone()
        if row:
            do_insert = True
            prev_stage = int(row[0])
        else:
            do_insert = False
            prev_stage = 0

        # If the new stage is greater than the old one...
        if stage > prev_stage:

            # Update the last completed stage value for this data.
            if do_insert:
                query = "INSERT INTO stages VALUES (NULL, ?, ?);"
                params = (identity, stage)
            else:
                query = "UPDATE stages SET stage = ? WHERE identity = ?;"
                params = (stage, identity)
            self.__cursor.execute(query, params)


    #--------------------------------------------------------------------------
    @transactional
    def clear_stage_mark(self, identity):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        self.__cursor.execute(
            "UPDATE stages SET stage = 0 WHERE identity = ?;", (identity,))


    #--------------------------------------------------------------------------
    @transactional
    def clear_all_stage_marks(self):
        self.__cursor.execute("UPDATE stages SET stage = 0;")


    #--------------------------------------------------------------------------
    @transactional
    def get_past_plugins(self, identity):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        self.__cursor.execute(
            "SELECT plugin.name FROM plugin, history"
            " WHERE history.plugin_id = plugin.rowid AND"
            "       history.identity = ?;",
            (identity,))
        rows = self.__cursor.fetchall()
        if rows:
            return { str(x[0]) for x in rows }
        return set()


    #--------------------------------------------------------------------------
    @transactional
    def clear_plugin_history(self, identity):
        self.__cursor.execute(
            "DELETE FROM history WHERE identity = ?;", (identity,))


    #--------------------------------------------------------------------------
    @transactional
    def clear_all_plugin_history(self):
        self.__cursor.execute("DELETE FROM history;")


    #--------------------------------------------------------------------------
    @transactional
    def get_pending_data(self, stage):
        if type(stage) is not int:
            raise TypeError("Expected integer, got %s" % type(stage))
        self.__cursor.execute(
            "SELECT identity FROM stages WHERE stage < ?;",
            (stage,))
        rows = self.__cursor.fetchall()
        if rows:
            return { str(x[0]) for x in rows }
        return set()


    #--------------------------------------------------------------------------
    @transactional
    def append_log_line(self, text, level,
                         is_error = False,
                        plugin_id = None,
                           ack_id = None,
                        timestamp = None):

        # Sanitize the parameters.
        if not timestamp:
            timestamp = time.time()
        else:
            timestamp = float(timestamp)

        level     = int(level)
        is_error  = bool(is_error)
        if plugin_id is not None and type(plugin_id) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_id))
        if ack_id is not None and type(ack_id) is not str:
            raise TypeError("Expected string, got %s" % type(ack_id))

        # Fetch the plugin rowid, add it if missing.
        if plugin_id is not None:
            plugin_rowid = self.__get_or_create_plugin_rowid(plugin_id)
        else:
            plugin_rowid = None

        # Append the log line.
        try:
            try:
                filtered_text = text.encode("utf-8")
            except UnicodeDecodeError:
                filtered_text = text.decode("latin-1").encode("utf-8")

            self.__cursor.execute(
                "INSERT INTO log VALUES (NULL, ?, ?, ?, ?, ?, ?);",
                (plugin_rowid, ack_id, filtered_text, level, is_error, timestamp))
        except Exception:
            return


    #--------------------------------------------------------------------------
    @transactional
    def get_log_lines(self, from_timestamp = None, to_timestamp = None,
                      filter_by_plugin = None, filter_by_data = None,
                      page_num = None, per_page = None):

        # Build the query.
        query = (
            "SELECT"
            " plugin.name, log.identity, log.text,"
            " log.level, log.is_error, log.timestamp"
            " FROM plugin, log"
            " WHERE plugin.rowid = log.plugin_id"
        )
        params = []
        if filter_by_plugin:
            plugin_rowid = self.__get_or_create_plugin_rowid(filter_by_plugin)
            query += " AND plugin.rowid = ?"
            params.append(plugin_rowid)
        if from_timestamp:
            query += " AND log.timestamp >= ?"
            params.append(from_timestamp)
        if to_timestamp:
            query += " AND log.timestamp <= ?"
            params.append(to_timestamp)
        if filter_by_data:
            query += " AND log.ack_id = ?"
            params.append(filter_by_data)
        query += " ORDER BY log.timestamp"
        if (
            page_num is not None and page_num >= 0 and
            per_page is not None and per_page > 0
        ):
            query += " LIMIT %d, %d" % (page_num * per_page, per_page)
        query += ";"

        # Run the query.
        self.__cursor.execute(query, tuple(params))

        # Return the results.
        return self.__cursor.fetchall()


    #--------------------------------------------------------------------------
    @transactional
    def get_mapped_values(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        return self.__get_mapped_values(shared_id, keys)

    def __get_mapped_values(self, shared_id, keys):
        values = []
        for key in keys:
            self.__cursor.execute(
                "SELECT value FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(key)))
            rows = self.__cursor.fetchone()
            if not rows:
                raise KeyError(key)
            values.append( self.decode( rows[0] ) )
        return tuple(values)


    #--------------------------------------------------------------------------
    @transactional
    def has_all_mapped_keys(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        result = True
        for key in keys:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(key)))
            found = bool( self.__cursor.fetchone()[0] )
            result = result and found
            if not result:
                break
        return result


    #--------------------------------------------------------------------------
    @transactional
    def has_any_mapped_key(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        for key in keys:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(key)))
            found = bool( self.__cursor.fetchone()[0] )
            if found:
                return True
        return False


    #--------------------------------------------------------------------------
    @transactional
    def has_each_mapped_key(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        result = []
        for key in keys:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(key)))
            found = bool( self.__cursor.fetchone()[0] )
            result.append(found)
        return tuple(result)


    #--------------------------------------------------------------------------
    @transactional
    def pop_mapped_values(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        keys = tuple(keys)
        values = self.__get_mapped_values(shared_id, keys)
        self.__delete_mapped_values(shared_id, keys)
        return values


    #--------------------------------------------------------------------------
    @transactional
    def put_mapped_values(self, shared_id, items):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        for key, value in items:
            self.__cursor.execute(
                "INSERT INTO shared_map VALUES (NULL, ?, ?, ?, ?);",
                (shared_id, self.get_hash(key),
                 self.encode(key), self.encode(value)))


    #--------------------------------------------------------------------------
    @transactional
    def swap_mapped_values(self, shared_id, items):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        old_values = []
        for key, value in items:
            self.__cursor.execute(
                "SELECT value FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(key)))
            rows = self.__cursor.fetchone()
            if rows:
                old = self.decode( rows[0] )
            else:
                old = None
            old_values.append(old)
            if old != value:
                self.__cursor.execute(
                    "INSERT INTO shared_map VALUES (NULL, ?, ?, ?, ?);",
                    (shared_id, self.get_hash(key),
                     self.encode(key), self.encode(value)))
        return tuple(old_values)


    #--------------------------------------------------------------------------
    @transactional
    def delete_mapped_values(self, shared_id, keys):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        self.__delete_mapped_values(shared_id, keys)

    def __delete_mapped_values(self, shared_id, keys):
        for key in keys:
            self.__cursor.execute(
                "DELETE FROM shared_map"
                " WHERE shared_id = ? AND key_hash = ?;",
                (shared_id, self.get_hash(key)))


    #--------------------------------------------------------------------------
    @transactional
    def get_mapped_keys(self, shared_id):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        self.__cursor.execute(
            "SELECT key FROM shared_map WHERE shared_id = ?;",
            (shared_id,))
        return { self.decode(row[0]) for row in self.__cursor.fetchall() }


    #--------------------------------------------------------------------------
    @transactional
    def has_all_shared_values(self, shared_id, values):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        result = True
        for value in values:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_heap"
                " WHERE shared_id = ? AND value_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(value)))
            found = bool( self.__cursor.fetchone()[0] )
            result = result and found
            if not result:
                break
        return result


    #--------------------------------------------------------------------------
    @transactional
    def has_any_shared_value(self, shared_id, values):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        for value in values:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_heap"
                " WHERE shared_id = ? AND value_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(value)))
            found = bool( self.__cursor.fetchone()[0] )
            if found:
                return True
        return False


    #--------------------------------------------------------------------------
    @transactional
    def has_each_shared_value(self, shared_id, values):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        result = []
        for value in values:
            self.__cursor.execute(
                "SELECT COUNT(rowid) FROM shared_heap"
                " WHERE shared_id = ? AND value_hash = ? LIMIT 1;",
                (shared_id, self.get_hash(value)))
            found = bool( self.__cursor.fetchone()[0] )
            result.append(found)
        return tuple(result)


    #--------------------------------------------------------------------------
    @transactional
    def pop_shared_values(self, shared_id, maximum):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        result = ()
        if maximum:
            self.__cursor.execute(
                "SELECT rowid, value FROM shared_heap"
                " WHERE shared_id = ?" +
                (" LIMIT %d;" % maximum) if maximum > 0 else ";",
                (shared_id,))
            rows = self.__cursor.fetchall()
            result = tuple(self.decode(value) for _, value in rows)
            for rowid, _ in rows:
                self.__cursor.execute(
                    "DELETE FROM shared_heap"
                    " WHERE shared_id = ? AND rowid = ?;",
                    (shared_id, rowid))
        return result


    #--------------------------------------------------------------------------
    @transactional
    def add_shared_values(self, shared_id, values):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        for value in values:
            self.__cursor.execute(
                "INSERT INTO shared_heap VALUES (NULL, ?, ?, ?);",
                (shared_id, self.get_hash(value), self.encode(value)))


    #--------------------------------------------------------------------------
    @transactional
    def remove_shared_values(self, shared_id, values):
        if type(shared_id) is not str:
            raise TypeError("Expected str, got %s" % type(shared_id))
        for value in values:
            self.__cursor.execute(
                "DELETE FROM shared_heap"
                " WHERE shared_id = ? AND value_hash = ?;",
                (shared_id, self.get_hash(value)))


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
            try:
                self.__db.execute("VACUUM;")
            finally:
                self.__db.close()
        except Exception:
            pass


#------------------------------------------------------------------------------
class AuditDB (BaseAuditDB):
    """
    Stores Data objects in a database.

    The database type is chosen automatically based on the filename.
    """


    #--------------------------------------------------------------------------
    def __new__(cls, audit_config):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """
        ##if (
        ##    audit_config.audit_db and
        ##    audit_config.audit_db.strip().lower().startswith("mongo://")
        ##):
        ##    return AuditMongoDB(audit_config)
        return AuditSQLiteDB(audit_config)


    #--------------------------------------------------------------------------
    @classmethod
    def get_config_from_closed_database(cls, audit_db, audit_name = None):
        if audit_db == ":memory:":
            raise ValueError(
                "Operation not supported for in-memory database!")
        ##if audit_db.strip().lower().startswith("mongo://"):
        ##    return AuditMongoDB.get_config_from_closed_database(
        ##        audit_db, audit_name)
        return AuditSQLiteDB.get_config_from_closed_database(
            audit_db, audit_name)
