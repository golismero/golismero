#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This plugin tries to find hidden subdomains.
"""

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
from golismero.api.data import discard_data
from golismero.api.data.information.dns import DnsRegister
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.logger import Logger
from golismero.api.net.dns import DNS
from golismero.api.parallel import pmap, Counter
from golismero.api.plugin import TestingPlugin
from golismero.api.text.wordlist import WordListLoader

from netaddr import IPAddress


#--------------------------------------------------------------------------
#
# DNS analyzer
#
#--------------------------------------------------------------------------
class DNSAnalyzer(TestingPlugin):


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Domain]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        m_domain = info.root

        # Skips localhost
        if m_domain == "localhost":
            return

        m_return = None

        # Checks if the hostname has been already processed
        if not self.state.check(m_domain):

            Logger.log_verbose("Starting DNS analyzer plugin")
            m_return = []

            m_reg_len = len(DnsRegister.DNS_TYPES)
            for l_step, l_type in enumerate(DnsRegister.DNS_TYPES):

                # Update status
                progress = (float(l_step) / float(m_reg_len)) * 100.0
                self.update_status(progress=progress)
                Logger.log_more_verbose("Making %r DNS query" % l_type)

                # Make the query
                m_return.extend(DNS.resolve(m_domain, l_type))

            # Set the domain parsed
            self.state.set(m_domain, True)

            # Add the information to the host
            map(info.add_information, m_return)

            Logger.log_verbose("Ending DNS analyzer plugin, found %d registers" % len(m_return))

        return m_return


#--------------------------------------------------------------------------
#
# DNS zone transfer
#
#--------------------------------------------------------------------------
class DNSZoneTransfer(TestingPlugin):


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Domain]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        m_domain = info.root

        # Skips localhost
        if m_domain == "localhost":
            return

        m_return = None

        # Checks if the hostname has been already processed
        if not self.state.check(m_domain):

            Logger.log_more_verbose("Starting DNS zone transfer plugin")
            m_return = []

            #
            # Make the zone transfer
            #
            m_ns_servers, m_zone_transfer = DNS.zone_transfer(m_domain, ns_allowed_zone_transfer=True)

            m_return_append = m_return.append
            if m_zone_transfer:

                Logger.log_more_verbose("DNS zone transfer successful")

                m_return.extend(m_zone_transfer)

                for l_ns in m_ns_servers:
                    # Create the vuln
                    l_v        = DNSZoneTransfer(l_ns)
                    l_resource = None

                    # Is a IPaddress?
                    try:
                        ip = IPAddress(l_ns)
                    except Exception:
                        ip = None
                    if ip is not None:

                        # Create the IP resource
                        l_resource = IP(l_ns)

                    else:

                        # Create the Domain resource
                        l_resource = Domain(l_ns)

                    # Associate the resource to the vuln
                    l_v.add_resource(l_resource)

                    # Append to the results: the resource and the vuln
                    m_return_append(l_v)
                    m_return_append(l_resource)

            else:
                Logger.log_more_verbose("DNS zone transfer failed, server not vulnerable")

            m_return.extend(m_ns_servers)

            # Set the domain parsed
            self.state.set(m_domain, True)

        return m_return


#--------------------------------------------------------------------------
#
# DNS Bruteforcer
#
#--------------------------------------------------------------------------
class DNSBruteforcer(TestingPlugin):


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Domain]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        m_domain = info.root

        # Skips localhost
        if m_domain == "localhost":
            return

        m_return = None

        # Checks if the hostname has been already processed
        if not self.state.check(m_domain):

            #
            # Looking for
            #
            m_subdomains = WordListLoader.get_advanced_wordlist_as_list("subs_small.txt")

            # Run in parallel
            self.base_domain = m_domain
            self.completed = Counter(0)
            self.total = len(m_subdomains)
            r = pmap(self.get_subdomains_bruteforcer, m_subdomains, pool_size=10)

            #
            # Remove repeated
            #

            # The results
            m_domains                  = set()
            m_domains_add              = m_domains.add
            m_domains_already          = []
            m_domains_already_append   = m_domains_already.append

            m_ips                      = set()
            m_ips_add                  = m_ips.add
            m_ips_already              = []
            m_ips_already_append       = m_ips_already.append

            if r:
                for doms in r:
                    for dom in doms:
                        # Domains
                        if dom.type == "CNAME":
                            if not dom.target in m_domains_already:
                                m_domains_already_append(dom.target)
                                if dom.target in Config.audit_scope:
                                    m_domains_add(dom)
                                else:
                                    discard_data(dom)

                        # IPs
                        if dom.type == "A":
                            if dom.address not in m_ips_already:
                                m_ips_already_append(dom.address)
                                m_ips_add(dom)

                # Unify
                m_domains.update(m_ips)

                m_return = m_domains


                # Add the information to the host
                map(info.add_information, m_return)

            # Set the domain as processed
            self.state.set(m_domain, True)

            Logger.log_verbose("DNS analyzer plugin found %d subdomains" % len(m_return))


            # Write the info as more user friendly
            if Logger.MORE_VERBOSE:
                m_tmp        = []
                m_tmp_append = m_tmp.append
                for x in m_return:
                    if getattr(x, "address", False):
                        m_tmp_append("%s (%s)" % (getattr(x, "address"), str(x)))
                    elif getattr(x, "target", False):
                        m_tmp_append("%s (%s)" % (getattr(x, "target"), str(x)))
                    else:
                        m_tmp_append(str(x))

                Logger.log_more_verbose("Subdomains found: \n\t+ %s" % "\n\t+ ".join(m_tmp))

        return m_return


    #----------------------------------------------------------------------
    def get_subdomains_bruteforcer(self, subdomain):
        """
        Try to discover subdomains using bruteforce. This function is
        prepared to run in parallel.

        To try to make as less as possible connections, discovered_domains
        contains a list with already discovered domains.

        :param base_domain: string with de domain to make the test.
        :type base_domain: str

        :param updater_func: function to update the state of the process.
        :type updater_func: update_status

        :param subdomain: string with the domain to process.
        :type subdomain: str
        """

        m_domain = "%s.%s" % (subdomain, self.base_domain)

        completed = self.completed.inc()
        progress  = (float(completed) / float(self.total)) * 100.0

        self.update_status(progress=progress)
        Logger.log_more_verbose("Looking for subdomain: %s" % m_domain)

        l_oks = DNS.get_a(m_domain, also_CNAME=True)
        l_oks.extend(DNS.get_aaaa(m_domain, also_CNAME=True))

        return l_oks
