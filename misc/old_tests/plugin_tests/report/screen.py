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

from golismero.api.plugin import ReportPlugin
from golismero.api.data.db import Database
from golismero.api.config import Config

# Data types
from golismero.api.data import Data
from golismero.api.data.resource import Resource
from golismero.api.data.information import Information


class TestReport(ReportPlugin):
    """
    Plugin to test the reports.
    """


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):
        return not output_file or output_file == "-"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):

        # Dump all objects in the database.
        print "-" * 79
        print "Report:"
        for data in Database.iterate():
            print
            print data.identity
            print repr(data)
            print sorted(data.links)
            for linked in data.linked_data:
                print "--> " + linked.identity
                print "--> " + repr(linked)
        print
