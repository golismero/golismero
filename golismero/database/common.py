#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Common abstract classes and utility functions for all databases.
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

__all__ = ["BaseDB", "atomic", "transactional"]

from ..common import pickle, decorator

import zlib


#------------------------------------------------------------------------------
@decorator
def atomic(fn, self, *args, **kwargs):
    """
    Atomic method.
    """
    return self._atom(fn, args, kwargs)


#------------------------------------------------------------------------------
@decorator
def transactional(fn, self, *args, **kwargs):
    """
    Transactional method.
    """
    return self._transaction(fn, args, kwargs)


#------------------------------------------------------------------------------
class BaseDB (object):
    """
    Base class with common functionality for all database classes.
    """

    def __enter__(self):
        return self

    def __exit__(self, etype, value, tb):
        self.close()


    #--------------------------------------------------------------------------
    def _atom(self, fn, args, kwargs):
        """
        Execute an atomic operation.

        Called automatically when using the @atomic decorator.

        :param fn: Method in this class marked as @atomic.
        :type fn: unbound method

        :param args: Positional arguments.
        :type args: tuple

        :param kwargs: Keyword arguments.
        :type kwargs: dict

        :returns: The return value after calling the 'fn' method.
        :raises: NotImplementedError -- Transactions not supported
        """
        raise NotImplementedError("Atomic operations not supported")


    #--------------------------------------------------------------------------
    def _transaction(self, fn, args, kwargs):
        """
        Execute a transactional operation.

        Called automatically when using the @transactional decorator.

        :param fn: Method in this class marked as @transactional.
        :type fn: unbound method

        :param args: Positional arguments.
        :type args: tuple

        :param kwargs: Keyword arguments.
        :type kwargs: dict

        :returns: The return value after calling the 'fn' method.
        :raises: NotImplementedError -- Transactions not supported
        """
        raise NotImplementedError("Transactions not supported")


    #--------------------------------------------------------------------------
    @staticmethod
    def encode(data):
        """
        Encode data for storage.

        :param data: Data to encode.

        :returns: str -- Encoded data.
        """
        data = pickle.dumps(data, -1)
        data = zlib.compress(data, 9)
        return data


    #--------------------------------------------------------------------------
    @staticmethod
    def decode(data):
        """
        Decode data from storage.

        :param data: Data to decode.
        :type data: str

        :returns: Decoded data.
        """
        data = zlib.decompress(data)
        data = pickle.loads(data)
        return data


    #--------------------------------------------------------------------------
    def compact(self):
        """
        Free unused disk space.

        This method does nothing when the underlying
        database doesn't support this operation.
        """
        return


    #--------------------------------------------------------------------------
    def dump(self, filename):
        """
        Dump the database contents to a file.

        :param filename: Output filename.
        :type filename: str

        :raises: NotImplementedError -- Operation not supported
        """
        raise NotImplementedError("Operation not supported")


    #--------------------------------------------------------------------------
    def close(self):
        """
        Free all resources associated with this database.

        This instance may no longer be used after calling this method.
        """
        raise NotImplementedError("Subclasses MUST implement this method!")
