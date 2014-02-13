#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: http://golismero-project.com
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
from golismero.api.data.resource.url import BaseUrl, Url
from golismero.api.data.vulnerability import UncategorizedVulnerability
from golismero.api.data.vulnerability.infrastructure.vulnerable_webapp \
     import VulnerableWebApp
from golismero.api.external import run_external_tool, find_binary_in_path, \
     find_cygwin_binary_in_path, tempfile, get_tools_folder
from golismero.api.logger import Logger
from golismero.api.net import ConnectionSlot
from golismero.api.net.scraper import extract_from_text
from golismero.api.net.web_utils import parse_url, urljoin
from golismero.api.plugin import ImportPlugin, TestingPlugin
from golismero.api.data.vulnerability.vuln_utils import extract_vuln_ids

from csv import reader
from os.path import abspath, join, exists, isfile, sep, split
from traceback import format_exc


#------------------------------------------------------------------------------
class NiktoPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def check_params(self):
        self.get_nikto()


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [BaseUrl]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        # Get the path to the Nikto scanner and the configuration file.
        nikto_script, config = self.get_nikto()

        # Build the command line arguments.
        # The -output argument will be filled by run_nikto.
        args = [
            "-host", info.hostname,
            "-ssl" if info.is_https else "-nossl",
            "-port", str(info.parsed_url.port),
            "-Format", "csv",
            "-ask", "no",
            "-nointeractive",
            ##"-useproxy",
        ]
        for option in ("Pause", "timeout", "Tuning", "Plugins"):
            value = Config.plugin_args.get(option.lower(), "")
            value = value.replace("\r", "")
            value = value.replace("\n", "")
            value = value.replace("\t", "")
            value = value.replace(" ", "")
            if value:
                args.extend(["-" + option, value])

        # Create a temporary output file.
        with tempfile(suffix = ".csv") as output:

            # Append the output file name to the arguments.
            args.append("-output")
            args.append(output)

            # If we need to set the proxy or the cookies, we'll have to create
            # a temporary config file with the modified settings, since there's
            # no way of passing these options through the command line.
            if Config.audit_config.proxy_addr or Config.audit_config.cookie:

                # Make sure we have a config file.
                if not config:
                    raise ValueError("Missing configuration file!")

                # Create a temporary config file.
                with tempfile(suffix = ".conf") as tmp_config:

                    # Open the original config file.
                    with open(config, "rU") as src:

                        # Open the new config file.
                        with open(tmp_config, "w") as dst:

                            # Copy the contents of the original config file.
                            dst.write( src.read() )

                            # Append the new settings.
                            proxy_addr = Config.audit_config.proxy_addr
                            if proxy_addr:
                                parsed = parse_url(proxy_addr)
                                dst.write("PROXYHOST=%s\n" % parsed.host)
                                dst.write("PROXYPORT=%s\n" % parsed.port)
                                if Config.audit_config.proxy_user:
                                    dst.write("PROXYUSER=%s\n" %
                                              Config.audit_config.proxy_user)
                                if Config.audit_config.proxy_pass:
                                    dst.write("PROXYPASS=%s\n" %
                                              Config.audit_config.proxy_pass)
                            cookie_dict = Config.audit_config.cookie
                            if cookie_dict:
                                cookie = ";".join(
                                    '"%s=%s"' % x
                                    for x in cookie_dict.iteritems()
                                )
                                dst.write("STATIC-COOKIE=%s\n" % cookie)

                    # Set the new config file.
                    args = ["-config", tmp_config] + args

                    # Run Nikto and parse the output.
                    return self.run_nikto(info, output, nikto_script, args)

            # Otherwise, just use the supplied config file.
            else:
                if config:
                    args = ["-config", config] + args

                # Run Nikto and parse the output.
                return self.run_nikto(info, output, nikto_script, args)


    #--------------------------------------------------------------------------
    def get_nikto(self):
        """
        Get the path to the Nikto scanner and the configuration file.

        :returns: Nikto scanner and configuration file paths.
        :rtype: tuple(str, str)

        :raises RuntimeError: Nikto scanner of config file not found.
        """

        # Get the path to the Nikto scanner.
        nikto_script = Config.plugin_args["exec"]
        if nikto_script and exists(nikto_script):
            nikto_dir = abspath(split(nikto_script)[0])
        else:
            nikto_dir = join(get_tools_folder(), "nikto")
            nikto_script = join(nikto_dir, "nikto.pl")
            if not nikto_script or not exists(nikto_script):
                nikto_script = find_binary_in_path("nikto")
                if not exists(nikto_script):
                    nikto_script = Config.plugin_args["exec"]
                    msg = "Nikto not found"
                    if nikto_script:
                        msg += ". File: %s" % nikto_script
                    Logger.log_error(msg)
                    raise RuntimeError(msg)

        # Get the path to the configuration file.
        config = Config.plugin_args.get("config", "nikto.conf")
        if not config:
            config = "nikto.conf"
        config = join(nikto_dir, config)
        config = abspath(config)
        if not isfile(config):
            config = Config.plugin_args.get("config", "nikto.conf")
            if not config:
                config = "nikto.conf"
            config = abspath(config)
            if not isfile(config):
                config = "/etc/nikto.conf"
                if not isfile(config):
                    msg = "Nikto config file not found"
                    if config:
                        msg += ". File: %s" % config
                    raise RuntimeError(msg)

        # Return the paths.
        return nikto_script, config


    #--------------------------------------------------------------------------
    def run_nikto(self, info, output_filename, command, args):
        """
        Run Nikto and convert the output to the GoLismero data model.

        :param info: Base URL to scan.
        :type info: BaseUrl

        :param output_filename: Path to the output filename.
            The format should always be CSV.
        :type output_filename: str

        :param command: Path to the Nikto script.
        :type command: str

        :param args: Arguments to pass to Nikto.
        :type args: list(str)

        :returns: Results from the Nikto scan.
        :rtype: list(Data)
        """

        # Get the Nikto directory.
        cwd = split(abspath(command))[0]

        # On Windows, we must run Perl explicitly.
        # Also it only works under Cygwin.
        if sep == "\\":
            perl = find_cygwin_binary_in_path("perl.exe")
            if not perl:
                Logger.log_error("Perl interpreter not found, cannot run Nikto!")
            args.insert(0, command)
            command = perl

        # Run Nikto and capture the text output.
        Logger.log("Launching Nikto against: %s" % info.hostname)
        Logger.log_more_verbose(
            "Nikto arguments: %s %s" % (command, " ".join(args)))
        with ConnectionSlot(info.hostname):
            code = run_external_tool(command, args, cwd = cwd,
                                     callback = Logger.log_verbose)

        # Log the output in extra verbose mode.
        if code:
            Logger.log_error("Nikto execution failed, status code: %d" % code)

        # Parse the results.
        results, vuln_count = self.parse_nikto_results(info, output_filename)

        # Log how many results we found.
        msg = (
            "Nikto found %d vulnerabilities for host: %s" % (
                vuln_count,
                info.hostname,
            )
        )
        if vuln_count:
            Logger.log(msg)
        else:
            Logger.log_verbose(msg)

        # Return the results.
        return results


    #--------------------------------------------------------------------------
    @staticmethod
    def parse_nikto_results(info, output_filename):
        """
        Convert the output of a Nikto scan to the GoLismero data model.

        :param info: Data object to link all results to (optional).
        :type info: BaseUrl

        :param output_filename: Path to the output filename.
            The format should always be CSV.
        :type output_filename:

        :returns: Results from the Nikto scan, and the vulnerability count.
        :rtype: list(Data), int
        """

        # Parse the scan results.
        # On error log the exception and continue.
        results = []
        vuln_count = 0
        hosts_seen = set()
        urls_seen = {}
        try:
            with open(output_filename, "rU") as f:
                csv_reader = reader(f)
                for row in csv_reader:
                    try:

                        # Each row (except for the first) has always
                        # the same 7 columns, but some may be empty.
                        if len(row) < 7:
                            continue
                        host, ip, port, vuln_tag, method, path, text = row[:7]

                        # Report domain names and IP addresses.
                        if (
                            (info is None or host != info.hostname) and
                            host not in hosts_seen
                        ):
                            hosts_seen.add(host)
                            if host in Config.audit_scope:
                                results.append( Domain(host) )
                        if ip not in hosts_seen:
                            hosts_seen.add(ip)
                            if ip in Config.audit_scope:
                                results.append( IP(ip) )

                        # Skip rows not informing of vulnerabilities.
                        if not vuln_tag:
                            continue

                        # Calculate the vulnerable URL.
                        if info is not None:
                            target = urljoin(info.url, path)
                        else:
                            if port == 443:
                                target = urljoin("https://%s/" % host, path)
                            else:
                                target = urljoin("http://%s/" % host, path)

                        # Skip if out of scope.
                        if target not in Config.audit_scope:
                            continue

                        # Report the URLs.
                        if (target, method) not in urls_seen:
                            url = Url(target, method)
                            urls_seen[ (target, method) ] = url
                            results.append(url)
                        else:
                            url = urls_seen[ (target, method) ]

                        # Get the reference URLs.
                        refs = extract_from_text(text)
                        refs.difference_update(urls_seen.itervalues())

                        # Report the vulnerabilities.
                        if vuln_tag == "OSVDB-0":
                            kwargs = {"level": "informational"}
                        else:
                            kwargs = extract_vuln_ids(
                                "%s: %s" % (vuln_tag, text))
                        kwargs["description"] = text if text else None
                        kwargs["references"]  = refs
                        if "osvdb" in kwargs and "OSVDB-0" in kwargs["osvdb"]:
                            tmp = list(kwargs["osvdb"])
                            tmp.remove("OSVDB-0")
                            if tmp:
                                kwargs["osvdb"] = tuple(tmp)
                            else:
                                del kwargs["osvdb"]
                        if vuln_tag == "OSVDB-0":
                            vuln = UncategorizedVulnerability(**kwargs)
                            vuln.add_resource(url)
                        else:
                            vuln = VulnerableWebApp(url, **kwargs)
                        results.append(vuln)
                        vuln_count += 1

                    # On error, log the exception and continue.
                    except Exception, e:
                        Logger.log_error_verbose(str(e))
                        Logger.log_error_more_verbose(format_exc())

        # On error, log the exception.
        except Exception, e:
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(format_exc())

        # Return the results and the vulnerability count.
        return results, vuln_count


#------------------------------------------------------------------------------
class NiktoImportPlugin(ImportPlugin):


    #--------------------------------------------------------------------------
    def is_supported(self, input_file):
        if input_file and input_file.lower().endswith(".csv"):
            with open(input_file, "rU") as fd:
                return "Nikto" in fd.readline()
        return False


    #--------------------------------------------------------------------------
    def import_results(self, input_file):
        try:
            results, vuln_count = NiktoPlugin.parse_nikto_results(
                None, input_file)
            if results:
                Database.async_add_many(results)
        except Exception, e:
            fmt = format_exc()
            Logger.log_error(
                "Could not load Nikto results from file: %s" % input_file)
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(fmt)
        else:
            if results:
                Logger.log(
                    "Loaded %d vulnerabilities and %d resources from file: %s"
                    % (vuln_count, len(results) - vuln_count, input_file)
                )
            else:
                Logger.log_verbose("No data found in file: %s" % input_file)
