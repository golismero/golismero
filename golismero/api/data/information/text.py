#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plain text data.
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

__all__ = ["Text"]

from . import Information
from .. import identity


#------------------------------------------------------------------------------
class Text(Information):
    """
    Plain text data.
    """

    information_type = Information.INFORMATION_PLAIN_TEXT


    #----------------------------------------------------------------------
    def __init__(self, data):
        """
        :param data: Plain text data.
        :type data: str
        """
        if not isinstance(data, basestring):
            raise TypeError("Expected string, got %s instead" % type(data))

        # Text.
        self.__raw_data = data

        # Parent constructor.
        super(Text, self).__init__()


    #----------------------------------------------------------------------
    @identity
    def raw_data(self):
        """
        :return: Plain text data.
        :rtype: str
        """
        return self.__raw_data
