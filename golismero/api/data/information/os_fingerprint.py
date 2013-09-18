#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fingerprint information for a particular operating system of a host.
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

__all__ = ["OSFingerprint"]

from . import Information
from .. import identity


#------------------------------------------------------------------------------
class OSFingerprint(Information):
    """
    Fingerprint information for a particular operating system.
    """

    information_type = Information.INFORMATION_OS_FINGERPRINT


    #----------------------------------------------------------------------
    def __init__(self, family, version=None, cpe=None, others = None):
        """
        :param family: OS name, at lowcase. The name will be one of the the file: 'wordlist/fingerprint/os_keywords.txt'. Example: "windows"
        :type family: str

        :param version: OS version. Example: "XP"
        :type version: str

        :param cpe: CPE (Common Platform Enumeration) of the OS. Example: "/o:microsoft:windows_xp"
        :type cpe: str

        :param others: Map of other possible OS by name and their probabilities of being correct [0.0 ~ 1.0].
        :type others: dict( str -> float )
        """

        # Check the data types.
        if not isinstance(family, str):
            raise TypeError("Expected str, got %r instead" % type(family))

        if version:
            if not isinstance(version, str):
                raise TypeError("Expected str, got %r instead" % type(version))

        if cpe is not None:
            if not isinstance(cpe, basestring):
                raise TypeError("Expected str, got '%s' instead" % type(cpe))

        if others is not None:
            if not isinstance(others, dict):
                raise TypeError("Expected dict, got %r instead" % type(others))
            for k, v in others.iteritems():
                if not isinstance(k, str):
                    raise TypeError("Expected str, got %r instead" % type(k))
                if not isinstance(v, float):
                    raise TypeError("Expected float, got %r instead" % type(v))

        # Convert CPE <2.3 (URI binding) to CPE 2.3 (formatted string binding).
        if cpe is not None:
            if not cpe.startswith("cpe:"):
                raise ValueError("Not a CPE name: %r" % cpe)
            if cpe.startswith("cpe:/"):
                cpe_parts = cpe[5:].split(":")
                if len(cpe_parts) < 11:
                    cpe_parts.extend( "*" * (11 - len(cpe_parts)) )
                cpe = "cpe:2.3:" + ":".join(cpe_parts)

        # OS name.
        self.__family         = family

        # OS version.
        self.__version        = version

        # CPE name.
        self.__cpe            = cpe

        # Other possibilities for this OS.
        self.__others         = others

        # Parent constructor.
        super(OSFingerprint, self).__init__()


    #----------------------------------------------------------------------
    def __repr__(self):
        return "<OSFingerprint server='%s-%s' cpe=%r>" % (
            self.__family,
            self.__version,
            self.__cpe,
        )


    #----------------------------------------------------------------------
    def __str__(self):
        s = self.__family
        if self.__version:
            s += " " + self.__version
        if self.__cpe:
            s += " (%s)" % self.__cpe
        return s


    #----------------------------------------------------------------------
    @identity
    def name(self):
        """
        :return: OS name.
        :rtype: str
        """
        return self.__family


    #----------------------------------------------------------------------
    @identity
    def version(self):
        """
        :return: OS version.
        :rtype: str
        """
        return self.__version


    #----------------------------------------------------------------------
    @identity
    def cpe(self):
        """
        :return: CPE name.
        :rtype: str
        """
        return self.__cpe


    #----------------------------------------------------------------------
    @identity
    def others(self):
        """
        :return: Map of other possible OS by name and their probabilities of being correct [0.0 ~ 1.0].
        :rtype: dict( str -> float )
        """
        return self.__others
