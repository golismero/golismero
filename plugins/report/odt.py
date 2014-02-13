#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

__all__ = ["ODTReport"]

from golismero.api.external import tempfile
from golismero.api.logger import Logger
from golismero.api.plugin import import_plugin

rstext = import_plugin("rst.py")

from warnings import catch_warnings


#------------------------------------------------------------------------------
class ODTReport(rstext.RSTReport):
    """
    Creates reports in OpenOffice document format (.odt).
    """

    EXTENSION = ".odt"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        Logger.log_verbose(
            "Writing OpenOffice report to file: %s" % output_file)

        # Load docutils.
        with catch_warnings(record=True):
            from docutils.core import publish_file
            from docutils.writers.odf_odt import Writer, Reader

        # Create a temporary file for the reStructured Text report.
        with tempfile(suffix=".rst") as filename:

            # Generate the report in reStructured Text format.
            Logger.log_more_verbose("Writing temporary file in rST format...")
            with open(filename, "w") as source:
                self.write_report_to_open_file(source)

            # Convert to OpenOffice format.
            Logger.log_more_verbose("Converting to OpenOffice format...")
            with open(filename, "rU") as source:
                writer = Writer()
                reader = Reader()
                with catch_warnings(record=True):
                    with open(output_file, "wb") as destination:
                        publish_file(
                            source = source,
                            destination = destination,
                            destination_path = output_file,
                            reader = reader,
                            writer = writer,
                        )
