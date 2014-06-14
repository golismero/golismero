#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from golismero.api.plugin import ImportPlugin
from golismero.api.data.db import Database
from golismero.api.config import Config

# Data types
from golismero.api.data import Data
from golismero.api.data.resource import Resource
from golismero.api.data.information import Information


class TestImport(ImportPlugin):
    """
    Plugin to test the results import functionality.
    """


    #--------------------------------------------------------------------------
    def is_supported(self, input_file):
        return False    # XXX TODO


    #--------------------------------------------------------------------------
    def import_results(self, input_file):

        pass            # XXX TODO
