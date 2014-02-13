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

__all__ = ["TextLogger"]

from golismero.api.audit import get_audit_log_lines
from golismero.api.config import Config
from golismero.api.logger import Logger
from golismero.api.plugin import ReportPlugin, get_plugin_info

from collections import namedtuple, defaultdict
from time import asctime, gmtime


#------------------------------------------------------------------------------
LogLine = namedtuple(
    "LogLine",
    [
        "plugin_id", "identity", "text", "level", "is_err", "time",
    ]
)


#------------------------------------------------------------------------------
class TextLogger(ReportPlugin):
    """
    Extracts only the logs.
    """

    EXTENSION = ".log"


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        Logger.log_verbose("Writing audit logs to file: %s" % output_file)

        # plugin_id -> plugin_name
        self.plugin_names = dict()

        # plugin_id -> ack_identity -> simple_id
        self.current_plugins = defaultdict(dict)

        # Open the output file.
        with open(output_file, "w") as f:

            # Paginate the log lines to limit the memory usage.
            page_num = 0
            while True:
                lines = get_audit_log_lines(page_num = page_num,
                                            per_page = 100)
                if not lines:
                    break
                page_num += 1

                # For each log line...
                for line in lines:

                    # Split the line into its components.
                    d = LogLine(*line)._asdict()

                    # Fix the log levels.
                    d["level"] = {
                        0: "INFO",
                        1: "LOW",
                        2: "MED",
                        3: "HIGH",
                    }.get(d["level"], "HIGH")
                    if d["is_err"]:
                        d["level"] = "ERR_" + d["level"]

                    # Fix the timestamp.
                    d["time"] = asctime(gmtime(d["time"]))

                    # Fix the plugin name.
                    d["plugin"] = self.get_plugin_name(
                        d["plugin_id"], d["identity"])

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

                    # Write the log lines.
                    for d in sub_lines:
                        l = "%(time)s : %(level)s : %(plugin)s : %(text)s\n"
                        l %= d
                        f.write(l.encode("utf-8"))

        # Launch the build command, if any.
        self.launch_command(output_file)


    #--------------------------------------------------------------------------
    def get_plugin_name(self, plugin_id, ack_identity):

        # If the message comes from the Orchestrator.
        if not plugin_id:
            return "GoLismero"

        # If the message is for us, just return our name.
        if plugin_id == Config.plugin_id:
            return Config.plugin_info.display_name

        # Get the plugin display name.
        plugin_name = self.plugin_names.get(plugin_id, None)
        if plugin_name is None:
            plugin_name = get_plugin_info(plugin_id).display_name
            self.plugin_names[plugin_id] = plugin_name

        # Append the simple ID if it's greater than zero.
        if ack_identity:
            ack_dict = self.current_plugins[plugin_id]
            simple_id = ack_dict.get(ack_identity, None)
            if simple_id is None:
                simple_id = len(ack_dict)
                ack_dict[ack_identity] = simple_id
            elif simple_id > 0:
                plugin_name = "%s (%d)" % (plugin_name, simple_id + 1)

        # Return the display name.
        return plugin_name
