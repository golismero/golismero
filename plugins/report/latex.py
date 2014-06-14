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

__all__ = ["LatexReport"]

import warnings
import sys

from os.path import abspath, split

from golismero.api.external import tempfile
from golismero.api.logger import Logger
from golismero.api.plugin import import_plugin

rstext = import_plugin("rst.py")


#------------------------------------------------------------------------------
class LatexReport(rstext.RSTReport):
    """
    Creates reports in LaTeX format (.tex).
    """

    EXTENSION = ".tex"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):

        # Workaround for docutils bug, see:
        # http://sourceforge.net/p/docutils/bugs/228/
        sentinel = object()
        old_standalone = sys.modules.get("standalone", sentinel)
        try:
            cwd = abspath(split(__file__)[0])
            sys.path.insert(0, cwd)
            try:
                with warnings.catch_warnings(record=True):
                    from docutils.readers import standalone
                    sys.modules["standalone"] = standalone
            finally:
                sys.path.remove(cwd)
            self.__generate_report(output_file)
        finally:
            if old_standalone is not sentinel:
                sys.modules["standalone"] = old_standalone
            else:
                del sys.modules["standalone"]


    #--------------------------------------------------------------------------
    def __generate_report(self, output_file):
        Logger.log_verbose(
            "Writing LaTeX report to file: %s" % output_file)

        # Load docutils.
        with warnings.catch_warnings(record=True):
            from docutils.core import publish_file

        # Create a temporary file for the reStructured Text report.
        with tempfile(suffix=".rst") as filename:

            # Generate the report in reStructured Text format.
            Logger.log_more_verbose("Writing temporary file in rST format...")
            with open(filename, "w") as source:
                self.write_report_to_open_file(source)

            # Convert to LaTeX format.
            Logger.log_more_verbose("Converting to LaTeX format...")
            with open(filename, "rU") as source:
                with warnings.catch_warnings(record=True):
                    with open(output_file, "wb") as destination:
                        publish_file(
                            source = source,
                            destination = destination,
                            destination_path = output_file,
                            writer_name = "latex",
                        )
