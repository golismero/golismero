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

from . import Information
from .. import identity


#------------------------------------------------------------------------------
class Binary(Information):
    """
    Binary data.
    """

    information_type = Information.INFORMATION_BINARY


    #----------------------------------------------------------------------
    def __init__(self, data):
        """
        :param data: Raw bytes.
        :type data: str
        """
        if type(data) is not str:
            raise TypeError("Expected string, got %r instead" % type(data))

        # Raw bytes.
        self.__raw_data = data

        # Parent constructor.
        super(Binary, self).__init__()


    #----------------------------------------------------------------------
    @identity
    def raw_data(self):
        """
        :returns: Raw bytes.
        :rtype: str
        """
        return self.__raw_data
