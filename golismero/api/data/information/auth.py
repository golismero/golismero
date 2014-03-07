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

__all__ = ["Username", "Password", "get_credentials"]

from . import Asset
from .. import identity, Relationship
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class Username(Asset):
    """
    Username.

    May be linked to one or more Password objects
    to indicate a valid set of credentials.
    """

    data_subtype = "username"


    #--------------------------------------------------------------------------
    def __init__(self, name):
        """
        :param name: Username.
        :type name: str
        """
        if not isinstance(name, basestring):
            raise TypeError("Expected string, got %r instead" % type(name))
        self.__name = to_utf8(name)
        super(Username, self).__init__()


    #--------------------------------------------------------------------------
    @identity
    def name(self):
        """
        :returns: Username.
        :rtype: str
        """
        return self.__name


#------------------------------------------------------------------------------
class Password(Asset):
    """
    Password.

    May be linked to one or more Username objects
    to indicate a valid set of credentials.
    """

    data_subtype = "password"


    #--------------------------------------------------------------------------
    def __init__(self, password):
        """
        :param password: Password.
        :type password: str
        """
        if not isinstance(password, basestring):
            raise TypeError("Expected str, got %r instead" % type(password))
        self.__password = to_utf8(password)
        super(Password, self).__init__()


    #--------------------------------------------------------------------------
    @identity
    def password(self):
        """
        :returns: Password.
        :rtype: str
        """
        return self.__password


#------------------------------------------------------------------------------
def get_credentials(user_or_pass):
    """
    Given a username or a password,
    find valid credentials in the audit database.

    :param user_or_pass: Username or password.
    :type user_or_pass: Username | Password

    :returns: Valid credentials.
    :rtype: list(Relationship(Username, Password))
    """

    # If given a username, look for passwords.
    if user_or_pass.is_instance(Username):
        passwords = {
            x.password: x for x in user_or_pass.find_linked_data(
                Password.data_type, Password.data_subtype)
        }
        Rel = Relationship(Username, Password)
        keys = passwords.keys()
        keys.sort()
        return [ Rel(user_or_pass, passwords[x]) for x in keys ]

    # If given a password, look for usernames.
    if user_or_pass.is_instance(Password):
        usernames = {
            x.name: x for x in user_or_pass.find_linked_data(
                Username.data_type, Username.data_subtype)
        }
        Rel = Relationship(Username, Password)
        keys = usernames.keys()
        keys.sort()
        return [ Rel(usernames[x], user_or_pass) for x in keys ]

    # If given anything else, raise an exception.
    raise TypeError(
        "Expected Username or Password, got %r instead" % type(user_or_pass))
