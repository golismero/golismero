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

__all__ = ["LTSVLogger"]

from golismero.api.audit import get_audit_log_lines
from golismero.api.logger import Logger
from golismero.api.plugin import ReportPlugin

from collections import namedtuple
from time import asctime, gmtime


#------------------------------------------------------------------------------
LogLine = namedtuple(
    "LogLine",
    [
        "plugin_id", "identity", "text", "level", "is_err", "time",
    ]
)


#------------------------------------------------------------------------------
class LTSVLogger(ReportPlugin):
    """
    Extracts only the logs, in labeled tab-separated values format.
    """

    EXTENSION = ".ltsv"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        Logger.log_verbose("Writing audit logs to file: %s" % output_file)

        # Open the output file.
        with open(output_file, "w") as f:

            # Paginate the log lines to limit the memory usage.
            page_num = 0
            while True:
                lines = get_audit_log_lines(page_num = page_num,
                                            per_page = 20)
                if not lines:
                    break
                page_num += 1

                # For each log line...
                for line in lines:

                    # Split the line into its components.
                    n = LogLine(*line)
                    d = n._asdict()
                    k = list(n._fields)

                    # Fix the log levels.
                    d["level"] = {
                        0: "INFO",
                        1: "LOW",
                        2: "MED",
                        3: "HIGH",
                    }.get(d["level"], "HIGH")
                    if d["is_err"]:
                        d["level"] = "ERR_" + d["level"]
                    del d["is_err"]
                    k.remove("is_err")

                    # Fix the timestamp.
                    d["time"] = asctime(gmtime(d["time"]))

                    # We can't have tab characters in the text.
                    # Replace them with spaces.
                    d["text"] = d["text"].replace("\t", " " * 8)

                    # The text may contain newlines, so we'll have to
                    # split it into multiple log lines if that happens.
                    if "\n" not in d["text"]:
                        sub_lines = [d]
                    else:
                        sub_lines = []
                        for x in d["text"].split("\n"):
                            x = x.rstrip()
                            d["text"] = x
                            sub_lines.append(d.copy())

                    # Write the log in LTSV format.
                    for d in sub_lines:
                        l = "\t".join(
                            "%s:%s" % (x, d[x])
                            for x in k
                        ) + "\n"
                        f.write(l.encode("utf-8"))

        # Launch the build command, if any.
        self.launch_command(output_file)
