#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Binary data.
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

__all__ = ["Binary"]

from . import File
from .. import identity


#------------------------------------------------------------------------------
class Binary(File):
    """
    Binary data.
    """

    information_type = File.INFORMATION_BINARY


    #--------------------------------------------------------------------------
    def __init__(self, data, content_type = "application/octet-stream"):
        """
        :param data: Raw bytes.
        :type data: str

        :param content_type: MIME type.
        :type content_type: str
        """

        # Check the argument types.
        if type(data) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(data))
        if type(content_type) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(content_type))
        if "/" not in content_type:
            raise ValueError("Invalid MIME type: %r" % content_type)
        if ";" in content_type and content_type.find(";") < content_type.find("/"):
            raise ValueError("Invalid MIME type: %r" % content_type)
        # TODO: canonicalize the MIME type

        # Save the properties.
        self.__raw_data     = data
        self.__content_type = content_type

        # Parent constructor.
        super(Binary, self).__init__()


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Binary Data"


    #--------------------------------------------------------------------------
    @identity
    def raw_data(self):
        """
        :returns: Raw bytes.
        :rtype: str
        """
        return self.__raw_data


    #--------------------------------------------------------------------------
    @identity
    def content_type(self):
        """
        :returns: MIME type.
        :rtype: str
        """
        return self.__content_type


    #--------------------------------------------------------------------------
    @property
    def mime_type(self):
        """
        :returns: First component of the MIME type.
        :rtype: str
        """
        content_type = self.content_type
        content_type = content_type[ : content_type.find("/") ]
        content_type = content_type.lower()
        return content_type


    #--------------------------------------------------------------------------
    @property
    def mime_subtype(self):
        """
        :returns: Second component of the MIME type.
        :rtype: str
        """
        content_type = self.content_type
        content_type = content_type[ content_type.find("/") + 1 : ]
        if ";" in content_type:
            content_type = content_type[ : content_type.find(";") ]
        content_type = content_type.lower()
        return content_type
