#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Information types.
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
Golismero project mail: contact@golismero-project.com

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

__all__ = ["Information", "File", "Asset", "Capture", "Fingerprint"]

from .. import Data


#------------------------------------------------------------------------------
class Information(Data):
    """
    Base class for informational results.
    """

    # Categories of informational data.
    CATEGORY_UNKNOWN     = 0    # Not a real value!
    CATEGORY_FILE        = 1
    CATEGORY_ASSET       = 2
    CATEGORY_CAPTURE     = 3
    CATEGORY_FINGERPRINT = 4

    data_type = Data.TYPE_INFORMATION
    data_subtype = "information/abstract"
    information_category = CATEGORY_UNKNOWN


#------------------------------------------------------------------------------
class File(Information):
    """
    File Data: raw file contents.
    """

    data_subtype = "information/abstract"
    information_category = Information.CATEGORY_FILE


#------------------------------------------------------------------------------
class Asset(Information):
    """
    Assets: sensitive information captured from the targets.
    """

    data_subtype = "information/abstract"
    information_category = Information.CATEGORY_ASSET


#------------------------------------------------------------------------------
class Capture(Information):
    """
    Protocol captures: raw network protocol dumps.
    """

    data_subtype = "information/abstract"
    information_category = Information.CATEGORY_CAPTURE


#------------------------------------------------------------------------------
class Fingerprint(Information):
    """
    Fingerprints: reconnaissance results.
    """

    data_subtype = "information/abstract"
    information_category = Information.CATEGORY_FINGERPRINT
