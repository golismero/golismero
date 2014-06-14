#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

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
import re

from os.path import join
from time import time
from traceback import format_exc

from golismero.api.config import Config
from golismero.api.data.resource.url import URL
from golismero.api.data.vulnerability.injection.sql import SQLInjection
from golismero.api.external import run_external_tool, find_binary_in_path, tempdir, get_tools_folder
from golismero.api.logger import Logger
from golismero.api.net import ConnectionSlot
from golismero.api.net.web_utils import WEB_SERVERS_VARS
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
class SQLMapTestingPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def check_params(self):
        if not find_binary_in_path("sqlmap.py"):
            raise RuntimeError(
                "SQLMap not found!"
                " You can download it from: http://sqlmap.org/")


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [URL]


    #--------------------------------------------------------------------------
    def run(self, info):

        if not info.has_url_params and not info.has_post_params:
            return

        # Result info
        results = []

        # Get user args
        user_args = shlex.split(Config.plugin_args["args"])

        with tempdir() as output_dir:

            # Basic command line
            args = [
                "-u",
                info.url,
                "--batch",
                "--output-dir",
                output_dir
            ]

            # Add the user args
            args.extend(user_args)

            #
            # GET Parameters injection
            #
            if info.has_url_params:

                args.extend([
                    "-p",
                    ",".join([x for x in info.url_params if x not in WEB_SERVERS_VARS]),
                ])

                r = self.make_injection(info.url, args)
                if r:
                    results.extend(self.parse_sqlmap_results(info, output_dir))

            #
            # POST Parameters injection
            #
            if info.has_post_params:
                args.extend([
                    "--data",
                    "&".join(["%s=%s" % (k, v) for k, v in info.post_params.iteritems() if k not in WEB_SERVERS_VARS])
                ])

                r = self.make_injection(info.url, args)
                if r:
                    results.extend(self.parse_sqlmap_results(info, output_dir))

        if results:
            Logger.log("Found %s SQL injection vulnerabilities." % len(results))
        else:
            Logger.log("No SQL injection vulnerabilities found.")

        return results


    #--------------------------------------------------------------------------
    def make_injection(self, target, args):
        """
        Run SQLMap against the given target.

        :param target: URL to scan.
        :type target: URL

        :param args: Arguments to pass to SQLMap.
        :type args: list(str)

        :return: True on success, False on failure.
        :rtype: bool
        """

        Logger.log("Launching SQLMap against: %s" % target)
        Logger.log_more_verbose("SQLMap arguments: %s" % " ".join(args))

        sqlmap_script = join(get_tools_folder(), "sqlmap", "sqlmap.py")

        with ConnectionSlot(target):
            t1 = time()
            code = run_external_tool(sqlmap_script, args,
                                     callback=Logger.log_verbose)
            t2 = time()

        if code:
            Logger.log_error("SQLMap execution failed, status code: %d" % code)
            return False
        Logger.log(
            "SQLMap scan finished in %s seconds for target: %s"
            % (t2 - t1, target))
        return True


    #--------------------------------------------------------------------------
    @staticmethod
    def parse_sqlmap_results(info, output_dir):
        """
        Convert the output of a SQLMap scan to the GoLismero data model.

        :param info: Data object to link all results to (optional).
        :type info: URL

        :param output_filename: Path to the output filename.
            The format should always be XML.
        :type output_filename:

        :returns: Results from the SQLMap scan.
        :rtype: list(Data)
        """


        # Example output file format:
        #
        # ---
        # Place: GET
        # Parameter: feria
        #     Type: boolean-based blind
        #     Title: AND boolean-based blind - WHERE or HAVING clause
        #     Payload: feria=VG13' AND 8631=8631 AND 'VWDy'='VWDy&idioma=es&tipouso=I
        # ---
        # web application technology: Tomcat 5.0, JSP, Servlet 2.5
        # back-end DBMS: Oracle
        # banner:    'Oracle Database 11g Release 11.2.0.3.0 - 64bit Production'


        results = []

        # Get result file
        log_file = join(output_dir, info.parsed_url.host, "log")

        # Parse
        try:
            with open(log_file, "rU") as f:
                text = f.read()

                # Split injections
                m_banner     = None
                m_backend    = None
                m_technology = None
                tmp          = []
                for t in text.split("---"):
                    #
                    # Is ijection details?
                    #
                    l_injectable_place  = re.search("(Place: )([a-zA-Z]+)", t)
                    if l_injectable_place:
                        # Common params
                        l_inject_place   = l_injectable_place.group(2)
                        l_inject_param   = re.search("(Parameter: )([\w\_\-]+)", t).group(2)
                        l_inject_type    = re.search("(Type: )([\w\- ]+)", t).group(2)
                        l_inject_title   = re.search("(Title: )([\w\- ]+)", t).group(2)
                        l_inject_payload = re.search(r"""(Payload: )([\w\- =\'\"\%\&\$\)\(\?\¿\*\@\!\|\/\\\{\}\[\]\<\>\_\:,;\.]+)""", t).group(2)

                        url = URL(info.url, method=l_inject_place, post_params=info.post_params, referer=info.referer)
                        v = SQLInjection(url,
                            title = "SQL Injection Vulnerability - " + l_inject_title,
                            vulnerable_params = { l_inject_param : l_inject_payload },
                            injection_point = SQLInjection.str2injection_point(l_inject_place),
                            injection_type = l_inject_type,
                        )
                        tmp.append(v)

                    # Get banner info
                    if not m_banner:
                        m_banner = re.search("(banner:[\s]*)(')([\w\- =\'\"\%\&\$\)\(\?\¿\*\@\!\|\/\\\{\}\[\]\<\>\_\.\:,;]*)(')", t)
                        if m_banner:
                            m_banner     = m_banner.group(3)
                            m_backend    = re.search("(back-end DBMS:[\s]*)([\w\- =\'\"\%\&\$\)\(\?\¿\*\@\!\|\/\\\{\}\[\]\<\>\_\.\:,;]+)", t).group(2)
                            m_technology = re.search("(web application technology:[\s]*)([\w\- =\'\"\%\&\$\)\(\?\¿\*\@\!\|\/\\\{\}\[\]\<\>\_\.\:,;]+)", t).group(2)

                # If banner was found, fill the vulns with these info
                for v in tmp:
                    if m_banner:
                        v.description = "Banner: %s\n\n%s\n%s" % (m_backend, m_backend, m_technology)

                    results.append(v)

        # On error, log the exception.
        except Exception, e:
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(format_exc())

        return results
