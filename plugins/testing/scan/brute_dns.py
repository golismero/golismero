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
from golismero.api.data.resource.domain import Domain
from golismero.api.text.text_utils import generate_random_string
from golismero.api.logger import Logger
from golismero.api.net.dns import DNS
from golismero.api.plugin import TestingPlugin
from golismero.api.text.wordlist import WordListLoader, WordlistNotFound
from golismero.api.data.vulnerability.information_disclosure.domain_disclosure import DomainDisclosure


#------------------------------------------------------------------------------
class DNSBruteforcer(TestingPlugin):


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [Domain]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        # Get the root domain only.
        root = info.root

        # Skip localhost.
        if root == "localhost":
            return

        # Skip root domains we've already processed.
        if self.state.put(root, True):
            return


        # Load the subdomains wordlist.
        try:
            wordlist = WordListLoader.get_advanced_wordlist_as_list(Config.plugin_args["wordlist"])
        except WordlistNotFound:
            Logger.log_error_verbose("Wordlist '%s' not found.." % Config.plugin_args["wordlist"])
            return
        except TypeError:
            Logger.log_error_verbose("Wordlist '%s' is not a file." % Config.plugin_args["wordlist"])
            return

        # Load the subdomains whitelist.
        try:
            whitelist = WordListLoader.get_advanced_wordlist_as_list(Config.plugin_config["wordlist"])
        except WordlistNotFound:
            Logger.log_error_verbose("Wordlist '%s' not found.." % Config.plugin_config["wordlist"])
            return
        except TypeError:
            Logger.log_error_verbose("Wordlist '%s' is not a file." % Config.plugin_config["wordlist"])
            return


        #
        # Set a base line for dinamyc sub-domains
        #
        m_virtual_domains = []
        for v in (generate_random_string(40) for x in xrange(3)):
            l_subdomain = ".".join((v, root))

            records = DNS.get_a(l_subdomain, also_CNAME=True)

            for rec in records:
                if rec.type == "CNAME":
                    m_virtual_domains.append(rec.target)

        # If 3 subdomains are the same, set the base domain
        m_base_domain = None
        if len(set(m_virtual_domains)) == 1:
            m_base_domain = m_virtual_domains[0]

        # Configure the progress notifier.
        self.progress.set_total(len(wordlist))
        self.progress.min_delta = 1  # notify every 1%

        # For each subdomain in the wordlist...
        found   = 0
        results = []
        visited = set()
        for prefix in wordlist:

            # Mark as completed before actually trying.
            # We can't put this at the end of the loop where it belongs,
            # because the "continue" statements would skip over this too.
            self.progress.add_completed()

            # Build the domain name.
            name = ".".join((prefix, root))

            # Skip if out of scope.
            if name not in Config.audit_scope:
                continue

            # Resolve the subdomain.
            records = DNS.get_a(name, also_CNAME=True)
            records.extend( DNS.get_aaaa(name, also_CNAME=True) )

            # If no DNS records were found, skip.
            if not records:
                continue

            # If CNAME is the base domain, skip
            chk = [True for x in records if x.type == "CNAME" and x.target == m_base_domain]
            if len(chk) > 0 and all(chk):
                continue

            # We found a subdomain!
            found += 1
            Logger.log_more_verbose(
                "Subdomain found: %s" % name)

            # Create the Domain object for the subdomain.
            domain = Domain(name)
            results.append(domain)

            #
            # Check for Domain disclosure
            #
            if prefix not in whitelist:
                d = DomainDisclosure(name,
                                     risk        = 0,
                                     level       = "low",
                                     title       = "Possible subdomain leak",
                                     description = "A subdomain was discovered which may be an unwanted information disclosure."
                                     )
                d.add_resource(domain)
                results.append(d)


            # For each DNs record, grab the address or name.
            # Skip duplicated records.
            for rec in records:
                if rec.type == "CNAME":
                    location = rec.target
                elif rec.type in ("A", "AAAA"):
                    location = rec.address
                else: # should not happen...
                    results.append(rec)
                    domain.add_information(rec)
                    continue
                if location not in visited:
                    visited.add(location)
                    results.append(rec)
                    domain.add_information(rec)

        # Log the results.
        if found:
            Logger.log(
                "Found %d subdomains for root domain: %s"
                % (found, root))
        else:
            Logger.log_verbose(
                "No subdomains found for root domain: %s" % root)

        # Return the results.
        return results
