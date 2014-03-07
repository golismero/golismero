#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wi-Fi BSSID.
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

__all__ = ["BSSID"]

from . import Resource
from .mac import MAC
from .. import merge
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class BSSID(MAC):
    """
    Wi-Fi BSSID (MAC address of a wireless router).
    """


    #--------------------------------------------------------------------------
    def __init__(self, bssid, essid = None):
        """
        :param bssid: BSSID.
        :type bssid: str

        :param essid: (Optional) ESSID.
        :type essid: str | None
        """

        # Parent constructor.
        super(BSSID, self).__init__(bssid)

        # Save the ESSID.
        self.essid = essid

        # Reset the crawling depth.
        self.depth = 0


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<BSSID %s>" % self.bssid


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Wi-Fi 802.11 BSSID"


    #--------------------------------------------------------------------------
    @property
    def bssid(self):
        """
        :return: BSSID.
        :rtype: str
        """
        return self.address


    #--------------------------------------------------------------------------
    @merge
    def essid(self):
        """
        :return: ESSID.
        :rtype: str | None
        """
        return self.__essid


    #--------------------------------------------------------------------------
    @essid.setter
    def essid(self, essid):
        """
        :param essid: ESSID.
        :type essid: str
        """
        essid = to_utf8(essid)
        if not isinstance(essid, basestring):
            raise TypeError("Expected string, got %r instead" % type(essid))
        self.__essid = essid


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        return [ MAC(self.bssid) ]
