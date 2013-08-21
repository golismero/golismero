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
from golismero.api.data.vulnerability import UrlVulnerability
from golismero.api.external import run_external_tool, \
     win_to_cygwin_path, cygwin_to_win_path
from golismero.api.logger import Logger
from golismero.api.plugin import ImportPlugin, TestingPlugin

import os
import stat

from csv import reader
from tempfile import NamedTemporaryFile
from os.path import abspath, join, exists, pathsep, sep, split
from traceback import format_exc
from urlparse import urljoin


#------------------------------------------------------------------------------
class NiktoPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [BaseUrl]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        # We can't calculate how long will Nikto take.
        self.update_status(progress = None)

        # Get the path to the Nikto scanner.
        nikto_script = Config.plugin_args["exec"]
        if nikto_script and exists(nikto_script):
            nikto_dir = split(nikto_script)[0]
            nikto_dir = abspath(nikto_dir)
        else:
            nikto_dir = split(__file__)[0]
            nikto_dir = join(nikto_dir, "nikto")
            nikto_dir = abspath(nikto_dir)
            nikto_script = join(nikto_dir, "nikto.pl")
            if not nikto_script or not exists(nikto_script):
                nikto_script = "/usr/bin/nikto"
                if not exists(nikto_script):
                    nikto_script = Config.plugin_args["exec"]
                    if nikto_script:
                        Logger.log_error("Nikto not found! File: %s" % nikto_script)
                    else:
                        Logger.log_error("Nikto not found!")
                    return

        # Get the path to the configuration file.
        config = Config.plugin_args["config"]
        if config:
            config = join(nikto_dir, config)
            config = abspath(config)
            if not exists(config):
                config = "/etc/nikto.conf"
                if not exists(config):
                    config = Config.plugin_args["config"]
                    if config:
                        Logger.log_error("Nikto config file not found! File: %s" % config)
                    else:
                        Logger.log_error("Nikto config file not found!")
                    return

        # On Windows, we must always call Perl explicitly.
        # On POSIX, only if the script is not marked as executable.
        command = nikto_script
        if sep == "\\" or os.stat(nikto_script)[stat.ST_MODE] & stat.S_IXUSR == 0:

            # Now the command to run is the Perl interpreter.
            if sep == "\\":
                command = "perl.exe"
            else:
                command = "perl"

            # Look for the Perl interpreter on the PATH. Fail if not found.
            found = False
            for candidate in os.environ.get("PATH", "").split(pathsep):
                candidate = candidate.strip()
                candidate = join(candidate, command)
                if exists(candidate):
                    found = True
                    command = candidate
                    break
            if not found:
                Logger.log_error("Perl interpreter not found!")

            # Detect if it's the Cygwin version but we're outside Cygwin.
            # If so we need to use Unix style paths.
            use_cygwin = False
            if sep == "\\":
                cygwin = split(command)[0]
                cygwin = join(cygwin, "cygwin1.dll")
                if exists(cygwin):
                    nikto_script = win_to_cygwin_path(nikto_script)
                    if config:
                        config = win_to_cygwin_path(config)
                    use_cygwin = True

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
        if config:
            args.insert(0, config)
            args.insert(0, "-config")
        if command != nikto_script:
            args.insert(0, nikto_script)
        for option in ("Pause", "timeout", "Tuning"):
            value = Config.plugin_args.get(option.lower(), None)
            if value:
                args.extend(["-" + option, value])

        # Get the current folder, so we can restore it later.
        cwd = os.getcwd()

        # On Windows we can't open a temporary file twice (although it's
        # actually Python who won't let us). Note that there is no exploitable
        # race condition here, because on Windows you can only create
        # filesystem links from an Administrator account.
        if sep == "\\":
            output_file = NamedTemporaryFile(suffix = ".csv", delete = False)
            try:
                output = output_file.name
                if use_cygwin:
                    output = win_to_cygwin_path(output)
                output_file.close()
                try:
                    os.chdir(nikto_dir)
                    return self.run_nikto(info, output, command, args)
                finally:
                    os.chdir(cwd)
            finally:
                os.unlink(output_file.name)

        # On POSIX we can do things more elegantly.
        # It also prevents a race condition vulnerability, although if you're
        # running a Python script from root you kinda deserve to get pwned.
        else:
            with NamedTemporaryFile(suffix = ".csv") as output_file:
                output = output_file.name
                try:
                    os.chdir(nikto_dir)
                    return self.run_nikto(info, output, command, args)
                finally:
                    os.chdir(cwd)


    #--------------------------------------------------------------------------
    def run_nikto(self, info, output_filename, command, args):
        """
        Run Nikto and convert the output to the GoLismero data model.

        :param info: Base URL to scan.
        :type info: BaseUrl

        :param output_filename: Path to the output filename.
            The format should always be CSV.
        :type output_filename:

        :param command: Path to the Nikto executable.
            May also be the Perl interpreter executable, with the
            Nikto script as its first argument.
        :type command: str

        :param args: Arguments to pass to the executable.
        :type args: list(str)

        :returns: Results from the Nikto scan.
        :rtype: list(Data)
        """

        # Append the output file name to the arguments.
        args.append("-output")
        args.append(output_filename)

        # Turn off DOS path warnings for Cygwin.
        # Does nothing on other platforms.
        env = os.environ.copy()
        cygwin = env.get("CYGWIN", "")
        if "nodosfilewarning" not in cygwin:
            if cygwin:
                cygwin += " "
            cygwin += "nodosfilewarning"
        env["CYGWIN"] = cygwin

        # Run Nikto and capture the text output.
        Logger.log("Launching Nikto against: %s" % info.hostname)
        Logger.log_more_verbose("Nikto arguments: %s %s" % (command, " ".join(args)))
        ##output, code = run_external_tool("C:\\cygwin\\bin\\perl.exe", ["-V"], env) # DEBUG
        output, code = run_external_tool(command, args, env)

        # Log the output in extra verbose mode.
        if code:
            Logger.log_error("Nikto execution failed, status code: %d" % code)
            if output:
                Logger.log_error_more_verbose(output)
        elif output:
            Logger.log_more_verbose(output)

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
        Run Nikto and convert the output to the GoLismero data model.

        :param info: Base URL to scan.
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
            if output_filename.startswith("/cygdrive/"):
                output_filename = cygwin_to_win_path(output_filename)
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
                        if (info is None or host != info.hostname) and host not in hosts_seen:
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

                        # Report the vulnerabilities.
                        vuln = UrlVulnerability(
                            url = url,
                            level = "informational",  # TODO: use the OSVDB API
                            description = "%s: %s" % (vuln_tag, text),
                        )
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
            Logger.log_error(
                "Could not load Nikto results from file: %s" % input_file)
            Logger.log_error_verbose(str(e))
            Logger.log_error_more_verbose(format_exc())
        else:
            if results:
                Logger.log(
                    "Loaded %d vulnerabilities and %d resources from file: %s" %
                    (vuln_count, len(results) - vuln_count, input_file)
                )
            else:
                Logger.log_verbose("No data found in file: %s" % input_file)
