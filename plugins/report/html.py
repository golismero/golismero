
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

__all__ = ["HTMLReport"]

from golismero import __version__ as VERSION
from golismero.api.config import Config
from golismero.api.data.information import Information
from golismero.api.data.vulnerability import Vulnerability
from golismero.api.data.vulnerability.vuln_utils import TAXONOMY_NAMES
from golismero.api.external import tempfile
from golismero.api.logger import Logger
from golismero.api.plugin import import_plugin, get_plugin_name

from collections import Counter
from zipfile import ZipFile, ZIP_DEFLATED

import cgi
import os
import os.path
import warnings

json = import_plugin("json.py")


#------------------------------------------------------------------------------
class HTMLReport(json.JSONOutput):
    """
    Writes reports as offline web pages.
    """


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):
        if not output_file:
            return False
        output_file = output_file.lower()
        return (
            output_file.endswith(".html") or
            output_file.endswith(".htm")
        )


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):

        Logger.log_verbose(
            "Writing HTML report to file: %s" % output_file)

        Logger.log_more_verbose("Generating JSON database...")

        # Warn about --full not being supported by this plugin.
        if not Config.audit_config.only_vulns:
            Config.audit_config.only_vulns = True
            Logger.log_more_verbose(
                "Full report mode not supported, switching to brief mode.")

        # Hardcode the arguments for the JSON plugin.
        Config.plugin_args["mode"] = "dump"
        Config.plugin_args["command"] = ""

        # Get the report data.
        report_data = self.get_report_data()

        Logger.log_more_verbose("Postprocessing JSON database...")

        # Remove the false positives, if any.
        del report_data["false_positives"]

        # Gather all taxonomies into a single property.
        for vuln in report_data["vulnerabilities"].itervalues():
            taxonomy = []
            for prop in TAXONOMY_NAMES:
                taxonomy.extend(vuln.get(prop, []))
            if taxonomy:
                taxonomy.sort()
                vuln["taxonomy"] = taxonomy

        # It's easier for the JavaScript code in the report to access the
        # vulnerabilities as an array instead of a map, so let's fix that.
        # Also, delete all properties we know aren't being used in the report.
        vulnerabilities = report_data["vulnerabilities"]
        sort_keys = [
            (data["display_name"],
             data["plugin_id"],
             data["target_id"],
             data["identity"])
            for data in vulnerabilities.itervalues()
        ]
        sort_keys.sort()
        report_data["vulnerabilities"] = [
            {
                propname: propvalue
                for propname, propvalue
                in vulnerabilities[identity].iteritems()
                if propname in (
                    "display_name",
                    "plugin_id",
                    "target_id",
                    "identity",
                    "links",
                    "data_type",
                    "data_subtype",
                    "title",
                    "description",
                    "solution",
                    "taxonomy",
                    "references",
                    "level",
                    "impact",
                    "severity",
                    "risk",
                )
            }
            for _, _, _, identity in sort_keys
        ]
        vulnerabilities.clear()
        sort_keys = []

        # Remove a bunch of data that won't be shown in the report anyway.
        for identity, data in report_data["informations"].items():
            if data["information_category"] not in (
                Information.CATEGORY_ASSET,
                Information.CATEGORY_FINGERPRINT,
            ):
                del report_data["informations"][identity]

        # Remove any dangling links we may have.
        links = set()
        for iterator in (
            report_data["resources"].itervalues(),
            report_data["informations"].itervalues(),
            report_data["vulnerabilities"]
        ):
            links.update(data["identity"] for data in iterator)
        for iterator in (
            report_data["resources"].itervalues(),
            report_data["informations"].itervalues(),
            report_data["vulnerabilities"]
        ):
            for data in iterator:
                tmp = set(data["links"])
                tmp.intersection_update(links)
                data["links"] = sorted(tmp)
                tmp.clear()
        links.clear()

        # Now, let's go through all Data objects and try to resolve the
        # plugin IDs to user-friendly plugin names.
        plugin_map = dict()
        for iterator in (
            report_data["resources"].itervalues(),
            report_data["informations"].itervalues(),
            report_data["vulnerabilities"]
        ):
            for data in iterator:
                if "plugin_id" in data:
                    plugin_id = data["plugin_id"]
                    if plugin_id not in plugin_map:
                        plugin_map[plugin_id] = get_plugin_name(plugin_id)
                    data["plugin_name"] = plugin_map[plugin_id]
        plugin_map.clear()

        # Calculate some statistics, so the JavaScript code doesn't have to.
        vulns_by_level = Counter()
        for level in Vulnerability.VULN_LEVELS:
            vulns_by_level[level] = 0
        vulns_by_level.update(
            v["level"] for v in report_data["vulnerabilities"])
        vulns_by_level = {k.title(): v for k, v in vulns_by_level.iteritems()}
        vulns_by_type = dict(Counter(
                v["display_name"] for v in report_data["vulnerabilities"]
            ))
        report_data["stats"] = {
            "resources":       len(report_data["resources"]),
            "informations":    len(report_data["informations"]),
            "vulnerabilities": len(report_data["vulnerabilities"]),
            "vulns_by_level":  vulns_by_level,
            "vulns_by_type":   vulns_by_type,
        }

        # It's better to show vulnerability levels as integers instead
        # of strings, so they can be sorted in the proper order. The
        # actual report shows them to the user as strings, but sorts
        # using the integer values.
        for vuln in report_data["vulnerabilities"]:
            vuln["level"] = Vulnerability.VULN_LEVELS.index(vuln["level"])

        # Generate the ZIP file comment.
        comment = "Report generated with GoLismero %s at %s UTC\n"\
                  % (VERSION, report_data["summary"]["report_time"])

        # Serialize the data and cleanup the unserialized version.
        serialized_data = json.dumps(report_data)
        del report_data

        # Escape all HTML entities from the serialized data,
        # since the JSON library doesn't seem to do it.
        serialized_data = cgi.escape(serialized_data)

        # Save the report data to disk.
        Logger.log_more_verbose("Writing report to disk...")
        template = os.path.dirname(__file__)
        template = os.path.abspath(template)
        template = os.path.join(template, "template.html")
        with open(template, "rb") as fd:
            html = fd.read()
        assert "%DATA%" in html, "Invalid template!"
        html = html.replace("%DATA%", serialized_data)
        del serialized_data
        with open(output_file, "wb") as fd:
            fd.write(html)
