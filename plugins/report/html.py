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
            output_file.endswith(".htm") or
            output_file.endswith(".zip")
        )


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):

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

        # It's easier for the JavaScript code in the report to access the
        # vulnerabilities as an array instead of a map, so let's fix that.
        # Also, delete all properties we know aren't being used in the report.
        vulnerabilities = report_data["vulnerabilities"]
        sort_keys = [
            (data["display_name"],
             data["plugin_id"],
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
                    "identity",
                    "links",
                    "data_type",
                    "data_subtype",
                    "title",
                    "description",
                    "solution",
                    "references",
                    "level",
                    "impact",
                    "severity",
                    "risk",
                )
            }
            for _, _, identity in sort_keys
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

        # We also want to tell the HTML report which of the vulnerability
        # properties are part of the taxonomy. This saves us from having to
        # change the HTML code every time we add a new taxonomy property.
        ##report_data["supported_taxonomies"] = TAXONOMY_NAMES

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
        if output_file.endswith(".zip"):
            serialized_data = json.dumps(report_data,
                                         sort_keys=True, indent=4)
        else:
            serialized_data = json.dumps(report_data)
        del report_data

        # Get the directory where we can find our template.
        html_report = os.path.dirname(__file__)
        html_report = os.path.join(html_report, "html_report")
        html_report = os.path.abspath(html_report)
        if not html_report.endswith(os.path.sep):
            html_report += os.path.sep

        # Save the report data to disk.
        Logger.log_more_verbose("Writing report to disk...")

        # Save it as a zip file.
        if output_file.endswith(".zip"):
            with ZipFile(output_file, mode="w", compression=ZIP_DEFLATED,
                         allowZip64=True) as zip:

                # Save the zip file comment.
                zip.comment = comment

                # Save the JSON data.
                arcname = os.path.join("js", "database.js")
                serialized_data = "data = " + serialized_data
                zip.writestr(arcname, serialized_data)
                del serialized_data

                # Copy the template dependencies into the zip file.
                for root, directories, files in os.walk(html_report):
                    if root.endswith(os.path.sep + "backup"):
                        continue
                    for basename in files:
                        if basename.endswith(".less"):
                            continue
                        if basename in ("index.html", "database.js"):
                            continue
                        filename = os.path.join(root, basename)
                        arcname = filename[len(html_report):]
                        if arcname == "index-orig.html":
                            arcname = "index.html"
                        zip.write(filename, arcname)

        # Save it as an HTML file with no dependencies.
        else:
            with open(os.path.join(html_report, "index.html"), "rb") as fd:
                template = fd.read()
            assert "%DATA%" in template
            serialized_data = template.replace("%DATA%", serialized_data)
            del template
            with open(output_file, "wb") as fd:
                fd.write(serialized_data)
