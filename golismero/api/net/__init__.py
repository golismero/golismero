#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Network protocols API.
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

__all__ = ["NetworkException", "NetworkOutOfScope", "ConnectionSlot", "slot"]

from ..config import Config
from ...messaging.codes import MessageCode


#------------------------------------------------------------------------------
class NetworkException(Exception):
    """
    Network connection errors.
    """
    pass


#------------------------------------------------------------------------------
class NetworkOutOfScope(NetworkException):
    """
    Resource is out of audit scope.
    """
    pass


#------------------------------------------------------------------------------
class ConnectionSlot (object):
    """
    Connection slot context manager.
    """

    def __init__(self, hostname, number = 1):
        """
        .. warning: Currently requesting more than one slot is not supported.
            There's a good reason for this, so don't try using this class
            multiple times to work around the limitation!

        :param hostname: Hostname to connect to.
        :type hostname: str

        :param number: Number of slots to request per call.
        :type number: int
        """
        self.__host   = hostname
        self.__number = number

    @property
    def hostname(self):
        """
        :returns: Hostname to connect to.
        :rtype: str
        """
        return self.__host

    @property
    def number(self):
        """
        :returns: Number of slots to request per call.
        :rtype: int
        """
        return self.__number

    def __enter__(self):
        self.__token = Config._context.remote_call(
            MessageCode.MSG_RPC_REQUEST_SLOT, self.hostname, self.number
        )
        if not self.__token:
            # XXX FIXME
            # This should block, not throw an error...
            raise IOError("Connection slots limit exceeded")

    def __exit__(self, type, value, tb):
        Config._context.remote_call(
            MessageCode.MSG_RPC_RELEASE_SLOT, self.__token
        )


#------------------------------------------------------------------------------
def slot(fn, number = 1):
    """
    Decorator for methods and functions
    that request a network slot when called.

    .. warning: Currently requesting more than one slot is not supported.
        There's a good reason for this, so don't try using this decorator
        multiple times to work around the limitation!

    :param fn: Method or function to decorate.
    :type fn: callable

    :param number: Number of slots to request per call.
    :type number: int
    """
    def method(hostname, *args, **kwargs):
        with ConnectionSlot(hostname, number):
            return fn(hostname, *args, **kwargs)
    return method
