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
from ..api.data import Data
from ..api.data.information import Information
from ..api.data.resource import Resource
from ..api.data.vulnerability import Vulnerability
##from ..api.shared import check_value   # FIXME do server-side checks too!
from ..api.text.text_utils import generate_random_string
from ..messaging.codes import MessageCode
from ..managers.rpcmanager import implementor

from os import path

import collections
import md5
import posixpath
import urlparse  # cannot use ParsedURL here!
import warnings

# Lazy imports
sqlite3 = None


#----------------------------------------------------------------------
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

@implementor(MessageCode.MSG_RPC_STATE_ADD)
def rpc_plugin_state_add(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.add_state_variable(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_STATE_REMOVE)
def rpc_plugin_state_remove(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.remove_state_variable(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_STATE_CHECK)
def rpc_plugin_state_check(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.has_state_variable(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_STATE_GET)
def rpc_plugin_state_get(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_state_variable(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_STATE_KEYS)
def rpc_plugin_state_keys(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.auditManager.get_audit(audit_name).database.get_state_variable_names(*args, **kwargs)

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

        :returns: Audit configuration.
        :rtype: AuditConfig

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
    @property
    def connection_url(self):
        """
        :returns: Connection URL for this database.
        :rtype: str
        """
        raise NotImplementedError()


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
        Get the audit start and end times.

        :returns: Audit start time (None if it hasn't started yet)
            and audit end time (None if it hasn't finished yet).
            Times are returned as POSIX timestamps.
        :rtype: tuple(float|None, float|None)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set_audit_start_time(self, start_time):
        """
        Set the audit start time.

        :param start_time: Audit start time (None if it hasn't started yet).
            Time is given as a POSIX timestamp.
        :type start_time: float
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def set_audit_stop_time(self, end_time):
        """
        Set the audit end time.

        :param end_time: Audit end time (None if it hasn't finished yet).
            Time is given as a POSIX timestamp.
        :type end_time: float
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
    def remove_data(self, identity, data_type = None):
        """
        Remove data given its identity hash.

        Optionally restrict the result by data type. Depending on the
        underlying database, this may result in a performance gain.

        :param identity: Identity hash.
        :type identity: str

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int

        :returns: True if the object was removed, False if it didn't exist.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove_many_data(self, identities, data_type = None):
        """
        Remove multiple data objects given their identity hashes.

        Optionally restrict the result by data type. Depending on the
        underlying database, this may result in a performance gain.

        :param identities: Identity hashes.
        :type identities: str

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_data_key(self, identity, data_type = None):
        """
        Check if a data object with the given
        identity hash is present in the database.

        Optionally restrict the result by data type. Depending on the
        underlying database, this may result in a performance gain.

        :param identity: Identity hash.
        :type identity: str

        :returns: True if the object is present, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data(self, identity, data_type = None):
        """
        Get an object given its identity hash.

        Optionally restrict the result by data type. Depending on the
        underlying database, this may result in a performance gain.

        :param identity: Identity hash.
        :type identity: str

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int

        :returns: Data object.
        :rtype: Data | None
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_many_data(self, identities, data_type = None):
        """
        Get multiple objects given their identity hashes.

        Optionally restrict the results by data type. Depending on the
        underlying database, this may result in a performance gain.

        :param identities: Identity hashes.
        :type identities: set(str)

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int

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
        :type data_type: int

        :param data_subtype: Optional data subtype.
        :type data_subtype: int | str

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
        :rtype: set( (int, int | str) )
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_data_count(self, data_type = None, data_subtype = None):
        """
        Count all objects of the requested type,
        optionally filtering by subtype.

        :param data_type: Optional data type. One of the Data.TYPE_* values.
        :type data_type: int

        :param data_subtype: Optional data subtype.
        :type data_subtype: int | str

        :returns: Identity hashes.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def add_state_variable(self, plugin_name, key, value):
        """
        Add a plugin state variable to the database.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param key: Variable name.
        :type key: str

        :param value: Variable value.
        :type value: anything
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def remove_state_variable(self, plugin_name, key):
        """
        Remove a plugin state variable from the database.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param key: Variable name.
        :type key: str
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def has_state_variable(self, plugin_name, key):
        """
        Check if plugin state variable is present in the database.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param key: Variable name.
        :type key: str

        :returns: True if the variable is present, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_state_variable(self, plugin_name, key):
        """
        Get the value of a plugin state variable given its name.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param key: Variable name.
        :type key: str

        :returns: Variable value.
        :rtype: \\*
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def get_state_variable_names(self, plugin_name):
        """
        Get all plugin state variable names in the database.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :returns: Variable names.
        :rtype: set(str)
        """
        raise NotImplementedError("Subclasses MUST implement this method!")


    #--------------------------------------------------------------------------
    def mark_plugin_finished(self, identity, plugin_name):
        """
        Mark the data as having been processed by the plugin.

        :param identity: Identity hash.
        :type identity: str

        :param plugin_name: Plugin name.
        :type plugin_name: str
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

        :returns: Set of plugin names.
        :rtype: set(str)
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
class AuditMemoryDB (BaseAuditDB):
    """
    Stores Audit results in memory.
    """


    #--------------------------------------------------------------------------
    def __init__(self, audit_config):
        super(AuditMemoryDB, self).__init__(audit_config)
        self.__start_time   = None
        self.__end_time     = None
        self.__results      = dict()
        self.__state        = collections.defaultdict(dict)
        self.__history      = collections.defaultdict(set)
        self.__stages       = collections.defaultdict(int)
        self.__shared_maps  = collections.defaultdict(dict)
        self.__shared_heaps = collections.defaultdict(set)


    #--------------------------------------------------------------------------
    def close(self):
        self.__results      = dict()
        self.__state        = collections.defaultdict(dict)
        self.__history      = collections.defaultdict(set)
        self.__stages       = collections.defaultdict(int)
        self.__shared_maps  = collections.defaultdict(dict)
        self.__shared_heaps = collections.defaultdict(set)


    #--------------------------------------------------------------------------
    @property
    def connection_url(self):
        return "memory://"


    #--------------------------------------------------------------------------
    def encode(self, data):
        return data


    #--------------------------------------------------------------------------
    def decode(self, data):
        return data


    #--------------------------------------------------------------------------
    def get_audit_times(self):
        return self.__start_time, self.__end_time


    #--------------------------------------------------------------------------
    def set_audit_start_time(self, start_time):
        self.__start_time = start_time


    #--------------------------------------------------------------------------
    def set_audit_stop_time(self, end_time):
        self.__end_time = end_time


    #--------------------------------------------------------------------------
    def add_data(self, data):
        if not isinstance(data, Data):
            raise TypeError("Expected Data, got %d instead" % type(data))
        identity = data.identity
        if identity in self.__results:
            self.__results[identity].merge(data)
            return False
        self.__results[identity] = data
        return True


    #--------------------------------------------------------------------------
    def add_many_data(self, dataset):
        for data in dataset:
            self.add_data(data)


    #--------------------------------------------------------------------------
    def remove_data(self, identity, data_type = None):
        try:
            if data_type is None or self.__results[identity].data_type == data_type:
                del self.__results[identity]
                return True
        except KeyError:
            pass
        return False


    #--------------------------------------------------------------------------
    def remove_many_data(self, identities, data_type = None):
        for identity in identities:
            self.remove_data(identity, data_type)


    #--------------------------------------------------------------------------
    def has_data_key(self, identity, data_type = None):
        return self.get_data(identity, data_type) is not None


    #--------------------------------------------------------------------------
    def get_data(self, identity, data_type = None):
        data = self.__results.get(identity, None)
        if data_type is not None and data is not None and data.data_type != data_type:
            data = None
        return data


    #----------------------------------------------------------------------
    def get_many_data(self, identities, data_type = None):
        result = ( self.get_data(identity, data_type) for identity in identities )
        return [ data for data in result if data ]


    #--------------------------------------------------------------------------
    def get_data_keys(self, data_type = None, data_subtype = None):

        # Ugly but (hopefully) efficient code follows.

        if data_type is None:
            if data_subtype is not None:
                raise NotImplementedError(
                    "Can't filter by subtype for all types")
            return { identity
                     for identity, data in self.__results.iteritems() }
        if data_subtype is None:
            return { identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type }
        if data_type == Data.TYPE_INFORMATION:
            return { identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.information_type == data_subtype }
        if data_type == Data.TYPE_RESOURCE:
            return { identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.resource_type == data_subtype }
        if data_type == Data.TYPE_VULNERABILITY:
            return { identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.vulnerability_type == data_subtype }
        raise NotImplementedError(
            "Unknown data type: %r" % data_type)


    #--------------------------------------------------------------------------
    def get_data_types(self, identities):
        result = { self.__get_data_type(identity) for identity in identities }
        try:
            result.remove(None)
        except KeyError:
            pass
        return result

    def __get_data_type(self, identity):
        data = self.__results.get(identity, None)
        if data is None:
            return None
        data_type = data.data_type
        if data_type == Data.TYPE_INFORMATION:
            return data_type, data.information_type
        if data_type == Data.TYPE_RESOURCE:
            return data_type, data.resource_type
        if data_type == Data.TYPE_VULNERABILITY:
            return data_type, data.vulnerability_type
        return None


    #--------------------------------------------------------------------------
    def get_data_count(self, data_type = None, data_subtype = None):

        # Ugly but (hopefully) efficient code follows.

        if data_type is None:
            if data_subtype is not None:
                raise NotImplementedError(
                    "Can't filter by subtype for all types")
            return len(self.__results)
        if data_subtype is None:
            return len({ identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type })
        if data_type == Data.TYPE_INFORMATION:
            return len({ identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.information_type == data_subtype })
        if data_type == Data.TYPE_RESOURCE:
            return len({ identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.resource_type == data_subtype })
        if data_type == Data.TYPE_VULNERABILITY:
            return len({ identity
                     for identity, data in self.__results.iteritems()
                     if data.data_type == data_type
                     and data.vulnerability_type == data_subtype })
        raise NotImplementedError(
            "Unknown data type: %r" % data_type)


    #--------------------------------------------------------------------------
    def add_state_variable(self, plugin_name, key, value):
        self.__state[plugin_name][key] = value


    #--------------------------------------------------------------------------
    def remove_state_variable(self, plugin_name, key):
        del self.__state[plugin_name][key]


    #--------------------------------------------------------------------------
    def has_state_variable(self, plugin_name, key):
        return key in self.__state[plugin_name]


    #--------------------------------------------------------------------------
    def get_state_variable(self, plugin_name, key):
        return self.__state[plugin_name][key]


    #--------------------------------------------------------------------------
    def get_state_variable_names(self, plugin_name):
        return set(self.__state[plugin_name].iterkeys())


    #--------------------------------------------------------------------------
    def mark_plugin_finished(self, identity, plugin_name):
        self.__history[identity].add(plugin_name)


    #--------------------------------------------------------------------------
    def mark_stage_finished(self, identity, stage):
        self.__stages[identity] = stage


    #--------------------------------------------------------------------------
    def clear_stage_mark(self, identity):
        try:
            del self.__stages[identity]
        except KeyError:
            pass


    #--------------------------------------------------------------------------
    def clear_all_stage_marks(self):
        self.__stages.clear()


    #--------------------------------------------------------------------------
    def get_past_plugins(self, identity):
        return self.__history[identity]


    #--------------------------------------------------------------------------
    def get_pending_data(self, stage):
        pending = {i for i,n in self.__stages.iteritems() if n < stage}
        missing = set(self.__results.iterkeys())
        missing.difference_update(self.__stages.iterkeys())
        pending.update(missing)
        return pending


    #--------------------------------------------------------------------------
    def get_mapped_values(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        return tuple( d[key] for key in keys )


    #--------------------------------------------------------------------------
    def has_all_mapped_keys(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        return all( key in d for key in keys )


    #--------------------------------------------------------------------------
    def has_any_mapped_key(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        return any( key in d for key in keys )


    #--------------------------------------------------------------------------
    def has_each_mapped_key(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        return tuple( key in d for key in keys )


    #--------------------------------------------------------------------------
    def pop_mapped_values(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        values = tuple(d[key] for key in keys)
        for key in keys:
            del d[key]
        return values


    #--------------------------------------------------------------------------
    def put_mapped_values(self, shared_id, items):
        self.__shared_maps[shared_id].update(items)


    #--------------------------------------------------------------------------
    def swap_mapped_values(self, shared_id, items):
        d = self.__shared_maps[shared_id]
        old = []
        for key, value in items:
            old.append( d.get(key, None) )
            d[key] = value
        return tuple(old)


    #--------------------------------------------------------------------------
    def delete_mapped_values(self, shared_id, keys):
        d = self.__shared_maps[shared_id]
        for key in keys:
            try:
                del d[key]
            except KeyError:
                pass


    #--------------------------------------------------------------------------
    def get_mapped_keys(self, shared_id):
        return set( self.__shared_maps[shared_id].iterkeys() )


    #--------------------------------------------------------------------------
    def has_all_shared_values(self, shared_id, values):
        d = self.__shared_heaps[shared_id]
        return all(value in d for value in values)


    #--------------------------------------------------------------------------
    def has_any_shared_value(self, shared_id, values):
        d = self.__shared_heaps[shared_id]
        return any(value in d for value in values)


    #--------------------------------------------------------------------------
    def has_each_shared_value(self, shared_id, values):
        d = self.__shared_heaps[shared_id]
        return tuple(value in d for value in values)


    #--------------------------------------------------------------------------
    def pop_shared_values(self, shared_id, maximum):
        d = self.__shared_heaps[shared_id]
        result = []
        while maximum != 0:  # don't do > 0, we want -1 to be infinite
            maximum -= 1
            try:
                result.append( d.pop() )
            except KeyError:
                break
        return tuple(result)


    #--------------------------------------------------------------------------
    def add_shared_values(self, shared_id, values):
        self.__shared_heaps[shared_id].update(values)


    #--------------------------------------------------------------------------
    def remove_shared_values(self, shared_id, values):
        self.__shared_heaps[shared_id].difference_update(values)


#------------------------------------------------------------------------------
class AuditSQLiteDB (BaseAuditDB):
    """
    Stores Audit results in a database file using SQLite.
    """

    # The current schema version.
    SCHEMA_VERSION = 1


    #--------------------------------------------------------------------------
    def __init__(self, audit_config):

        # Initialize the busy flag and the database cursor.
        self.__busy   = False
        self.__cursor = None

        # Load the SQLite module.
        global sqlite3
        if sqlite3 is None:
            import sqlite3

        # Get the filename from the connection string.
        filename = self.__parse_connection_string(
            audit_config.audit_db, audit_config.audit_name)

        # See if we have a filename, and an old database file.
        have_file = filename and path.exists(filename)

        # If we have a filename...
        if filename:

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
                audit_config.audit_name = path.splitext(path.basename(filename))[0]

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

            # Create the database file.
            self.__filename = filename
            self.__db = sqlite3.connect(filename)

        # Update the database connection string.
        audit_config.audit_db = self.connection_url

        # Create or validate the database schema.
        # This raises an exception on error.
        self.__create(audit_config)


    #--------------------------------------------------------------------------
    @staticmethod
    def __parse_connection_string(audit_db, audit_name = None):
        """
        :param audit_db: Connection string.
        :type audit_db: str

        :param audit_name: Optional, audit name.
        :type audit_name: str | None

        :returns: Database filename.
        :rtype: str
        """

        # Parse the connection URL.
        parsed = urlparse.urlparse(audit_db)

        # Extract the filename.
        filename = posixpath.join(parsed.netloc, parsed.path)
        if filename.endswith(posixpath.sep):
            filename = filename[:-len(posixpath.sep)]
        if path.sep != posixpath.sep:
            filename.replace(posixpath.sep, path.sep)
        if "%" in filename:
            filename = urlparse.unquote(filename)

        # If we don't have a filename but we have an audit name...
        if not filename and audit_name:

            # Generate the filename from the audit name.
            filename = "".join(
                (c if c in "-_~" or c.isalnum() else "_")
                for c in audit_name
            )
            filename = filename + ".db"

        # Return the filename.
        return filename


    #--------------------------------------------------------------------------
    @classmethod
    def get_config_from_closed_database(cls, audit_db, audit_name = None):

        # Load the SQLite module.
        global sqlite3
        if sqlite3 is None:
            import sqlite3

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
                    cursor.execute("SELECT audit_config FROM golismero LIMIT 1;")
                    row = cursor.fetchone()
                    if not row:
                        raise IOError("Missing data in database!")
                    try:
                        audit_config = cls.decode(row[0])
                    except Exception:
                        raise IOError("Corrupted database!")

                    # Finish the transaction.
                    db.commit()

                    # Return the config.
                    return audit_config

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
    @property
    def connection_url(self):
        return "sqlite://" + self.filename


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
    def __create(self, audit_config):
        """
        Create the database schema if needed.

        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """

        # Check if the schema is already created.
        self.__cursor.execute((
            "SELECT count(*) FROM sqlite_master"
            " WHERE type = 'table' AND name = 'golismero';"))

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

        # If not present...
        else:

            # Create the schema.
            self.__cursor.executescript(
            """

            ----------------------------------------------------------
            -- Table to store the file information.
            -- There must only be one row in it.
            ----------------------------------------------------------

            CREATE TABLE golismero (
                schema_version INTEGER NOT NULL,
                audit_name STRING NOT NULL,
                start_time REAL DEFAULT NULL,
                end_time REAL DEFAULT NULL,
                audit_config BLOB NOT NULL
            );

            ----------------------------------------------------------
            -- Tables to store the data.
            ----------------------------------------------------------

            CREATE TABLE information (
                rowid INTEGER PRIMARY KEY,
                identity STRING UNIQUE NOT NULL,
                type INTEGER NOT NULL,
                data BLOB NOT NULL
            );

            CREATE TABLE resource (
                rowid INTEGER PRIMARY KEY,
                identity STRING UNIQUE NOT NULL,
                type INTEGER NOT NULL,
                data BLOB NOT NULL
            );

            CREATE TABLE vulnerability (
                rowid INTEGER PRIMARY KEY,
                identity STRING UNIQUE NOT NULL,
                type STRING NOT NULL,
                data BLOB NOT NULL
            );

            ----------------------------------------------------------
            -- Tables to store the plugin state and history.
            ----------------------------------------------------------

            CREATE TABLE plugin (
                rowid INTEGER PRIMARY KEY,
                name STRING UNIQUE NOT NULL
            );

            CREATE TABLE state (
                rowid INTEGER PRIMARY KEY,
                plugin_id INTEGER NOT NULL,
                key STRING NOT NULL,
                value BLOB NOT NULL,
                FOREIGN KEY(plugin_id) REFERENCES plugin(rowid),
                UNIQUE(plugin_id, key) ON CONFLICT REPLACE
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
                "INSERT INTO golismero VALUES (?, ?, NULL, NULL, ?);",
                (self.SCHEMA_VERSION,
                 self.audit_name,
                 self.encode(audit_config))
            )


    #--------------------------------------------------------------------------
    @transactional
    def __get_audit_name_from_database(self):
        try:
            self.__cursor.execute("SELECT audit_name FROM golismero LIMIT 1;")
            return self.__cursor.fetchone()[0]
        except Exception:
            pass


    #--------------------------------------------------------------------------
    def __get_data_table_and_type(self, data):
        data_type = data.data_type
        if   data_type == Data.TYPE_INFORMATION:
            table = "information"
            dtype = data.information_type
        elif data_type == Data.TYPE_RESOURCE:
            table = "resource"
            dtype = data.resource_type
        elif data_type == Data.TYPE_VULNERABILITY:
            table = "vulnerability"
            dtype = data.vulnerability_type
        elif data_type == Data.TYPE_UNKNOWN:
            warnings.warn(
                "Received %s object of type TYPE_UNKNOWN" % type(data),
                RuntimeWarning, stacklevel=3)
            if   isinstance(data, Information):
                data.data_type = Data.TYPE_INFORMATION
                table = "information"
                dtype = data.information_type
                if dtype == Information.INFORMATION_UNKNOWN:
                    warnings.warn(
                        "Received %s object of subtype INFORMATION_UNKNOWN" % type(data),
                        RuntimeWarning, stacklevel=3)
            elif isinstance(data, Resource):
                data.data_type = Data.TYPE_RESOURCE
                table = "resource"
                dtype = data.resource_type
                if dtype == Resource.RESOURCE_UNKNOWN:
                    warnings.warn(
                        "Received %s object of subtype RESOURCE_UNKNOWN" % type(data),
                        RuntimeWarning, stacklevel=3)
            elif isinstance(data, Vulnerability):
                data.data_type = Data.TYPE_VULNERABILITY
                table = "vulnerability"
                dtype = data.vulnerability_type
            else:
                raise NotImplementedError(
                    "Unknown data type %r!" % type(data))
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        return table, dtype


    #--------------------------------------------------------------------------
    @transactional
    def get_audit_times(self):
        self.__cursor.execute(
            "SELECT start_time, end_time FROM golismero LIMIT 1;")
        start_time, end_time = self.__cursor.fetchone()
        return start_time, end_time


    #--------------------------------------------------------------------------
    @transactional
    def set_audit_start_time(self, start_time):
        self.__cursor.execute(
            "UPDATE golismero SET start_time = ?;",
            (start_time,)
        )


    #--------------------------------------------------------------------------
    @transactional
    def set_audit_stop_time(self, end_time):
        self.__cursor.execute(
            "UPDATE golismero SET end_time = ?;",
            (end_time,)
        )


    #--------------------------------------------------------------------------
    @transactional
    def add_data(self, data):
        return self.__add_data(data)

    def __add_data(self, data):
        if not isinstance(data, Data):
            raise TypeError("Expected Data, got %d instead" % type(data))
        table, dtype = self.__get_data_table_and_type(data)
        identity = data.identity
        old_data = self.__get_data(identity, data.data_type)
        is_new = old_data is None
        if not is_new:
            old_data.merge(data)
            data = old_data
        query  = "INSERT OR REPLACE INTO %s VALUES (NULL, ?, ?, ?);" % table
        values = (identity, dtype, self.encode(data))
        self.__cursor.execute(query, values)
        if is_new:
            self.__cursor.execute(
                "INSERT INTO stages (identity) VALUES (?);",
                (identity,))
        return is_new


    #--------------------------------------------------------------------------
    @transactional
    def add_many_data(self, dataset):
        for data in dataset:
            self.__add_data(data)


    #--------------------------------------------------------------------------
    @transactional
    def remove_data(self, identity, data_type = None):
        if data_type is None:
            tables = ("information", "resource", "vulnerability")
        elif data_type == Data.TYPE_INFORMATION:
            tables = ("information",)
        elif data_type == Data.TYPE_RESOURCE:
            tables = ("resource",)
        elif data_type == Data.TYPE_VULNERABILITY:
            tables = ("vulnerability",)
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        for table in tables:
            self.__cursor.execute(
                "DELETE FROM %s WHERE identity = ?;" % table,
                (identity,)
            )
            if self.__cursor.rowcount:
                self.__cursor.execute(
                    "DELETE FROM history WHERE identity = ?;",
                    (identity,)
                )
                self.__cursor.execute(
                    "DELETE FROM stages WHERE identity = ?;",
                    (identity,)
                )
                return True
        return False


    #--------------------------------------------------------------------------
    @transactional
    def remove_many_data(self, identities, data_type = None):
        if data_type is None:
            tables = ("information", "resource", "vulnerability")
        elif data_type == Data.TYPE_INFORMATION:
            tables = ("information",)
        elif data_type == Data.TYPE_RESOURCE:
            tables = ("resource",)
        elif data_type == Data.TYPE_VULNERABILITY:
            tables = ("vulnerability",)
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        for table in tables:
            for identity in identities:
                self.__cursor.execute(
                    "DELETE FROM %s WHERE identity = ?;" % table,
                    (identity,)
                )
                if self.__cursor.rowcount:
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
    def has_data_key(self, identity, data_type = None):
        if data_type is None:
            tables = ("information", "resource", "vulnerability")
        elif data_type == Data.TYPE_INFORMATION:
            tables = ("information",)
        elif data_type == Data.TYPE_RESOURCE:
            tables = ("resource",)
        elif data_type == Data.TYPE_VULNERABILITY:
            tables = ("vulnerability",)
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        for table in tables:
            query = "SELECT COUNT(rowid) FROM %s WHERE identity = ? LIMIT 1;" % table
            self.__cursor.execute(query, (identity,))
            row = self.__cursor.fetchone()
            if row[0]:
                return True
        return False


    #--------------------------------------------------------------------------
    @transactional
    def get_data(self, identity, data_type = None):
        return self.__get_data(identity, data_type)

    @transactional
    def get_many_data(self, identities, data_type = None):
        # TODO: optimize by checking multiple identities in the same query,
        #       but beware of the maximum SQL query length limit.
        #       See: http://www.sqlite.org/limits.html
        result = ( self.__get_data(identity, data_type) for identity in identities )
        return [ data for data in result if data ]

    def __get_data(self, identity, data_type = None):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        if data_type is None:
            tables = ("information", "resource", "vulnerability")
        elif data_type == Data.TYPE_INFORMATION:
            tables = ("information",)
        elif data_type == Data.TYPE_RESOURCE:
            tables = ("resource",)
        elif data_type == Data.TYPE_VULNERABILITY:
            tables = ("vulnerability",)
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        for table in tables:
            query = "SELECT data FROM %s WHERE identity = ? LIMIT 1;" % table
            self.__cursor.execute(query, (identity,))
            row = self.__cursor.fetchone()
            if row and row[0]:
                return self.decode(row[0])


    #--------------------------------------------------------------------------
    @transactional
    def get_data_keys(self, data_type = None, data_subtype = None):

        # Get all the keys.
        if data_type is None:
            if data_subtype is not None:
                raise NotImplementedError(
                    "Can't filter by subtype for all types")
            hashes = set()
            for table in ("information", "resource", "vulnerability"):
                query  = "SELECT identity FROM %s;" % table
                self.__cursor.execute(query)
                hashes.update( str(row[0]) for row in self.__cursor.fetchall() )
            return hashes

        # Get keys filtered by type and subtype.
        if   data_type == Data.TYPE_INFORMATION:
            table = "information"
        elif data_type == Data.TYPE_RESOURCE:
            table = "resource"
        elif data_type == Data.TYPE_VULNERABILITY:
            table = "vulnerability"
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        if data_subtype is None:
            query  = "SELECT identity FROM %s;" % table
            values = ()
        else:
            query  = "SELECT identity FROM %s WHERE type = ?;" % table
            values = (data_subtype,)
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
        for table, data_type, subtype_filter in (
            ("information",   Data.TYPE_INFORMATION,   int),
            ("resource",      Data.TYPE_RESOURCE,      int),
            ("vulnerability", Data.TYPE_VULNERABILITY, str),
        ):
            query  = "SELECT type FROM %s WHERE identity = ? LIMIT 1;" % table
            values = (identity,)
            self.__cursor.execute(query, values)
            row = self.__cursor.fetchone()
            if row:
                return data_type, subtype_filter(row[0])


    #--------------------------------------------------------------------------
    @transactional
    def get_data_count(self, data_type = None, data_subtype = None):

        # Count all the keys.
        if data_type is None:
            if data_subtype is not None:
                raise NotImplementedError(
                    "Can't filter by subtype for all types")
            count = 0
            for table in ("information", "resource", "vulnerability"):
                self.__cursor.execute("SELECT COUNT(rowid) FROM %s;" % table)
                count += int(self.__cursor.fetchone()[0])
            return count

        # Count keys filtered by type and subtype.
        if   data_type == Data.TYPE_INFORMATION:
            table = "information"
        elif data_type == Data.TYPE_RESOURCE:
            table = "resource"
        elif data_type == Data.TYPE_VULNERABILITY:
            table = "vulnerability"
        else:
            raise NotImplementedError(
                "Unknown data type %r!" % data_type)
        if data_subtype is None:
            query  = "SELECT COUNT(rowid) FROM %s;" % table
            values = ()
        else:
            query  = "SELECT COUNT(rowid) FROM %s WHERE type = ?;" % table
            values = (data_subtype,)
        self.__cursor.execute(query, values)
        return int(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def add_state_variable(self, plugin_name, key, value):
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))
        if type(key) is not str:
            raise TypeError("Expected string, got %s" % type(key))

        # Fetch the plugin rowid, add it if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        if rows:
            plugin_id = rows[0]
        else:
            self.__cursor.execute(
                "INSERT INTO plugin VALUES (NULL, ?);",
                (plugin_name,))
            plugin_id = self.__cursor.lastrowid
            if plugin_id is None:
                self.__cursor.execute(
                    "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
                    (plugin_name,))
                rows = self.__cursor.fetchone()
                plugin_id = rows[0]

        # Save the state variable.
        self.__cursor.execute(
            "INSERT INTO state VALUES (NULL, ?, ?, ?);",
            (plugin_id, key, self.encode(value)))


    #--------------------------------------------------------------------------
    @transactional
    def remove_state_variable(self, plugin_name, key):
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))
        if type(key) is not str:
            raise TypeError("Expected string, got %s" % type(key))

        # Fetch the plugin rowid, fail if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        plugin_id = rows[0]

        # Delete the state variable.
        self.__cursor.execute(
            "DELETE FROM state WHERE plugin_id = ? AND key = ?;",
            (plugin_id, key))


    #--------------------------------------------------------------------------
    @transactional
    def has_state_variable(self, plugin_name, key):
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))
        if type(key) is not str:
            raise TypeError("Expected string, got %s" % type(key))

        # Fetch the plugin rowid, return False if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        if not rows:
            return False
        plugin_id = rows[0]

        # Check if the state variable is defined.
        self.__cursor.execute(
            "SELECT COUNT(rowid) FROM state"
            " WHERE plugin_id = ? AND key = ? LIMIT 1",
            (plugin_id, key))
        return bool(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def get_state_variable(self, plugin_name, key):
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))
        if type(key) is not str:
            raise TypeError("Expected string, got %s" % type(key))

        # Fetch the plugin rowid, fail if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        plugin_id = rows[0]

        # Get the state variable value, fail if missing.
        self.__cursor.execute(
            "SELECT value FROM state"
            " WHERE plugin_id = ? AND key = ? LIMIT 1;",
            (plugin_id, key))
        return self.decode(self.__cursor.fetchone()[0])


    #--------------------------------------------------------------------------
    @transactional
    def get_state_variable_names(self, plugin_name):
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))

        # Fetch the plugin rowid, return an empty set if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        if not rows:
            return set()
        plugin_id = rows[0]

        # Get the state variable names.
        self.__cursor.execute(
            "SELECT key FROM state WHERE plugin_id = ?;",
            (plugin_id,))
        return {str(row[0]) for row in self.__cursor.fetchall()}


    #--------------------------------------------------------------------------
    @transactional
    def mark_plugin_finished(self, identity, plugin_name):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        if type(plugin_name) is not str:
            raise TypeError("Expected string, got %s" % type(plugin_name))

        # Fetch the plugin rowid, add it if missing.
        self.__cursor.execute(
            "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
            (plugin_name,))
        rows = self.__cursor.fetchone()
        if rows:
            plugin_id = rows[0]
        else:
            self.__cursor.execute(
                "INSERT INTO plugin VALUES (NULL, ?);",
                (plugin_name,))
            plugin_id = self.__cursor.lastrowid
            if plugin_id is None:
                self.__cursor.execute(
                    "SELECT rowid FROM plugin WHERE name = ? LIMIT 1;",
                    (plugin_name,))
                rows = self.__cursor.fetchone()
                plugin_id = rows[0]

        # Mark the data as processed by this plugin.
        self.__cursor.execute(
            "INSERT INTO history VALUES (NULL, ?, ?);",
            (plugin_id, identity))


    #--------------------------------------------------------------------------
    @transactional
    def mark_stage_finished(self, identity, stage):
        if type(identity) is not str:
            raise TypeError("Expected string, got %s" % type(identity))
        if type(stage) is not int:
            raise TypeError("Expected integer, got %s" % type(stage))

        # Get the previous value of the last completed stage for this data.
        self.__cursor.execute(
            "SELECT stage FROM stages WHERE identity = ? LIMIT 1;",
            (identity,)
            )
        row = self.__cursor.fetchone()
        if row:
            prev_stage = int(row[0])
        else:
            prev_stage = 0

        # If the new stage is greater than the old one...
        if stage > prev_stage:

            # Update the last completed stage value for this data.
            self.__cursor.execute(
                "INSERT INTO stages VALUES (NULL, ?, ?);",
                (identity, stage))


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

    The database type is chosen automatically based on the connection string.
    """

    # Map of URL schemes to AuditDB classes.
    __classmap = {
        "memory": AuditMemoryDB,
        "sqlite": AuditSQLiteDB,
    }


    #--------------------------------------------------------------------------
    def __new__(cls, audit_config):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """
        parsed = urlparse.urlparse(audit_config.audit_db)
        scheme = parsed.scheme.lower()
        try:
            clazz = cls.__classmap[scheme]
        except KeyError:
            raise ValueError("Unsupported database type: %r" % scheme)
        return clazz(audit_config)


    #--------------------------------------------------------------------------
    @classmethod
    def get_config_from_closed_database(cls, audit_db, audit_name = None):
        parsed = urlparse.urlparse(audit_db)
        scheme = parsed.scheme.lower()
        try:
            clazz = cls.__classmap[scheme]
        except KeyError:
            raise ValueError("Unsupported database type: %r" % scheme)
        return clazz.get_config_from_closed_database(audit_db, audit_name)
