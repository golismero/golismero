#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared data containers for plugins.

.. note: Important note: while these data containers may somewhat look like
         Python's dictionaries and sets, they are not the same thing. Most
         importantly, the dict() and set() types use equality comparisons to
         determine if two keys or two values are the same, so:

         >>> set([False, 0, 0L, 0.0, complex(0, 0), "", u""])
         set([False, ''])

         This happens because many of those objects, when compared to each
         other, are evaluated as equal.

         Howerver, in our data containers all of them are considered different!

         >>> h = SharedHeap()
         >>> h.add(False)
         >>> h.add(0)
         >>> h.add(0L)
         >>> h.add(0.0)
         >>> h.add(complex(0, 0))
         >>> h.add("")
         >>> h.add(u"")
         >>> sorted(h.pop_many(7), key=str)
         ['', u'', 0, 0L, 0.0, 0j, False]

         Same thing happens with the dictionaries:

         >>> { True: 0, 1: 1, 1.0: 2, complex(1,0): 3, "test": 4, u"test": 5 }
         {'test': 5, True: 3}

         In our shared maps, again, all of them are different:

         >>> m = SharedMap()
         >>> m[True] = 0
         >>> m[1] = 1
         >>> m[1.0] = 2
         >>> m[complex(1,0)] = 3
         >>> m["test"] = 4
         >>> m[u"test"] = 5
         >>> sorted(m.keys(), key=str)
         [(1+0j), 1, 1.0, True, 'test', u'test']

         Also, the built-in dict() and set() type support different data types
         than our containers. Most importantly, our containers can be nested
         however you like:

         >>> h = SharedHeap()
         >>> m = SharedMap()
         >>> m[s] = m
         >>> m[m] = s
         >>> s.add(m)
         >>> s.add(s)
         >>> m["string"] = object()
         >>> m[object()] = "string"
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: Type 'object' cannot be used in shared data containers
         >>> s.add("string")
         >>> s.add(object())
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: Type 'object' cannot be used in shared data containers

         On the other hand, dict() and set() cannot be nested arbitrarily:

         >>> a = {}
         >>> b = set()
         >>> a[b] = b
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: unhashable type: 'set'
         >>> a[a] = a
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: unhashable type: 'dict'
         >>> b.add(a)
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: unhashable type: 'dict'
         >>> b.add(b)
         Traceback (most recent call last):
           File "<stdin>", line 1, in <module>
         TypeError: unhashable type: 'set'
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

__all__ = ["SharedMap", "SharedHeap"]

from .config import Config
from ..common import pickle
from ..messaging.codes import MessageCode

from uuid import uuid4


# Sentinel value.
_sentinel = object()


#------------------------------------------------------------------------------
def check_value(obj):
    """
    Check if the given object can be used in a shared data container.

    Immutable, hashable built-in types can be used as keys and values.
    Shared data containers can also be used. Any other data type is forbidden.

    :param obj: Object to test.
    :type obj: \\*

    :raises TypeError: An invalid data type was found.
    """

    # This function checks for infinite loops, because it's technically
    # possible to have self-referencing tuples. Yeah, it's crazy, I know.
    # See: http://stackoverflow.com/questions/11873448/

    # Copy these globals to the local namespace (optimization).
    valid_objects     = _valid_objects
    valid_scalars     = _valid_scalars
    valid_containers  = _valid_containers
    shared_containers = _shared_containers

    # Visitor for the target object, checking for infinite recursion.
    stack   = [obj]
    visited = set()
    while stack:
        obj = stack.pop()
        obj_id = id(obj)  # faster + works for non hashable types
        if obj_id in visited:
            continue
        visited.add(obj_id)
        typ = type(obj)

        # Recursive case for immutable containers.
        if any(typ is x for x in valid_containers):
            stack.extend(obj)
            continue

        # Reject invalid types.
        if (all(obj is not x for x in valid_objects)     and
            all(typ is not x for x in valid_scalars)     and
            all(typ is not x for x in shared_containers)
        ):
            t = repr(typ)
            if t.startswith("<type '") and t.endswith("'>"):
                t = "'%s'" % t[7:-2]
            raise TypeError(
            "Type %s cannot be used in shared data containers" % t)


#------------------------------------------------------------------------------
def encode_key(obj):
    """
    Encode the given object to be used as a key in a shared data container.

    Immutable, hashable built-in types can be used as keys and values.
    Shared data containers can also be used. Any other data type is forbidden.

    :param obj: Object to encode.
    :type obj: \\*

    :returns: Encoded object stream.
    :rtype: str

    :raises TypeError: An invalid data type was found.
    """

    # Check the data type.
    check_value(obj)

    # Pickle the object using the compatibility protocol,
    # because it ensures the same output for the same input.
    return pickle.dumps(obj, protocol = 0)


#------------------------------------------------------------------------------
def decode_key(data):
    """
    Decode the given object to be used in a shared data container.

    Immutable, hashable built-in types can be used as keys and values.
    Shared data containers can also be used. Any other data type is forbidden.

    :param data: Encoded object stream.
    :type data: str

    :returns: Decoded object.
    :rtype: \\*
    """

    # Unpickle the object.
    return pickle.loads(data)


#------------------------------------------------------------------------------
class AbstractSharedContainer (object):
    """
    Base class for shared data containers.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        self._shared_id = str( uuid4() )


    #--------------------------------------------------------------------------
    @property
    def shared_id(self):
        """
        :returns: Global unique ID of this shared data container.
        :rtype: str
        """
        return self._shared_id


#------------------------------------------------------------------------------
class SharedMap (AbstractSharedContainer):
    """
    Shared data container that can map string keys to arbitrary values.
    Said values can only be of immutable types, or other shared containers.
    """


    #--------------------------------------------------------------------------
    def get(self, key, default = _sentinel):
        """
        Get the value for a given key.

        :param key: Key to look for.
        :type key: immutable

        :param default: Optional default value. If set, when the name
                        is not found the default is returned instead
                        of raising KeyError.
        :type default: immutable

        :returns: Value mapped to the requested key.
        :rtype: immutable

        :raises KeyError: The key was not mapped.
        """
        if default is not _sentinel:
            check_value(default)
        try:
            return self.get_many( (key,) ) [0]
        except KeyError:
            if default is not _sentinel:
                return default
            raise


    #--------------------------------------------------------------------------
    def get_many(self, keys):
        """
        Get the values for the given keys.

        :param key: Keys to look for.
        :type key: tuple( immutable, ... )

        :returns: Values mapped to the requested keys, in the same order.
        :rtype: tuple( immutable, ... )

        :raises KeyError: Not all keys were mapped.
        """
        keys = [encode_key(k) for k in keys]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_GET, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def check(self, key):
        """
        Check if the given key has been defined.

        .. warning: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

            Therefore this pattern is NOT recommended:
                myvar = None
                if "myvar" in mysharedmap:
                    myvar = mysharedmap["myvar"]

            You should do this instead:
                try:
                    myvar = mysharedmap["myvar"]
                except KeyError:
                    myvar = None

        :param key: Key to look for.
        :type key: immutable

        :returns: True if the key was defined, False otherwise.
        :rtype: bool
        """
        return self.check_all( (key,) )


    #--------------------------------------------------------------------------
    def check_all(self, keys):
        """
        Check if all of the given keys has been defined.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: True if all keys were defined, False otherwise.
        :rtype: bool
        """
        keys = [encode_key(k) for k in keys]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_CHECK_ALL, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def check_any(self, keys):
        """
        Check if any of the given keys has been defined.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: True if any of the keys was defined, False otherwise.
        :rtype: bool
        """
        keys = [encode_key(k) for k in keys]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_CHECK_ANY, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def check_each(self, keys):
        """
        Check if each of the given keys has been defined.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param keys: Keys to look for.
        :type keys: tuple( immutable, ... )

        :returns: Tuple with the results, in the same order, for each key.
            True for each defined key, False for each undefined key.
        :rtype: tuple( bool, ... )
        """
        keys = [encode_key(k) for k in keys]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_CHECK_EACH, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def pop(self, key, default = _sentinel):
        """
        Get the value for a given key and remove it from the map.

        :param key: Key to look for.
        :type key: immutable

        :param default: Optional default value. If set, when the name
                        is not found the default is returned instead
                        of raising KeyError.
        :type default: immutable

        :returns: Value mapped to the requested key.
        :rtype: immutable

        :raises KeyError: The key was not mapped.
        """
        try:
            return self.pop_many( (key,) ) [0]
        except KeyError:
            if default is not _sentinel:
                return default
            raise


    #--------------------------------------------------------------------------
    def pop_many(self, keys):
        """
        Get the values for the given keys and remove them from the map.

        :param keys: Keys to look for.
        :type keys: tuple(immutable, ...)

        :returns: Values mapped to the requested keys, in the same order.
        :rtype: tuple(immutable, ...)

        :raises KeyError: Not all keys were mapped.
        """
        keys = [encode_key(k) for k in keys]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_POP, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def put(self, key, value):
        """
        Map the given key to the given value, and return the previous value.
        If you don't care for the previous value, try async_put() instead.

        :param key: Key to map.
        :type key: immutable

        :param value: Value to map.
        :type value: immutable

        :returns: Previous mapped value, if any. None otherwise.
        :rtype: immutable | None
        """
        return self.put_many( ( (key, value), ) ) [0]


    #--------------------------------------------------------------------------
    def async_put(self, key, value):
        """
        Map the given key to the given value.
        Unlike put() this method is asynchronous and has no return value.

        :param key: Key to map.
        :type key: immutable

        :param value: Value to map.
        :type value: immutable
        """
        self.async_put_many( (key, value) )


    #--------------------------------------------------------------------------
    def put_many(self, items):
        """
        Map the given keys to the given values, and return the previous values.
        If you don't care for the previous values, try async_put_many()
        instead.

        :param items: Keys and values to map, in (key, value) tuples.
        :type items: tuple( tuple(immutable, immutable), ... )

        :returns: Previous mapped values, if any, in the same order.
            None for each missing key.
        :rtype: tuple( immutable | None, ... )
        """
        items = [ (encode_key(k), v) for (k, v) in items ]
        for (k, v) in items:
            check_value(v)
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_SWAP, self.shared_id, items)


    #--------------------------------------------------------------------------
    def async_put_many(self, items):
        """
        Map the given key to the given value. Unlike put_many() this
        method is asynchronous and has no return value.

        :param items: Keys and values to map, in (key, value) tuples.
        :type items: tuple( tuple(immutable, immutable), ... )
        """
        items = [ (encode_key(k), v) for (k, v) in items ]
        for (k, v) in items:
            check_value(v)
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_PUT, self.shared_id, items)


    #--------------------------------------------------------------------------
    def delete(self, key):
        """
        Delete the given key from the map.

        .. note: If the key was not defined, no error is raised.

        :param key: Key to delete.
        :type key: immutable
        """
        self.delete_many( (key,) )


    #--------------------------------------------------------------------------
    def delete_many(self, keys):
        """
        Delete the given keys from the map.

        .. note: If any of the keys was not defined, no error is raised.

        :param keys: Keys to delete.
        :type keys: tuple( immutable, ... )
        """
        keys = [encode_key(k) for k in keys]
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_DELETE, self.shared_id, keys)


    #--------------------------------------------------------------------------
    def keys(self):
        """
        Get the keys of the map.

        .. warning: Due to the asynchronous nature of GoLismero plugins, it's
            possible the list of keys is not accurate - another instance
            of the plugin may remove or add new keys right after you call
            this method.

        :returns: Keys defined in this shared map, in any order.
        :rtype: tuple( immutable, ... )
        """
        keys = Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_MAP_KEYS, self.shared_id)
        return tuple(decode_key(k) for k in keys)


    #--------------------------------------------------------------------------
    # Aliases.

    __getitem__  = get
    __setitem__  = async_put
    __delitem__  = delete
    __contains__ = check


#------------------------------------------------------------------------------
class SharedHeap (AbstractSharedContainer):
    """
    Shared data container that can host arbitrary values without order.
    Said values can only be of immutable types.
    """


    #--------------------------------------------------------------------------
    def check(self, value):
        """
        Check if the given value is present in the container.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param value: Value to look for.
        :type value: immutable

        :returns: True if the value was found, False otherwise.
        :rtype: bool
        """
        return self.check_all( (value,) )


    #--------------------------------------------------------------------------
    def check_all(self, values):
        """
        Check if all of the given values are present in the container.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: True if all of the values were found, False otherwise.
        :rtype: bool
        """
        values = [encode_key(v) for v in values]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_CHECK_ALL, self.shared_id, values)


    #--------------------------------------------------------------------------
    def check_any(self, values):
        """
        Check if any of the given values are present in the container.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: True if any of the values was found, False otherwise.
        :rtype: bool
        """
        values = [encode_key(v) for v in values]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_CHECK_ANY, self.shared_id, values)


    #--------------------------------------------------------------------------
    def check_each(self, values):
        """
        Check if each of the given values is present in the container.

        .. note: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            values right after you call this method.

        :param values: Values to look for.
        :type values: tuple( immutable, ... )

        :returns: Tuple with the results, in the same order, for each value.
            True for each value found, False for each not found.
        :rtype: tuple( bool, ... )
        """
        values = [encode_key(v) for v in values]
        return Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_CHECK_EACH, self.shared_id, values)


    #--------------------------------------------------------------------------
    def pop(self):
        """
        Get a random value from the container and remove it.

        :returns: Value removed from the container.
        :rtype: immutable

        :raises KeyError: The container was empty.
        """
        values = self.pop_many(1)
        if not values:
            raise KeyError("The container was empty")
        return values[0]


    #--------------------------------------------------------------------------
    def pop_many(self, maximum):
        """
        Get multiple random values from the container and remove them.

        :param maximum: Maximum number of values to retrieve.
            This method may return less than this number if there aren't enough
            values in the container.

        :returns: Values removed from the container, in any order.
            If the container was empty, returns an empty tuple.
        :rtype: tuple( immutable, ... )
        """
        maximum = long(maximum)
        if maximum < 1:
            return ()
        values = Config._context.remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_POP, self.shared_id, maximum)
        return tuple(decode_key(v) for v in values)


    #--------------------------------------------------------------------------
    def add(self, value):
        """
        Add the given value to the container.

        :param value: Value to add.
        :type value: immutable
        """
        self.add_many( (value,) )


    #--------------------------------------------------------------------------
    def add_many(self, values):
        """
        Add the given values to the container.

        :param values: Values to add.
        :type values: tuple( immutable, ... )
        """
        values = [encode_key(v) for v in values]
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_ADD, self.shared_id, values)


    #--------------------------------------------------------------------------
    def remove(self, value):
        """
        Remove the given value from the container.

        .. note: If the value was not found, no error is raised.

        :param value: Value to remove.
        :type value: immutable
        """
        self.remove_many( (value,) )


    #--------------------------------------------------------------------------
    def remove_many(self, values):
        """
        Remove the given values from the container.

        .. note: If any of the values was not found, no error is raised.

        :param values: Values to remove.
        :type values: tuple( immutable, ... )
        """
        values = [encode_key(v) for v in values]
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_SHARED_HEAP_REMOVE, self.shared_id, values)


    #--------------------------------------------------------------------------
    # Aliases.

    __contains__      = check
    update            = add_many
    difference_update = remove_many


#------------------------------------------------------------------------------

# Unique built-in immutable hashable objects.
_valid_objects = (None, Ellipsis)

# Built-in immutable hashable scalar types.
_valid_scalars = (bool, int, long, float, str, unicode, complex)

# Built-in immutable hashable container types.
_valid_containers = (tuple, frozenset)

# Shared container types. (Internally they're immutable proxy objects).
_shared_containers = (SharedMap, SharedHeap)
