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

from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.url import URL
from golismero.api.data.vulnerability.injection.sql import SQLInjection
from golismero.api.data.vulnerability.injection.xss import XSS
from golismero.api.logger import Logger
from golismero.api.plugin import TestingPlugin
from golismero.api.text.text_utils import to_utf8
from golismero.api.net.web_utils import parse_url

import requests
import traceback


#------------------------------------------------------------------------------
class PunkSPIDER(TestingPlugin):
    """
    This plugin tries to perform passive reconnaissance on a target using
    the PunkSPIDER vulnerability lookup engine.
    """


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [Domain]


    #--------------------------------------------------------------------------
    def run(self, info):

        # Query PunkSPIDER.
        host_id = info.hostname
        host_id = parse_url(host_id).hostname
        host_id = ".".join(reversed(host_id.split(".")))
        d = self.query_punkspider(host_id)

        # Stop if we have no results.
        if not d:
            Logger.log("No results found for host: %s" % info.hostname)
            return

        # This is where we'll collect the data we'll return.
        results = []

        # For each vulnerability...
        for v in d["data"]:
            try:

                # Future-proof checks.
                if v["protocol"] not in ("http", "https"):
                    Logger.log_more_verbose(
                        "Skipped non-web vulnerability: %s"
                        % to_utf8(v["id"]))
                    continue
                if v["bugType"] not in ("xss", "sqli", "bsqli"):
                    Logger.log_more_verbose(
                        "Skipped unknown vulnerability type: %s"
                        % to_utf8(v["bugType"]))
                    continue

                # Get the vulnerable URL, parameter and payload.
                url = to_utf8(v["vulnerabilityUrl"])
                param = to_utf8(v["parameter"])
                parsed = parse_url(url)
                payload = parsed.query_params[param]

                # Get the level.
                level = to_utf8(v["level"])

                # Create the URL object.
                url_o = URL(url)
                results.append(url_o)

                # Get the vulnerability class.
                if v["bugType"] == "xss":
                    clazz = XSS
                else:
                    clazz = SQLInjection

                # Create the Vulnerability object.
                vuln = clazz(
                    url_o,
                    vulnerable_params = { param: payload },
                    injection_point = clazz.INJECTION_POINT_URL,
                    injection_type = to_utf8(v["bugType"]), # FIXME
                    level = level,
                    tool_id = to_utf8(v["id"]),
                )
                results.append(vuln)

            # Log errors.
            except Exception, e:
                tb = traceback.format_exc()
                Logger.log_error_verbose(str(e))
                Logger.log_error_more_verbose(tb)

        # Log how many vulnerabilities we found.
        count = int(len(results) / 2)
        if count == 0:
            Logger.log("No vulnerabilities found for host: " + info.hostname)
        elif count == 1:
            Logger.log("Found one vulnerability for host: " + info.hostname)
        else:
            Logger.log("Found %d vulnerabilities for host: %s"
                       % (count, info.hostname))

        # Return the results.
        return results


    #--------------------------------------------------------------------------
    # The PunkSPIDER API.

    URL = (
        "https://www.punkspider.org/service/search/detail/%s"
    )

    HEADERS = {
        "Accept": "*/*",
        "Referer": "https://www.punkspider.org/",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/31.0.1650.63 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    def query_punkspider(self, host_id):
        try:
            r = requests.get(self.URL % host_id,
                             headers = self.HEADERS,
                             verify=False)
            assert r.headers["Content-Type"].startswith("application/json"),\
                "Response from server is not a JSON encoded object"
            return r.json()
        except requests.RequestException, e:
            Logger.log_error(
                "Query to PunkSPIDER failed, reason: %s" % str(e))
