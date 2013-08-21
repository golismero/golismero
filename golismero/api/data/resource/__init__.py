#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Resource types.
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn@cr0hn.com
  Mario Vilas | mvilas@gmail.com

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

__all__ = ["Resource"]

from .. import Data


#------------------------------------------------------------------------------
class Resource(Data):
    """
    Base class for resources.
    """

    #--------------------------------------------------------------------------
    #
    # Types of Infomation results
    #
    #--------------------------------------------------------------------------
    RESOURCE_UNKNOWN       = 0    # Not a real value!
    RESOURCE_URL           = 1    # URLs
    RESOURCE_BASE_URL      = 2    # Base URLs
    RESOURCE_FOLDER_URL    = 3    # Folder URLs
    RESOURCE_DOMAIN        = 4    # Domain names
    RESOURCE_IP            = 5    # IP addresses
    RESOURCE_EMAIL         = 6    # Email addresses


    #----------------------------------------------------------------------

    data_type = Data.TYPE_RESOURCE
    resource_type = RESOURCE_UNKNOWN
