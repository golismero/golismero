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

# Acknowledgements:
# Thank you Danito for pointing out the Freegeoip.net service!
# https://twitter.com/dan1t0

from golismero.api.data.information.geolocation import Geolocation
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.logger import Logger
from golismero.api.plugin import TestingPlugin
from golismero.api.net.web_utils import json_decode

import netaddr
import requests
import traceback


#----------------------------------------------------------------------
class GeoIP(TestingPlugin):
    """
    This plugin tries to geolocate all IP addresses and domain names.
    """

    # TODO: this could be useful as a fallback if freegeoip.net fails:
    # http://linux.die.net/man/1/geoiplookup
    # https://github.com/ioerror/blockfinder


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Domain, IP]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # This is where we'll collect the data we'll return.
        results = []

        # Get the IP address or domain name.
        # Skip unsupported targets.
        if info.data_subtype == IP.data_subtype:
            if info.version != 4:
                return
            target = info.address
            parsed = netaddr.IPAddress(target)
            if parsed.is_loopback() or \
               parsed.is_private()  or \
               parsed.is_link_local():
                return
        elif info.data_subtype == Domain.data_subtype:
            target = info.hostname
            if "." not in target:
                return
        else:
            assert False, type(info)

        # Query the freegeoip.net service.
        # FIXME: the service supports SSL, but we need up to date certificates.
        Logger.log_more_verbose("Querying freegeoip.net for: " + target)
        resp   = requests.get("http://freegeoip.net/json/" + target)
        if not resp.content:
            raise RuntimeError(
                "Freegeoip.net webservice is not available,"
                " possible network error?"
            )
        kwargs = json_decode(resp.content)

        # Remove the IP address from the response.
        address = kwargs.pop("ip")

        # Create a Geolocation object.
        geoip = Geolocation(**kwargs)
        geoip.add_resource(info)
        results.append(geoip)

        # Log the location.
        try:
            Logger.log_verbose("%s is in %s" % (target, geoip))
        except Exception, e:
            fmt = traceback.format_exc()
            Logger.log_error("Error: %s" % str(e))
            Logger.log_error_more_verbose(fmt)

        # If we received a Domain object, create an IP object too.
        if info.resource_type == Domain.resource_type:
            ip = IP(address)
            ip.add_resource(info)
            ip.add_information(geoip)
            results.append(ip)

        # Return the results.
        return results
