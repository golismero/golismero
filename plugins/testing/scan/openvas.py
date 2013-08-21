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

from golismero.api.config import Config
from golismero.api.data.db import Database
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.data.vulnerability import Vulnerability
from golismero.api.logger import Logger
from golismero.api.plugin import TestingPlugin, ImportPlugin

from threading import Event
from traceback import format_exc
from functools import partial

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

# Import the OpenVAS libraries from the plugin data folder.
import os, sys
_lib_path = os.path.abspath(os.path.split(__file__)[0])
if _lib_path not in sys.path:
    sys.path.insert(0, _lib_path)
from openvas_lib import VulnscanManager, VulnscanException


#------------------------------------------------------------------------------
# TODO: maybe polish up this class and add it to the API, see #64
class OpenVASProgress(object):
    def __init__(self, func):
        self.func = func
        self.previous = None
    def __call__(self, progress):
        if self.previous != progress:
            self.previous = progress
            self.func(progress)


#------------------------------------------------------------------------------
class OpenVASPlugin(TestingPlugin):


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [IP]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Synchronization object to wait for completion.
        m_event = Event()

        # Get the config.
        m_user      = Config.plugin_args["user"]
        m_password  = Config.plugin_args["password"]
        m_host      = Config.plugin_args["host"]
        m_port      = Config.plugin_args["port"]
        m_timeout   = Config.plugin_args["timeout"]
        m_profile   = Config.plugin_args["profile"]

        # Sanitize the port and timeout.
        try:
            m_port = int(m_port)
        except Exception:
            m_port = 9390
        if m_timeout.lower().strip() in ("inf", "infinite", "none"):
            m_timeout = None
        else:
            try:
                m_timeout = int(m_timeout)
            except Exception:
                m_timeout = None

        # Connect to the scanner.
        try:
            m_scanner = VulnscanManager(m_host, m_user, m_password, m_port, m_timeout)
        except VulnscanException, e:
            t = format_exc()
            Logger.log_error("Error connecting to OpenVAS, aborting scan!")
            #Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(t)
            return

        # Launch the scanner.
        m_scan_id, m_target_id = m_scanner.launch_scan(
            target = info.address,
            profile = m_profile,
            callback_end = partial(lambda x: x.set(), m_event),
            callback_progress = OpenVASProgress(self.update_status)
        )
        Logger.log_more_verbose("OpenVAS task ID: %s" % m_scan_id)

        # Wait for completion.
        m_event.wait()

        try:

            # Get the scan results.
            m_openvas_results = m_scanner.get_results(m_scan_id)

            # Clear the info

            m_scanner.delete_scan(m_scan_id)
            m_scanner.delete_target(m_target_id)

            # Convert the scan results to the GoLismero data model.
            return self.parse_results(m_openvas_results, info)
        except Exception,e:
            t = format_exc()
            Logger.log_error_verbose("Error parsing OpenVAS results: %s" % str(e))
            Logger.log_error_more_verbose(t)
        finally:

            # Clean up.
            try:
                m_scanner.delete_scan(m_scan_id)
            except Exception:
                pass   # XXX FIXME #135


    #----------------------------------------------------------------------
    @staticmethod
    def parse_results(openvas_results, ip = None):
        """
        Convert the OpenVAS scan results to the GoLismero data model.

        :param openvas_results: OpenVAS scan results.
        :type openvas_results: list(OpenVASResult)

        :param ip: (Optional) IP address to link the vulnerabilities to.
        :type ip: IP | None

        :returns: Scan results converted to the GoLismero data model.
        :rtype: list(Data)
        """

        # This is where we'll store the results.
        results = []

        # Remember the hosts we've seen so we don't create them twice.
        hosts_seen = {}

        LEVELS_CORRESPONDENCES = {
            'debug' : 'low',
            'log'   : 'informational',
            'low'   : "low",
            'medium': 'middle',
            'high'  : "high",
        }

        # For each OpenVAS result...
        for opv in openvas_results:
            try:

                # Get the host.
                host = opv.host

                # Get or create the vulnerable resource.
                target = ip
                if host in hosts_seen:
                    target = hosts_seen[host]
                elif not ip or ip.address != host:
                    try:
                        target = IP(host)
                    except ValueError:
                        target = Domain(host)
                    hosts_seen[host] = target
                    results.append(target)

                # Get the threat level.
                try:
                    level = opv.threat.lower()
                except Exception:
                    level = "informational"

                # Get the metadata.
                nvt = opv.nvt
                ##references = nvt.xrefs
                ##cvss = nvt.cvss
                ##cve = nvt.cve
                ##vulnerability_type = nvt.category

                # Get the vulnerability description.
                description = opv.description
                if not description:
                    description = nvt.description
                    if not description:
                        description = nvt.summary
                        if not description:
                            description = "A vulnerability has been found."
                if opv.notes:
                    description += "\n" + "\n".join(
                        " - " + note.text
                        for note in opv.notes
                    )

                # Create the vulnerability instance.
                vuln = Vulnerability(
                    level       = LEVELS_CORRESPONDENCES[level.lower()],
                    description = description,
                    ##cvss        = cvss,
                    ##cve         = cve,
                    ##references  = references.split("\n"),
                )
                ##vuln.vulnerability_type = vulnerability_type

                # Link the vulnerability to the resource.
                if target is not None:
                    target.add_vulnerability(vuln)

            # Skip on error.
            except Exception, e:
                t = format_exc()
                Logger.log_error_verbose("Error parsing OpenVAS results: %s" % str(e))
                Logger.log_error_more_verbose(t)
                continue

            # Add the vulnerability.
            results.append(vuln)

        # Return the converted results.
        return results


#------------------------------------------------------------------------------
class OpenVASImportPlugin(ImportPlugin):


    #--------------------------------------------------------------------------
    def is_supported(self, input_file):
        if input_file and input_file.lower().endswith(".xml"):
            with open(input_file, "rU") as fd:
                line = fd.readline()
                return line.startswith('<report extension="xml" id="')
        return False


    #--------------------------------------------------------------------------
    def import_results(self, input_file):
        try:
            xml_results       = etree.parse(input_file)
            openvas_results   = VulnscanManager.transform(xml_results.getroot())
            golismero_results = OpenVASPlugin.parse_results(openvas_results)
            if golismero_results:
                Database.async_add_many(golismero_results)
        except Exception, e:
            Logger.log_error(
                "Could not load OpenVAS results from file: %s" % input_file)
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(format_exc())
        else:
            if golismero_results:
                Logger.log(
                    "Loaded %d results from file: %s" %
                    (len(golismero_results), input_file)
                )
            else:
                Logger.log_verbose("No data found in file: %s" % input_file)
