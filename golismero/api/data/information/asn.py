#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Autonomous System Number (ASN) for BGP routing.
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

__all__ = ["ASN"]

from . import Information
from .. import identity, merge
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class ASN(Information):
    """
    Autonomous System Number (ASN) for BGP routing.
    """

    information_type = Information.INFORMATION_ASN

    AS_FIRST   = 0
    AS_LAST_16 = 65535
    AS_LAST_32 = 4294967295
    AS_TRANS   = 23456

    # TODO: maybe add a property for the AS type?


    #--------------------------------------------------------------------------
    def __init__(self, asn, isp = None):
        """
        :param asn: Autonomous System Number (ASN).
                    Both *asplain* and *asdot* notations are supported.
        :type asn: str | int

        :param isp: (Optional) ISP name.
        :type isp: str
        """

        # Check the data types.
        asn = to_utf8(asn)
        if not isinstance(asn, str):
            try:
                asn = str(int(asn))
            except Exception:
                raise TypeError(
                    "Expected str or int, got %r instead" % type(asn))
        if isp:
            isp = to_utf8(isp)
            if not isinstance(isp, str):
                raise TypeError("Expected str, got %r instead" % type(isp))
        else:
            isp = None

        # Validate the ASN.
        try:
            if "." in asn:
                high, low = map(int, asn.split("."))
                asn = "%d.%d" % (high, low)
                assert 65535 >= high >= 0
                assert 65535 >= low >= 0
                assert ((high << 16) + low) != self.AS_LAST_32
                if high == 0:
                    assert low != self.AS_TRANS
            else:
                only = int(asn)
                assert only >= 0
                if only > 65535:
                    asn = "%d.%d" % (only >> 16, only & 0xFFFF)
                else:
                    asn = "0.%d" % only
                assert only != self.AS_TRANS
                assert only != self.AS_FIRST
                assert only != self.AS_LAST_16
        except Exception:
            raise ValueError("Invalid ASN: %r" % asn)

        # Save the properties.
        self.__asn = asn
        self.__isp = isp

        # Parent constructor.
        super(ASN, self).__init__()


    #--------------------------------------------------------------------------
    def __str__(self):
        if self.isp:
            return "%s (ASN %s)" % (self.isp, self.asn)
        return self.asn


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<ASN asn=%r, isp=%r>" % (self.asn, self.isp)


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Autonomous System Number (ASN)"


    #--------------------------------------------------------------------------
    @identity
    def asn(self):
        """
        :return: Autonomous System Number (ASN), in *asdot* notation.
        :rtype: str
        """
        return self.__asn


    #--------------------------------------------------------------------------
    @merge
    def isp(self):
        """
        :return: ISP name.
        :rtype: str
        """
        return self.__isp


    #--------------------------------------------------------------------------
    @isp.setter
    def isp(self, isp):
        """
        :param isp: ISP name.
        :type isp: str
        """
        if isp:
            isp = to_utf8(isp)
            if not isinstance(isp, str):
                raise TypeError("Expected str, got %r instead" % type(isp))
        else:
            isp = None
        self.__isp = isp


    #--------------------------------------------------------------------------
    @property
    def asdot(self):
        """
        :return: Autonomous System Number (ASN), in *asdot* notation.
        :rtype: str
        """
        return self.asn


    #--------------------------------------------------------------------------
    @property
    def asplain(self):
        """
        :return: Autonomous System Number (ASN), in *asplain* notation.
        :rtype: str
        """
        high, low = map(int, self.asn.split("."))
        return str((high << 16) + low)


    #--------------------------------------------------------------------------
    @property
    def is_private(self):
        """
        :returns: True if the ASN is private, False if it's public.
        :rtype: bool
        """
        high, low = map(int, self.asn.split("."))
        if high == 0:
            return 64512 <= low <= 65534
        return 4200000000 <= ((high << 16) + low) <= 4294967294


    #--------------------------------------------------------------------------
    @property
    def is_public(self):
        """
        :returns: True if the ASN is public, False if it's private.
        :rtype: bool
        """
        return not self.is_private
