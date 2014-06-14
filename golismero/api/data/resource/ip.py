#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
IP address.
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

__all__ = ["IP"]

from . import Resource
from .. import identity
from .. import Config
from ...text.text_utils import to_utf8

from netaddr import IPAddress


#------------------------------------------------------------------------------
class IP(Resource):
    """
    IP address.
    """


    #--------------------------------------------------------------------------
    def __init__(self, address):
        """
        :param address: IP address.
        :type address: str
        """

        address = to_utf8(address)
        if not isinstance(address, str):
            raise TypeError("Expected str, got %r instead" % type(address))

        try:
            if address.startswith("[") and address.endswith("]"):
                parsed  = IPAddress(address[1:-1], version=6)
                address = address[1:-1]
            else:
                parsed  = IPAddress(address)
            version = int( parsed.version )
        except Exception:
            raise ValueError("Invalid IP address: %s" % address)

        # IP address and protocol version.
        self.__address = address
        self.__version = version

        # Parent constructor.
        super(IP, self).__init__()

        # Reset the crawling depth.
        self.depth = 0


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.address


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<IPv%s address=%r>" % (self.version, self.address)


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "IP Address"


    #--------------------------------------------------------------------------
    @identity
    def address(self):
        """
        :return: IP address.
        :rtype: str
        """
        return self.__address


    #--------------------------------------------------------------------------
    @property
    def version(self):
        """
        :return: version of IP protocol: 4 or 6.
        :rtype: int(4|6)
        """
        return self.__version


    #--------------------------------------------------------------------------
    def is_in_scope(self, scope = None):
        if scope is None:
            scope = Config.audit_scope
        return self.address in scope
