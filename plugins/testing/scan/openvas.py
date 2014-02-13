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

import os.path
import sys
import yaml

from functools import partial
from threading import Event
from traceback import format_exc
from warnings import warn
from time import sleep

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

from openvas_lib import VulnscanManager, VulnscanException, VulnscanVersionError, VulnscanAuditNotFoundError
from openvas_lib.data import OpenVASResult


from golismero.api.config import Config
from golismero.api.data.db import Database
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.data.vulnerability import UncategorizedVulnerability, Vulnerability
from golismero.api.data.vulnerability.infrastructure.outdated_platform import *  # noqa
from golismero.api.logger import Logger
from golismero.api.net.scraper import extract_from_text
from golismero.api.plugin import TestingPlugin, ImportPlugin


#------------------------------------------------------------------------------
# OpenVAS plugin extra files.
base_dir = os.path.split(os.path.abspath(__file__))[0]
openvas_dir = os.path.join(base_dir, "openvas_plugin")
openvas_db = os.path.join(openvas_dir, "openvas.sqlite3")
openvas_yaml = os.path.join(openvas_dir, "categories.yaml")
del base_dir


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


    #--------------------------------------------------------------------------
    def check_params(self):

        # Check the parameters.
        try:
            m_user = Config.plugin_args["user"]
            m_password = Config.plugin_args["password"]
            m_host = Config.plugin_args["host"]
            m_port = int(Config.plugin_args["port"])
            m_timeout = Config.plugin_args["timeout"]
            m_profile = Config.plugin_args["profile"]

            assert m_user,     "Missing username"
            assert m_password, "Missing password"
            assert m_host,     "Missing hostname"
            assert m_profile,  "Missing scan profile"
            assert 0 < m_port < 65536, "Missing or wrong port number"
            if m_timeout.lower().strip() in ("inf", "infinite", "none"):
                m_timeout = None
            else:
                m_timeout = int(m_timeout)
                assert m_timeout > 0, "Wrong timeout value"

        except Exception, e:
            raise ValueError(str(e))

        # Connect to the scanner.
        try:
            VulnscanManager(m_host, m_user, m_password, m_port, m_timeout)
        except VulnscanVersionError:
            raise RuntimeError(
                "Remote host is running an unsupported version of OpenVAS."
                " Only OpenVAS 6 is currently supported.")
        except VulnscanException, e:
            raise RuntimeError(str(e))

        # Check the plugin database exists.
        if not os.path.exists(openvas_db):
            warn("OpenVAS plugin not initialized, please run setup.py")


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [IP]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        # Checks if connection was not set as down
        if not self.state.check("connection_down"):

            # Synchronization object to wait for completion.
            m_event = Event()

            # Get the config.
            m_user = Config.plugin_args["user"]
            m_password = Config.plugin_args["password"]
            m_host = Config.plugin_args["host"]
            m_port = Config.plugin_args["port"]
            m_timeout = Config.plugin_args["timeout"]
            m_profile = Config.plugin_args["profile"]

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
                Logger.log_more_verbose(
                    "Connecting to OpenVAS server at %s:%d" % (m_host, m_port))
                m_scanner = VulnscanManager(
                    m_host, m_user, m_password, m_port, m_timeout)

            except VulnscanVersionError:
                Logger.log_error(
                    "Remote host is running an unsupported version of OpenVAS."
                    " Only OpenVAS 6 is currently supported.")

                # Set the openvas connection as down and remember it.
                self.state.put("connection_down", True)
                return

            except VulnscanException, e:
                t = format_exc()
                Logger.log_error("Error connecting to OpenVAS, aborting scan!")
                Logger.log_error_more_verbose(t)

                # Set the openvas connection as down and remember it.
                self.state.put("connection_down", True)
                return

            m_scan_id = None
            m_target_id = None
            try:
                # Launch the scanner.
                m_scan_id, m_target_id = m_scanner.launch_scan(
                    target=info.address,
                    profile=m_profile,
                    callback_end=partial(lambda x: x.set(), m_event),
                    callback_progress=OpenVASProgress(self.update_status)
                )
                Logger.log_more_verbose("OpenVAS task ID: %s" % m_scan_id)

                # Wait for completion.
                m_event.wait()

                # Get the scan results.
                m_openvas_results = m_scanner.get_results(m_scan_id)

            except Exception, e:
                t = format_exc()
                Logger.log_error_verbose(
                    "Error parsing OpenVAS results: %s" % str(e))
                Logger.log_error_more_verbose(t)
                return

            finally:

                # Clean up.
                if m_scan_id:
                    # Stop the scan
                    for i in xrange(3):
                        try:

                            # Clear the info
                            m_scanner.stop_audit(m_scan_id)

                            # If not error, break
                            break
                        except VulnscanAuditNotFoundError:
                            break
                        except Exception, e:
                            sleep(0.1)
                            Logger.log_error_more_verbose(
                                "Error while stopping scan ID: %s. "
                                "Attempt %s. Error: %s" %
                                (str(m_scan_id), str(i)), e.message)
                            continue

                    # Delete the scan
                    for i in xrange(3):
                        try:

                            # Clear the info
                            m_scanner.delete_scan(m_scan_id)

                            # If not error, break
                            break
                        except Exception, e:
                            sleep(0.1)
                            Logger.log_error_more_verbose(
                                "Error while deleting scan ID: %s. "
                                "Attempt %s. Error: %s" %
                                (str(m_scan_id), str(i)), e.message)
                            continue

                if m_target_id:
                    # Remove the target
                    for i in xrange(3):
                        try:

                            # Clear the info
                            m_scanner.delete_target(m_target_id)

                            # If not error, break
                            break
                        except Exception, e:
                            sleep(0.1)
                            Logger.log_error_more_verbose(
                                "Error while deleting target ID: %s. "
                                "Attempt %s. Error: %s" %
                                (str(m_target_id), str(i)), e.message)
                            continue

        # Convert the scan results to the GoLismero data model.
        return self.parse_results(m_openvas_results, info)


    #--------------------------------------------------------------------------
    @staticmethod
    def parse_results(openvas_results, ip=None):
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

        # Map of OpenVAS levels to GoLismero levels.
        OPV_LEVELS_TO_GLM_LEVELS = {
            'debug': 'informational',
            'log': 'informational',
            'low': "low",
            'medium': 'middle',
            'high': "high",
        }

        RISKS = {
            'debug': 0,
            'log': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }

        # Do we have the OpenVAS plugin database?
        use_openvas_db = os.path.exists(openvas_db)
        if not use_openvas_db:
            Logger.log_error(
                "OpenVAS plugin not initialized, please run setup.py")
        else:

            # Load the database using the Django ORM.
            from standalone.conf import settings
            try:
                settings = settings(
                    DATABASES = {
                        'default': {
                            'ENGINE': 'django.db.backends.sqlite3',
                            'NAME': '%s' % openvas_db,
                        }
                    },
                )
            except RuntimeError:
                Logger.log("Django backend previously loaded.")

            # Load the ORM model.
            sys.path.insert(0, openvas_dir)
            try:
                from models import Families, Plugin
            finally:
                sys.path.remove(openvas_dir)

            # Load the categories.
            CATEGORIES = {}
            if os.path.exists(openvas_yaml):
                try:
                    CATEGORIES = yaml.load( open(openvas_yaml, 'rU'),
                                            Loader=Loader )
                except Exception, e:
                    tb = format_exc()
                    Logger.log_error_verbose(
                        "Failed to load categories, reason: %s" % str(e))
                    Logger.log_error_more_verbose(tb)
            else:
                Logger.log_error(
                    "Missing OpenVAS categories file: %s" % openvas_yaml)

        # For each OpenVAS result...
        for opv in openvas_results:
            try:

                # XXX why would this happen?
                if not isinstance(opv, OpenVASResult):
                    warn("Expected OpenVASResult, got %r instead" % type(opv),
                         RuntimeWarning)
                    continue

                # Get the host.
                host = opv.host

                if host is None:
                    continue

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
                cvss = nvt.cvss_base
                cvss_vector = nvt.cvss_base_vector
                cve = nvt.cve.split(", ") if nvt.cve else []
                oid = nvt.oid
                name = nvt.name
                risk = RISKS.get(nvt.risk_factor.lower(), 0)

                # Get the vulnerability description.
                description = opv.description
                if not description:
                    description = nvt.description
                    if not description:
                        description = nvt.summary
                        if not description:
                            description = None
                if opv.notes:
                    description += "\n" + "\n".join(
                        " - " + note.text
                        for note in opv.notes
                    )

                # Get the reference URLs.
                references = extract_from_text(description)

                # Prepare the vulnerability properties.
                kwargs = {
                    "level": OPV_LEVELS_TO_GLM_LEVELS[level.lower()],
                    "description": description,
                    "references": references,
                    "cve": cve,
                    "risk": risk
                }
                if cvss_vector:
                    kwargs["cvss_vector"] = cvss_vector
                elif cvss:
                    kwargs["cvss_base"] = cvss
                if name:
                    kwargs["title"] = name

                # If we have the OpenVAS plugin database, look up the plugin ID
                # that reported this vulnerability and create the vulnerability
                # using a specific class. Otherwise use the vulnerability class
                # for uncategorized vulnerabilities.
                clazz = UncategorizedVulnerability
                if use_openvas_db and oid:
                    oid_spt = oid.split(".")
                    if len(oid_spt) > 0:
                        l_plugin_id = oid_spt[-1]
                        kwargs["tool_id"] = l_plugin_id
                        try:
                            l_family = Plugin.objects.get(
                                plugin_id = l_plugin_id).family_id
                            l_family = l_family.strip()

                            if l_plugin_id in CATEGORIES:
                                clazz = globals()[CATEGORIES[l_plugin_id]]

                            elif l_family in CATEGORIES:
                                clazz = globals()[CATEGORIES[l_family]]
                        except Exception, e:
                            tb = format_exc()
                            Logger.log_error_verbose(
                                "Failed to find category %r, reason: %s" %
                                (l_plugin_id, str(e)))
                            Logger.log_error_more_verbose(tb)

                # Create the vulnerability instance.
                vuln = clazz(**kwargs)

                # Link the vulnerability to the resource.
                if target is not None:
                    target.add_vulnerability(vuln)

                # Add the vulnerability.
                results.append(vuln)

            # Skip on error.
            except Exception, e:
                t = format_exc()
                Logger.log_error_verbose(
                    "Error parsing OpenVAS results: %s" % str(e))
                Logger.log_error_more_verbose(t)
                continue

        # Return the converted results.
        return results


#------------------------------------------------------------------------------
class OpenVASImportPlugin(ImportPlugin):


    #--------------------------------------------------------------------------
    def is_supported(self, input_file):
        if input_file and input_file.lower().endswith(".xml"):
            with open(input_file, "rU") as fd:
                line = fd.readline()
                is_ours = line.startswith('<report')
            if is_ours:
                if not os.path.exists(openvas_db):
                    warn("OpenVAS plugin not initialized, please run setup.py")
                return True
        return False


    #--------------------------------------------------------------------------
    def import_results(self, input_file):
        try:
            xml_results = etree.parse(input_file)
            xml_root = xml_results.getroot()
            openvas_results = VulnscanManager.transform(xml_root)
            golismero_results = OpenVASPlugin.parse_results(openvas_results)
            if golismero_results:
                Database.async_add_many(golismero_results)
        except Exception, e:
            fmt = format_exc()
            Logger.log_error(
                "Could not load OpenVAS results from file: %s" % input_file)
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(fmt)
        else:
            if golismero_results:
                data_count = len(golismero_results)
                vuln_count = sum(
                    1 for x in golismero_results
                    if x.is_instance(Vulnerability)
                )
                if vuln_count == 0:
                    vuln_msg = ""
                elif vuln_count == 1:
                    vuln_msg = " (1 vulnerability)"
                else:
                    vuln_msg = " (%d vulnerabilities)" % vuln_count
                Logger.log(
                    "Loaded %d %s%s from file: %s" %
                    (data_count, "results" if data_count != 1 else "result",
                     vuln_msg, input_file)
                )
            else:
                Logger.log_error("No results found in file: %s" % input_file)
