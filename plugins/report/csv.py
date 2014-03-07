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

__all__ = ["CSVReport"]

from golismero.api import VERSION
from golismero.api.audit import get_audit_times, parse_audit_times
from golismero.api.config import Config
from golismero.api.data import Data
from golismero.api.data.db import Database
from golismero.api.logger import Logger
from golismero.api.plugin import ReportPlugin
from golismero.api.text.text_utils import to_utf8

from datetime import datetime

import csv

# Load the fast C version of pickle,
# if not available use the pure-Python version.
try:
    import cPickle as pickle
except ImportError:
    import pickle


#------------------------------------------------------------------------------
class CSVReport(ReportPlugin):
    """
    Creates reports in CSV format.
    """

    EXTENSION = ".csv"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        Logger.log_verbose(
            "Writing CSV report to file: %s" % output_file)

        # All rows have the same format but the first.
        # There's always 26 columns in every row.
        # Most columns are for Vulnerability objects, empty for other types.
        # Read the source code for more details, it's really simple. :)

        # Open the output file.
        with open(output_file, "w") as f:
            writer = csv.writer(f)

            # Write the first row, describing the report itself.
            report_time = datetime.utcnow()
            start_time, stop_time, run_time = parse_audit_times(
                                                        *get_audit_times())
            row = [
                "GoLismero " + VERSION,
                1,  # format version
                Config.audit_name,
                start_time,
                stop_time,
                run_time,
                report_time,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                pickle.dumps(Config.audit_config, protocol=0).encode("hex"),
                pickle.dumps(Config.audit_scope, protocol=0).encode("hex"),
            ]
            row = [to_utf8(x) if x is not None else "" for x in row]
            writer.writerow(row)

            # Used to convert the false_positive flag to a string value.
            fp = {
                True: 1,
                False: 0,
                None: -1,
            }

            # Just the vulnerabilities?
            if Config.audit_config.only_vulns:

                # Dump only Vulnerability objects that are not false positives.
                for vuln in self.__iterate_data(
                        data_type=Data.TYPE_VULNERABILITY):
                    if vuln.false_positive:
                        continue
                    target = vuln.target
                    row = [
                        vuln.identity,
                        vuln.data_type,
                        vuln.data_subtype,
                        None,
                        vuln.display_name,
                        vuln.plugin_id,
                        vuln.tool_id,
                        vuln.custom_id,
                        vuln.level,
                        vuln.risk,
                        vuln.severity,
                        vuln.impact,
                        vuln.cvss_base,
                        vuln.cvss_score,
                        vuln.cvss_vector,
                        fp[vuln.false_positive],
                        target.identity,
                        target.display_name,
                        vuln.title,
                        vuln.description,
                        vuln.solution,
                        "\n".join(vuln.references),
                        "\n".join(vuln.taxonomies),
                        str(target),
                        pickle.dumps(vuln, protocol=0).encode("hex"),
                        pickle.dumps(target, protocol=0).encode("hex"),
                    ]
                    row = [to_utf8(x) if x is not None else "" for x in row]
                    writer.writerow(row)

            # Full database dump?
            else:

                # Dump all objects in the database.
                for data in self.__iterate_data():
                    if data.data_type == Data.TYPE_VULNERABILITY:
                        vuln = data
                        target = vuln.target
                        row = [
                            vuln.identity,
                            vuln.data_type,
                            vuln.data_subtype,
                            None,
                            vuln.display_name,
                            vuln.plugin_id,
                            vuln.tool_id,
                            vuln.custom_id,
                            vuln.level,
                            vuln.risk,
                            vuln.severity,
                            vuln.impact,
                            vuln.cvss_base,
                            vuln.cvss_score,
                            vuln.cvss_vector,
                            fp[vuln.false_positive],
                            target.identity,
                            target.display_name,
                            vuln.title,
                            vuln.description,
                            vuln.solution,
                            "\n".join(vuln.references),
                            "\n".join(vuln.taxonomies),
                            str(target),
                            pickle.dumps(vuln, protocol=0).encode("hex"),
                            pickle.dumps(target, protocol=0).encode("hex"),
                        ]
                    else:
                        row = [
                            data.identity,
                            data.data_type,
                            data.data_subtype,
                            getattr(data, "category", None),
                            data.display_name,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            0,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            str(data),
                            None,
                            pickle.dumps(data, protocol=0).encode("hex"),
                        ]
                    row = [to_utf8(x) if x is not None else "" for x in row]
                    writer.writerow(row)


    #--------------------------------------------------------------------------
    def __iterate_data(self,
                       identities = None,
                       data_type = None,
                       data_subtype = None):
        if identities is None:
            identities = list(Database.keys(data_type, data_subtype))
        if identities:
            for page in xrange(0, len(identities), 100):
                for data in Database.get_many(identities[page:page + 100]):
                    yield data
