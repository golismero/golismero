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

__all__ = ["TextReport"]

import sys

from collections import defaultdict

from golismero.api.audit import get_audit_times, parse_audit_times
from golismero.api.config import Config
from golismero.api.data.db import Database
from golismero.api.data.information.fingerprint import OSFingerprint, WebServerFingerprint, ServiceFingerprint
from golismero.api.data.information.geolocation import Geolocation
from golismero.api.data.information.portscan import Portscan
from golismero.api.data.information.traceroute import Traceroute
from golismero.api.data.resource.bssid import BSSID
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.email import Email
from golismero.api.data.resource.ip import IP
from golismero.api.data.resource.mac import MAC
from golismero.api.data.resource.url import URL, BaseURL
from golismero.api.logger import Logger
from golismero.api.plugin import ReportPlugin, get_plugin_name

# Data types
from golismero.api.data import Data
from golismero.api.data.information import Information
from golismero.api.data.resource import Resource
from golismero.api.data.vulnerability import Vulnerability

# XXX HACK
from golismero.main.console import Console, colorize, colorize_substring, get_terminal_size


#------------------------------------------------------------------------------
from texttable import Texttable as orig_Texttable

class Texttable(orig_Texttable):
    def _str(self, i, x):
        if x is None:
            return ""
        if isinstance(x, unicode):
            return x.encode("UTF-8")
        return str(x)


#------------------------------------------------------------------------------
class TextReport(ReportPlugin):
    """
    Plugin to display reports on screen or to a plain text file.
    """


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):

        # We need some custom logic here, because the same plugin is used for
        # both text output to a file and text output to the console.
        return (
            not output_file
            or output_file == "-"
            or output_file.lower().endswith(".txt")
        )


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        self.__show_data = not Config.audit_config.only_vulns
        if output_file and output_file.lower().endswith(".txt"):
            Logger.log_verbose("Writing text report to file: %s" % output_file)
            self.__console = False
            self.__color   = False
            self.__width   = int( Config.plugin_args.get("width", "0") )
            self.__console = False
            with open(output_file, mode='w') as self.__fd:
                self.__write_report()
        else:
            self.__console = True
            self.__color   = Console.use_colors
            self.__width   = max(0, get_terminal_size()[0])
            self.__fd      = sys.stdout
            self.__write_report()


    #--------------------------------------------------------------------------
    def __colorize(self, txt, level_or_color):
        if self.__color:
            return colorize(txt, level_or_color)
        return txt


    #--------------------------------------------------------------------------
    def __iterate(self, data_type = None, data_subtype = None):
        if Database.count(data_type=data_type, data_subtype=data_subtype) <100:
            return Database.get_many(
                Database.keys(data_type=data_type, data_subtype=data_subtype)
            )
        return Database.iterate(data_type=data_type, data_subtype=data_subtype)


    #--------------------------------------------------------------------------
    def __add_related(self, table, data, data_type, data_subtype, title):
        t = [ str(x) for x in data.find_linked_data(data_type, data_subtype) ]
        if t:
            if len(t) == 1:
                table.add_row((title, t[0]))
            else:
                t.sort()
                table.add_row((title + "s", "\n".join(t)))


    #--------------------------------------------------------------------------
    def __fix_table_width(self, table):
        if self.__width > 0:
            if hasattr(table, "_hline_string"):
                table._hline_string = "" # workaround for bug in texttable
            assert all(len(x) == 2 for x in table._rows), table._rows
            w = max( len(x[0]) for x in table._rows )
            if table._header:
                assert len(table._header) == 2, len(table._header)
                w = max( w, len(table._header[0]) )
            m = w + 8
            if self.__width > m:
                table.set_cols_width((w, self.__width - m))


    #--------------------------------------------------------------------------
    def __write_report(self):

        # Header
        print >>self.__fd, ""
        print >>self.__fd, "--= %s =--" % self.__colorize("Report", "cyan")
        print >>self.__fd, ""

        # Summary
        start_time, stop_time, run_time = parse_audit_times( *get_audit_times() )
        host_count  = Database.count(Data.TYPE_RESOURCE, Domain.data_subtype)
        host_count += Database.count(Data.TYPE_RESOURCE, IP.data_subtype)
        vuln_count  = Database.count(Data.TYPE_VULNERABILITY)
        print >>self.__fd, "-# %s #- " % self.__colorize("Summary", "yellow")
        print >>self.__fd, ""
        print >>self.__fd, "Audit started:   %s" % self.__colorize(start_time, "yellow")
        print >>self.__fd, "Audit ended:     %s" % self.__colorize(stop_time, "yellow")
        print >>self.__fd, "Execution time:  %s" % self.__colorize(run_time, "yellow")
        print >>self.__fd, ""
        print >>self.__fd, "Scanned hosts:   %s" % self.__colorize(str(host_count), "yellow")
        print >>self.__fd, "Vulnerabilities: %s" % self.__colorize(str(vuln_count), "red" if vuln_count else "yellow")
        print >>self.__fd, ""

        # Audit scope
        if self.__show_data or not self.__console:
            table = Texttable()
            scope_domains = ["*." + r for r in Config.audit_scope.roots]
            scope_domains.extend(Config.audit_scope.domains)
            if Config.audit_scope.addresses:
                table.add_row(("IP addresses", "\n".join(Config.audit_scope.addresses)))
            if scope_domains:
                table.add_row(("Domains", "\n".join(scope_domains)))
            if Config.audit_scope.web_pages:
                table.add_row(("Web pages", "\n".join(Config.audit_scope.web_pages)))
            if table._rows:
                self.__fix_table_width(table)
                print >>self.__fd, "-# %s #- " % self.__colorize("Audit Scope", "yellow")
                print >>self.__fd, ""
                print >>self.__fd, table.draw()
                print >>self.__fd, ""

        # Discovered hosts
        if self.__show_data:
            need_header = True
            for domain in self.__iterate(Data.TYPE_RESOURCE, Domain.data_subtype):
                table = Texttable()
                self.__add_related(table, domain, Data.TYPE_RESOURCE, IP.data_subtype, "IP Address")
                self.__add_related(table, domain, Data.TYPE_INFORMATION, Geolocation.data_subtype, "Location")
                self.__add_related(table, domain, Data.TYPE_INFORMATION, WebServerFingerprint.data_subtype, "Web Server")
                self.__add_related(table, domain, Data.TYPE_INFORMATION, OSFingerprint.data_subtype, "OS Fingerprint")
                if table._rows:
                    if need_header:
                        need_header = False
                        print >>self.__fd, "-# %s #- " % self.__colorize("Hosts", "yellow")
                        print >>self.__fd, ""
                    table.header(("Domain Name", domain.hostname))
                    self.__fix_table_width(table)
                    text = table.draw()
                    if self.__color:
                        text = colorize_substring(text, domain.hostname, "red" if domain.get_links(Data.TYPE_VULNERABILITY) else "green")
                    print >>self.__fd, text
                    print >>self.__fd, ""
            for ip in self.__iterate(Data.TYPE_RESOURCE, IP.data_subtype):
                table = Texttable()
                self.__add_related(table, ip, Data.TYPE_RESOURCE, Domain.data_subtype, "Domain Name")
                self.__add_related(table, ip, Data.TYPE_RESOURCE, MAC.data_subtype, "MAC Address")
                self.__add_related(table, ip, Data.TYPE_RESOURCE, BSSID.data_subtype, "WiFi 802.11 BSSID")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, Geolocation.data_subtype, "Location")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, WebServerFingerprint.data_subtype, "Web Server")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, OSFingerprint.data_subtype, "OS Fingerprint")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, ServiceFingerprint.data_subtype, "Service")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, Portscan.data_subtype, "Port Scan")
                self.__add_related(table, ip, Data.TYPE_INFORMATION, Traceroute.data_subtype, "Network Route")
                if table._rows:
                    if need_header:
                        need_header = False
                        print >>self.__fd, "-# %s #- " % self.__colorize("Hosts", "yellow")
                        print >>self.__fd, ""
                    table.header(("IP Address", ip.address))
                    self.__fix_table_width(table)
                    text = table.draw()
                    if self.__color:
                        text = colorize_substring(text, ip.address, "red" if ip.get_links(Data.TYPE_VULNERABILITY) else "green")
                    print >>self.__fd, text
                    print >>self.__fd, ""

        # Web servers
        if self.__show_data and Database.count(Data.TYPE_RESOURCE, BaseURL.data_subtype):
            print >>self.__fd, "-# %s #- " % self.__colorize("Web Servers", "yellow")
            print >>self.__fd, ""
            crawled = defaultdict(list)
            vulnerable = []
            for url in self.__iterate(Data.TYPE_RESOURCE, URL.data_subtype):
                crawled[url.hostname].append(url.url)
                if self.__color and url.get_links(Data.TYPE_VULNERABILITY):
                    vulnerable.append(url)
            for url in self.__iterate(Data.TYPE_RESOURCE, BaseURL.data_subtype):
                table = Texttable()
                table.header(("Base URL", url.url))
                self.__add_related(table, url, Data.TYPE_INFORMATION, WebServerFingerprint.data_subtype, "Server")
                self.__add_related(table, url, Data.TYPE_INFORMATION, OSFingerprint.data_subtype, "Platform")
                urls = crawled[url.hostname]
                if urls:
                    urls.sort()
                    table.add_row(("Visited URLs", "\n".join(urls)))
                if table._rows:
                    self.__fix_table_width(table)
                    text = table.draw()
                    if self.__color:
                        p = text.find("\n")
                        p = text.find("\n", p + 1)
                        p = text.find("\n", p + 1)
                        if p > 0:
                            text = colorize_substring(text[:p], url.url, "red" if url.get_links(Data.TYPE_VULNERABILITY) else "green") + text[p:]
                        for u in vulnerable:
                            if u != url.url:
                                text = colorize_substring(text, u, "red")
                    print >>self.__fd, text
                    print >>self.__fd, ""

        # Emails
        if self.__show_data:
            emails = {
                e.address: "red" if e.get_links(Data.TYPE_VULNERABILITY) else "green"
                for e in self.__iterate(Data.TYPE_RESOURCE, Email.data_subtype)
            }
            if emails:
                print >>self.__fd, "-# %s #- " % self.__colorize("Email Addresses", "yellow")
                print >>self.__fd, ""
                for e in sorted(emails):
                    print >>self.__fd, "* " + self.__colorize(e, emails[e])
                print >>self.__fd, ""

        # Vulnerabilities
        print >>self.__fd, "-# %s #- " % self.__colorize("Vulnerabilities", "yellow")
        print >>self.__fd, ""
        count = Database.count(Data.TYPE_VULNERABILITY)
        if count:
            if self.__show_data:
                print >>self.__fd, self.__colorize("%d vulnerabilities found!" % count, "red")
                print >>self.__fd, ""
            vuln_types = { v.display_name: v.vulnerability_type for v in self.__iterate(Data.TYPE_VULNERABILITY) }
            titles = vuln_types.keys()
            titles.sort()
            if "Uncategorized Vulnerability" in titles:
                titles.remove("Uncategorized Vulnerability")
                titles.append("Uncategorized Vulnerability")
            for title in titles:
                data_subtype = vuln_types[title]
                print >>self.__fd, "-- %s (%s) -- " % (self.__colorize(title, "cyan"), data_subtype)
                print >>self.__fd, ""
                for vuln in self.__iterate(Data.TYPE_VULNERABILITY, data_subtype):
                    table = Texttable()
                    table.header(("Occurrence ID", vuln.identity))
                    w = len(table.draw())
                    table.add_row(("Title", vuln.title))
                    ##targets = self.__gather_vulnerable_resources(vuln)
                    targets = [vuln.target]
                    table.add_row(("Found By", get_plugin_name(vuln.plugin_id)))
                    p = len(table.draw())
                    table.add_row(("Level", vuln.level))
                    #table.add_row(("Impact", vuln.impact))
                    #table.add_row(("Severity", vuln.severity))
                    #table.add_row(("Risk", vuln.risk))
                    q = len(table.draw())
                    if vuln.cvss_base:
                        table.add_row(("CVSS Base", vuln.cvss_base))
                    if vuln.cvss_score:
                        table.add_row(("CVSS Score", vuln.cvss_score))
                    if vuln.cvss_vector:
                        table.add_row(("CVSS Vector", vuln.cvss_vector))
                    if len(targets) > 1:
                        targets.sort()
                        table.add_row(("Locations", "\n".join(targets)))
                    elif targets:
                        table.add_row(("Location", targets[0]))
                    table.add_row(("Description", vuln.description))
                    table.add_row(("Solution", vuln.solution))
                    taxonomy = []
                    if vuln.bid:
                        taxonomy.extend(vuln.bid)
                    if vuln.cve:
                        taxonomy.extend(vuln.cve)
                    if vuln.cwe:
                        taxonomy.extend(vuln.cwe)
                    if vuln.osvdb:
                        taxonomy.extend(vuln.osvdb)
                    if vuln.sa:
                        taxonomy.extend(vuln.sa)
                    if vuln.sectrack:
                        taxonomy.extend(vuln.sectrack)
                    if vuln.xf:
                        taxonomy.extend(vuln.xf)
                    if taxonomy:
                        table.add_row(("Taxonomy", "\n".join(taxonomy)))
                    if vuln.references:
                        table.add_row(("References", "\n".join(sorted(vuln.references))))
                    details = vuln.display_properties.get("Details")
                    if details:
                        props = details.keys()
                        props.sort()
                        table.add_row(("Additional details", "\n".join(("%s: %s" % (x, details[x])) for x in props)))
                    self.__fix_table_width(table)
                    text = table.draw()
                    if self.__color:
                        text_1 = text[:w]
                        text_3 = text[p:q]
                        text_1 = colorize_substring(text_1, vuln.identity, vuln.level.lower())
                        for lvl in Vulnerability.VULN_LEVELS:
                            if lvl in text_3:
                                text_3 = colorize_substring(text_3, lvl, lvl.lower())
                        text = text_1 + text[w:p] + text_3 + text[q:]
                    print >>self.__fd, text
                    print >>self.__fd, ""
        else:
            print >>self.__fd, self.__colorize("No vulnerabilities found.", "green")
            print >>self.__fd, ""


    #--------------------------------------------------------------------------
    def __gather_vulnerable_resources(self, vuln):
        vulnerable = []
        visited = set()
        queue = [vuln]
        while queue:
            data = queue.pop()
            identity = data.identity
            if identity not in visited:
                visited.add(identity)
                if data.data_type == Data.TYPE_RESOURCE:
                    vulnerable.append(str(data))
                else:
                    queue.extend(data.linked_data)
        visited.clear()
        return vulnerable
