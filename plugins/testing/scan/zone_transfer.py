#!/usr/bin/python
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

from golismero.api.config import Config
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.data.vulnerability.information_disclosure.dns_zone_transfer\
     import DNSZoneTransfer
from golismero.api.logger import Logger
from golismero.api.net.dns import DNS
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
class DNSZoneTransferPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [Domain]


    #--------------------------------------------------------------------------
    def run(self, info):

        # Get the root domain only.
        root = info.root

        # Skip localhost.
        if root == "localhost":
            return

        # Skip if the root domain is out of scope.
        if root not in Config.audit_scope:
            return

        # Skip root domains we've already processed.
        if self.state.put(root, True):
            return

        # Attempt a DNS zone transfer.
        ns_servers, resolv = DNS.zone_transfer(
            root, ns_allowed_zone_transfer = True)

        # On failure, skip.
        if not resolv:
            Logger.log_verbose(
                "DNS zone transfer failed, server %r not vulnerable"
                % root)
            return

        # Create a Domain object for the root domain.
        domain = Domain(root)

        # Associate all the results with the root domain.
        for r in resolv:
            map(domain.add_information, r)

        # Add the root domain to the results.
        results = []
        results.append(domain)

        # We have a vulnerability on each of the nameservers involved.
        msg = "DNS zone transfer successful, "
        if len(ns_servers) > 1:
            msg += "%d nameservers for %r are vulnerable!"
            msg %= (len(ns_servers), root)
        else:
            msg += "nameserver for %r is vulnerable!" % root
        Logger.log(msg)

        # If we don't have the name servers...
        if not ns_servers:

            # Assume the root domain also points to the nameserver.
            vulnerability = DNSZoneTransfer(domain, root)
            results.append(vulnerability)

        # If we have the name servers...
        else:

            # Create a vulnerability for each nameserver in scope.
            for ns in ns_servers:
                vulnerability = DNSZoneTransfer(domain, ns)
                results.append(vulnerability)

        # Return the results.
        return results
