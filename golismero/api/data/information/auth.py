#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authentication data.
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

__all__ = ["Username", "Password"]

from . import Information
from .. import identity


#------------------------------------------------------------------------------
class Username(Information):
    """
    Username.
    """

    information_type = Information.INFORMATION_USERNAME


    #----------------------------------------------------------------------
    def __init__(self, name):
        """
        :param name: Username.
        :type name: str
        """
        if not isinstance(name, basestring):
            raise TypeError("Expected string, got %s instead" % type(name))
        self.__name = name
        super(Username, self).__init__()


    #----------------------------------------------------------------------
    @identity
    def name(self):
        """
        :returns: Username.
        :rtype: str
        """
        return self.__name


#------------------------------------------------------------------------------
class Password(Information):
    """
    Password.
    """

    information_type = Information.INFORMATION_PASSWORD


    #----------------------------------------------------------------------
    def __init__(self, password):
        """
        :param password: Password.
        :type password: str
        """
        if not isinstance(password, basestring):
            raise TypeError("Expected string, got %s instead" % type(password))
        self.__password = password
        super(Password, self).__init__()


    #----------------------------------------------------------------------
    @identity
    def password(self):
        """
        :returns: Password.
        :rtype: str
        """
        return self.__password
