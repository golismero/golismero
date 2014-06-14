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

__all__ = ["BSONOutput"]

from golismero.api.logger import Logger
from golismero.api.plugin import import_plugin
json = import_plugin("json.py")

# Lazy imports.
BSON = None


#------------------------------------------------------------------------------
class BSONOutput(json.JSONOutput):
    """
    Dumps the output in BSON (Binary JSON) format.
    """

    EXTENSION = ".bson"


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):
        if super(BSONOutput, self).is_supported(output_file):
            try:
                self.load_bson()
            except ImportError:
                Logger.log_error(
                    "BSON encoder not found!\n"
                    "Get it from:\n"
                    "    https://github.com/mongodb/mongo-python-driver\n"
                    "Or alternatively from:\n"
                    "    https://github.com/martinkou/bson"
                )
                return False
            return True
        return False


    #--------------------------------------------------------------------------
    @staticmethod
    def load_bson():
        global BSON
        if BSON is None:
            try:
                from pymongo.bson import BSON
            except ImportError:
                from bson import dumps
                class BSON(object):
                    @staticmethod
                    def encode(obj, *args, **kwargs):
                        return dumps(obj)


    #--------------------------------------------------------------------------
    def serialize_report(self, output_file, report_data):
        self.load_bson()
        bson_data = BSON.encode(report_data, check_keys=True)
        with open(output_file, "wb") as fp:
            fp.write(bson_data)


    #--------------------------------------------------------------------------
    def test_data_serialization(self, data):
        self.load_bson()
        BSON.encode(data, check_keys=True)
