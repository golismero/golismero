#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Authors:
  Jekkay Hu | jekkay<@>gmail.com
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: http://golismero-project.com
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

import shlex
from time import time
from traceback import format_exc
from os.path import join

from golismero.api.config import Config
from golismero.api.data.resource.url import URL
from golismero.api.data.vulnerability.injection.xss import XSS
from golismero.api.external import run_external_tool, tempfile, \
    find_binary_in_path, get_tools_folder
from golismero.api.logger import Logger
from golismero.api.net import ConnectionSlot
from golismero.api.net.web_utils import WEB_SERVERS_VARS
from golismero.api.plugin import TestingPlugin

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET


#------------------------------------------------------------------------------
class XSSerPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def check_params(self):
        if not find_binary_in_path("xsser.py"):
            raise RuntimeError(
                "XSSer not found! You can download it from: "
                "http://xsser.sourceforge.net/")


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [URL]


    #--------------------------------------------------------------------------
    def run(self, info):

        if not isinstance(info, URL):
            return

        if not info.has_url_params and not info.has_post_params:
            return

        # Get user args
        user_args = shlex.split(Config.plugin_args.get("args", []))

        # Result info
        results = []

        with tempfile(prefix="tmpxss", suffix=".xml") as filename:

            args = [
                "--xml=%s" % filename,
                "--no-head",
                "--threads",
                "1"
            ]

            # Add the user args
            args.extend(user_args)

            if info.has_url_params:

                # Get payload for config injection point
                args.extend([
                    "-u",
                    "%s://%s" % (info.parsed_url.scheme, info.parsed_url.host),
                ])

                # When we want to try GET parameters, we must pass to xsser one by one.
                for param, value in info.parsed_url.query_params.iteritems():

                    # Not evaluate web server params
                    if param in WEB_SERVERS_VARS:
                        continue

                    # Prepare and reorder params
                    fixed_params = "&".join(["%s=%s" % (x, y) for x, y in info.parsed_url.query_params.iteritems() if x != param])

                    # Add param to text + fixed params
                    if fixed_params: # -> empty fixed params
                        params = "%s?%s&%s=" % (info.parsed_url.path, fixed_params, param)
                    else:
                        params = "%s?%s=" % (info.parsed_url.path, param)

                    # Prepary args for xsser
                    args.extend([
                        "-g",
                        params
                    ])

                    # Run xsser
                    if self.run_xsser(info.hostname, info.url, args):
                        results.extend(self.parse_xsser_result(info, filename))

            if info.has_post_params:
                args.extend([
                    "-u",
                    info.url,
                    "-p",
                    "&".join(
                        ["%s=%s" % (k, v)
                            for k, v in info.post_params.iteritems() if k not in WEB_SERVERS_VARS]
                    ),
                ])
                if self.run_xsser(info.hostname, info.url, args):
                    results.extend(self.parse_xsser_result(info, filename))

        if results:
            Logger.log("Found %s XSS vulnerabilities." % len(results))
        else:
            Logger.log_verbose("No XSS vulnerabilities found.")

        return results


    #--------------------------------------------------------------------------
    def run_xsser(self, hostname, url, args):
        """
        Run XSSer against the given target.

        :param url: The URL to be tested.
        :type url: str

        :param command: Path to the XSSer script.
        :type command: str

        :param args: The arguments to pass to XSSer.
        :type args: list

        :return: True id successful, False otherwise.
        :rtype: bool
        """

        Logger.log("Launching XSSer against: %s" % url)
        Logger.log_more_verbose("XSSer arguments: %s" % " ".join(args))

        xsser_script = join(get_tools_folder(), "xsser", "xsser.py")

        with ConnectionSlot(hostname):
            t1 = time()
            code = run_external_tool(xsser_script, args, callback=Logger.log_verbose)
            t2 = time()

        if code:
            Logger.log_error("XSSer execution failed, status code: %d" % code)
            return False
        Logger.log("XSSer scan finished in %s seconds for target: %s" % (t2 - t1, url))
        return True


    #--------------------------------------------------------------------------
    def get_subnode_text(self, node, childname, defaulvalue = None):
        """
        Get the subnode text.

        :param node: XML tree element.
        :type node: Element

        :param childname: Child node name.
        :type childname: str

        :param defaultvalue:
            Default value to return if child node doesn't exist.
        :type defaultvalue: str | None

        :return: Child node's text.
        :rtype: str | None
        """
        try:
            return node.find(childname).text
        except Exception:
            pass
        return defaulvalue


    #--------------------------------------------------------------------------
    def parse_xsser_result(self, target, filename):
        """
        Convert the result to GoLismero data model.

        :param target: Dectected URL.
        :type target: URL

        :param filename: Path to scan results file generated by XSSer.
        :type filename: str

        :return: Scan results.
        :rtype: list(XSSInjection)
        """
        result = []
        try:
            tree = ET.parse(filename)
            scan = tree.getroot()

            # Get the count of successful injections.
            # Abort if no injections were successful.
            node = scan.find('.//abstract/injections/successful')
            if node is None:
                return result
            successcount = int(node.text)
            if successcount <= 0:
                return result

            # Get the results.
            for node in scan.findall(".//results/attack"):

                _injection = self.get_subnode_text(node, "injection", None)
                if _injection is None:
                    continue

                _browsers = self.get_subnode_text(node, "browsers", "IE")
                _method   = self.get_subnode_text(node, "method",   "GET")

                url = URL(url = target.url,
                          method = _method,
                          post_params = target.post_params if _method == "POST" else None,
                          referer = target.referer)
                vul = XSS(url,
                          vulnerable_params = {"injection":_injection},
                          injection_point = XSS.INJECTION_POINT_URL,
                          injection_type = "XSS",
                          )
                vul.description += "\n\nBrowsers: %s\n" % _browsers
                result.append(vul)

        except Exception, e:
            tb = format_exc()
            Logger.log_error(str(e))
            Logger.log_error_more_verbose(tb)

        return result
