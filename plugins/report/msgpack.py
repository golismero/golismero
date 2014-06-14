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

__all__ = ["MessagePackOutput"]

from golismero.api.plugin import import_plugin
json = import_plugin("json.py")

# Lazy imports.
umsgpack = None


#------------------------------------------------------------------------------
class MessagePackOutput(json.JSONOutput):
    """
    Dumps the output in MessagePack format.
    """

    EXTENSION = ".msgpack"


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):

        # Load MessagePack.
        global umsgpack
        if umsgpack is None:
            try:
                import umsgpack
            except ImportError:
                raise RuntimeError(
                    "MessagePack not installed!"
                    " You can get it from: http://msgpack.org/")

        # Call the superclass method.
        return super(MessagePackOutput, self).is_supported(output_file)


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):

        # Load MessagePack.
        global umsgpack
        if umsgpack is None:
            try:
                import umsgpack
            except ImportError:
                raise RuntimeError(
                    "MessagePack not installed!"
                    " You can get it from: http://msgpack.org/")

        # Call the superclass method.
        super(MessagePackOutput, self).generate_report(output_file)


    #--------------------------------------------------------------------------
    def serialize_report(self, output_file, report_data):
        raw_data = umsgpack.packb(report_data)
        with open(output_file, "wb") as fp:
            fp.write(raw_data)


    #--------------------------------------------------------------------------
    def test_data_serialization(self, data):
        umsgpack.packb(data)
