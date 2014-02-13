#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MAC address.
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

__all__ = ["MAC"]

from . import Resource
from .. import identity
from ...text.text_utils import to_utf8

import re


#------------------------------------------------------------------------------
class MAC(Resource):
    """
    MAC address.
    """

    resource_type = Resource.RESOURCE_MAC

    # TODO add a database of MAC address prefixes and manufacturers,
    #      that way we can autodiscover BSSIDs from MACs


    #--------------------------------------------------------------------------
    # Regular expression to match MAC addresses.
    __re_mac = re.compile(
        r"[0-9A-Fa-f][0-9A-Fa-f]"
        r"[ \:\-\.]?"
        r"[0-9A-Fa-f][0-9A-Fa-f]"
        r"[ \:\-\.]?"
        r"[0-9A-Fa-f][0-9A-Fa-f]"
        r"[ \:\-\.]?"
        r"[0-9A-Fa-f][0-9A-Fa-f]"
        r"[ \:\-\.]?"
        r"[0-9A-Fa-f][0-9A-Fa-f]"
        r"[ \:\-\.]?"
        r"[0-9A-Fa-f][0-9A-Fa-f]"
    )


    #--------------------------------------------------------------------------
    def __init__(self, address):
        """
        :param address: MAC address.
        :type address: str
        """

        # Validate and normalize the address.
        address = to_utf8(address)
        if not isinstance(address, str):
            raise TypeError("Expected str, got %r instead" % type(address))
        if not self.__re_mac.match(address):
            raise ValueError("Invalid %s: %r" % (self.display_name, address))
        address = re.sub(r"[^0-9A-Fa-f]", "", address)
        if not len(address) == 12:
            raise ValueError("Invalid %s: %r" % (self.display_name, address))
        address = ":".join(
            address[i:i+2]
            for i in xrange(0, len(address) - 2, 2)
        )

        # Save the address.
        self.__address = address

        # Parent constructor.
        super(MAC, self).__init__()

        # Reset the crawling depth.
        self.depth = 0


    #--------------------------------------------------------------------------
    @classmethod
    def search(cls, text):
        """
        Extract MAC addresses from text input.
        You can pass each one of them to the constructor of this class.

        :param text: Text to scan.
        :type text: str

        :returns: MAC addresses found.
        :rtype: list(str)
        """
        return cls.__re_mac.findall(text)


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.address


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<MAC address=%r>" % self.address


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "MAC Address"


    #--------------------------------------------------------------------------
    @identity
    def address(self):
        """
        :return: MAC address.
        :rtype: str
        """
        return self.__address
