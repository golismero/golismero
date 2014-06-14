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

from golismero.api.data.information.dns import DnsRegister
from golismero.api.data.resource.domain import Domain
from golismero.api.logger import Logger
from golismero.api.net.dns import DNS
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
class DNSPlugin(TestingPlugin):


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [Domain]


    #--------------------------------------------------------------------------
    def run(self, info):

        # Skip localhost.
        if info.root == "localhost":
            return

        # Get the domain name.
        domain = info.hostname
        Logger.log_more_verbose("Querying domain: %s" % domain)

        # We have as many steps as DNS register types there are.
        self.progress.set_total( len(DnsRegister.DNS_TYPES) )

        # Only show progress updates every 10%.
        self.progress.min_delta = 10

        # Try to get a DNS record of each type.
        results = []
        for step, rtype in enumerate(DnsRegister.DNS_TYPES):
            results.extend( DNS.resolve(domain, rtype) )
            self.progress.add_completed()
        Logger.log_more_verbose(
            "Found %d DNS registers for domain: %s"
            % (len(results), domain))

        # Link all DNS records to the domain.
        map(info.add_information, results)

        # Return the results.
        return results
