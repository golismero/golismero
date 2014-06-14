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

import os.path

from functools import partial
from threading import Event
from traceback import format_exc
from warnings import warn
from time import sleep

try:
    import cPickle as Pickler
except ImportError:
    import pickle as Pickler

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

from openvas_lib import VulnscanManager, VulnscanException, VulnscanVersionError, VulnscanAuditNotFoundError
from openvas_lib.data import OpenVASResult

from golismero.api.data import vulnerability
from golismero.api.data.vulnerability import Vulnerability, \
    UncategorizedVulnerability  # noqa
from golismero.api.logger import Logger
from golismero.api.config import Config
from golismero.api.data.db import Database
from golismero.api.data.resource.ip import IP
from golismero.api.data.resource.domain import Domain
from golismero.api.net.web_utils import parse_url
from golismero.api.plugin import TestingPlugin, ImportPlugin


#------------------------------------------------------------------------------
# OpenVAS plugin extra files.
base_dir = os.path.split(os.path.abspath(__file__))[0]
openvas_dir = os.path.join(base_dir, "openvas_plugin")
openvas_db = os.path.join(openvas_dir, "openvas.db")
del base_dir


#------------------------------------------------------------------------------
# Helper function to load all vulnerability types.
def load_vulnerability_types():
    data_types = []

    # Look for Python files in golismero/api/data.
    api_data = os.path.dirname(vulnerability.__file__)
    api_data = os.path.abspath(api_data)
    for root, folders, files in os.walk(api_data):
        for name in files:
            if name.startswith("_") or not name.endswith(".py"):
                continue

            # Get the module name from its file path.
            name = name[:-3]
            name = os.path.join(root, name)
            name = os.path.abspath(name)
            name = name[len(api_data):]
            if name.startswith(os.path.sep):
                name = name[1:]
            name = name.replace(os.path.sep, ".")
            name = "golismero.api.data.vulnerability." + name

            # Load the module and extract all its data types.
            module = __import__(name, globals(), locals(), ['*'])
            for name in dir(module):
                if name.startswith("_") or name == "Vulnerability":
                    continue
                clazz = getattr(module, name)
                if isinstance(clazz, type) and \
                        issubclass(clazz, Vulnerability) and \
                                clazz not in data_types:
                    data_types.append(clazz)
                    globals()[name] = clazz

    return data_types

load_vulnerability_types()


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
    def get_accepted_types(self):
        return [IP]


    #--------------------------------------------------------------------------
    def run(self, info):

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

        # Maps of OpenVAS levels to GoLismero levels.
        LEVELS = {
            'debug': 'informational',
            'log': 'informational',
            'low': "low",
            'medium': 'middle',
            'high': "high",
        }
        RISKS = {
            'none': 0,
            'debug': 0,
            'log': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }

        # Do we have the OpenVAS plugin database?
        if not os.path.exists(openvas_db):
            Logger.log_error(
                "OpenVAS plugin not initialized, please run setup.py")
            return

        # Load the database.
        with open(openvas_db, "rb") as f:
            use_openvas_db = Pickler.load(f)

        # Get the configuration.
        import_log = Config.audit_config.boolean(
            Config.plugin_args.get("import_log", "no"))
        import_debug = Config.audit_config.boolean(
            Config.plugin_args.get("import_debug", "no"))

        # For each OpenVAS result...
        for opv in openvas_results:
            try:

                # Get the host.
                host = opv.host

                # Skip if we don't have a target host.
                if host is None:
                    continue

                # Get the threat level.
                threat = getattr(opv, "threat", "log").lower()

                # Discard log and debug entries, keep only the vulnerabilities.
                if threat == "log" and not import_log:
                    continue
                if threat == "debug" and not import_debug:
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

                # Get the vulnerability description.
                description = opv.description
                if not description:
                    description = nvt.description
                    if not description:
                        description = nvt.summary
                        if not description:
                            description = None

                # Extract the relevant information from the results.
                nvt       = opv.nvt
                vid       = opv.id
                oid       = int(nvt.oid.split(".")[-1])
                name      = getattr(nvt, "name", None)
                cvss_base = getattr(nvt, "cvss_base", None)
                level     = LEVELS.get(threat, "informational")
                risk      = RISKS.get(
                    getattr(opv.nvt, "risk_factor", "none").lower(), 0)

                # Extract the CVEs and Bugtraq IDs.
                cve = nvt.cve.split(", ") if nvt.cve else []
                if "NOCVE" in cve:
                    cve.remove("NOCVE")
                bid = []
                if nvt.bid:
                    bid.extend("BID-" + x for x in nvt.bid.split(", "))
                if nvt.bugtraq:
                    bid.extend("BID-" + x for x in nvt.bugtraq.split(", "))
                if "NOBID" in bid:
                    cve.remove("NOBID")

                # Extract the notes and add them to the description text.
                if opv.notes and description is not None:
                    description += "\n" + "\n".join(
                        " - " + note.text
                        for note in opv.notes
                    )

                # Extract the reference URLs from the description text.
                references = []
                if description is not None:
                    p = description.find("URL:")
                    while p >= 0:
                        p += 4
                        q2 = description.find("\n", p)
                        q1 = description.find(",", p, q2)
                        if q1 > p:
                            q = q1
                        else:
                            q = q2
                        if q < p:
                            q = len(description)
                        url = description[p:q].strip()
                        try:
                            url = parse_url(url).url
                            references.append(url)
                        except Exception:
                            Logger.log_error(format_exc())
                            pass
                        p = description.find("URL:", q)

                # Prepare the vulnerability properties.
                kwargs = {
                    "title":        name,
                    "description":  description,
                    "references":   references,
                    "level":        level,
                    "risk":         risk,
                    "severity":     risk,
                    "impact":       risk,
                    "cvss_base":    cvss_base,
                    "cve":          cve,
                    "bid":          bid,
                    "tool_id":      "openvas_plugin_%s" % oid,
                    "custom_id":    vid,
                }

                # If we have the OpenVAS plugin database, look up the plugin ID
                # that reported this vulnerability and create the vulnerability
                # using a specific class. Otherwise use the vulnerability class
                # for uncategorized vulnerabilities.
                classname = "UncategorizedVulnerability"
                if oid in use_openvas_db:
                    classname = use_openvas_db[oid][0][0]

                # Create the Vulnerability object.
                try:
                    clazz = globals()[classname]
                    vuln  = clazz(target, **kwargs)
                except Exception, e:
                    t = format_exc()
                    Logger.log_error_more_verbose(
                        "Could not load vulnerability of type: %s" % classname)
                    Logger.log_error_more_verbose(t)
                    vuln = UncategorizedVulnerability(target, **kwargs)
                results.append(vuln)

            # Skip this result on error.
            except Exception, e:
                t = format_exc()
                Logger.log_error_verbose(
                    "Error parsing OpenVAS results: %s" % str(e))
                Logger.log_error_more_verbose(t)

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
