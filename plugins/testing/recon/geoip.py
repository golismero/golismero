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

# Acknowledgements:
# Thank you Danito for pointing out the Freegeoip.net service!
# https://twitter.com/dan1t0

from golismero.api.data.information.geolocation import Geolocation
from golismero.api.data.information.traceroute import Traceroute
from golismero.api.data.resource.bssid import BSSID
from golismero.api.data.resource.ip import IP
from golismero.api.data.resource.mac import MAC
from golismero.api.logger import Logger
from golismero.api.plugin import TestingPlugin
from golismero.api.net.web_utils import json_decode

from geopy import geocoders
from shodan.wps import Skyhook

import netaddr
import requests
import traceback

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


#------------------------------------------------------------------------------
class GeoIP(TestingPlugin):
    """
    This plugin tries to geolocate all IP addresses and BSSIDs.
    It also enhances existing geolocation data from other sources.
    """

    # TODO: this could be useful as a fallback if freegeoip.net fails:
    # http://linux.die.net/man/1/geoiplookup
    # https://github.com/ioerror/blockfinder
    # http://geoip2.readthedocs.org/en/latest/
    # http://www.geonames.org/export/
    # https://github.com/danielmiessler/geoip/blob/master/geoip.rb


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [IP, MAC, BSSID, Traceroute, Geolocation]


    #--------------------------------------------------------------------------
    def run(self, info):

        # This is where we'll collect the data we'll return.
        results = []

        # Augment geolocation data obtained through other means.
        # (For example: image metadata)
        if info.is_instance(Geolocation):
            if not info.street_addr:
                street_addr = self.query_google(info.latitude, info.longitude)
                if street_addr:
                    info.street_addr = street_addr
                    #
                    # TODO: parse the street address
                    #
                    Logger.log("Location (%s, %s) is in %s" % \
                               (info.latitude, info.longitude, street_addr))
            return

        # Extract IPs from traceroute results and geolocate them.
        if info.is_instance(Traceroute):
            addr_to_ip = {}
            for hop in info.hops:
                if hop is not None:
                    if hop.address and hop.address not in addr_to_ip:
                        addr_to_ip[hop.address] = IP(hop.address)
            results.extend( addr_to_ip.itervalues() )
            coords_to_geoip = {}
            for res in addr_to_ip.itervalues():
                r = self.run(res)
                if r:
                    for x in r:
                        if not x.is_instance(Geolocation):
                            results.append(x)
                        else:
                            key = (x.latitude, x.longitude)
                            if key not in coords_to_geoip:
                                coords_to_geoip[key] = x
                                results.append(x)
                            else:
                                coords_to_geoip[key].merge(x)
            return results

        # Geolocate IP addresses using Freegeoip.
        if info.is_instance(IP):

            # Skip unsupported targets.
            if info.version != 4:
                return
            ip = info.address
            parsed = netaddr.IPAddress(ip)
            if parsed.is_loopback() or \
               parsed.is_private()  or \
               parsed.is_link_local():
                return

            # Query the freegeoip.net service.
            kwargs = self.query_freegeoip(ip)
            if not kwargs:
                return

            # Translate the arguments for Geolocation().
            kwargs.pop("ip")

        # Geolocate BSSIDs using Skyhook.
        elif info.is_instance(BSSID) or info.is_instance(MAC):
            skyhook = self.query_skyhook(info.address)
            if not skyhook:
                return

            # Translate the arguments for Geolocation().
            kwargs = {
                "latitude":     skyhook["latitude"],
                "longitude":    skyhook["longitude"],
                "accuracy":     skyhook["hpe"],
                "country_name": skyhook["country"],
                "country_code": skyhook["country_code"],
                "region_code":  skyhook["state_code"],
                "region_name":  skyhook["state"],
            }

        # Fail for other data types.
        else:
            assert False, "Internal error! Unexpected type: %r" % type(info)

        # Query the Google Geocoder to get the street address.
        street_addr = self.query_google(
            kwargs["latitude"], kwargs["longitude"])
        if street_addr:
            kwargs["street_addr"] = street_addr

        # Create a Geolocation object.
        geoip = Geolocation(**kwargs)
        geoip.add_resource(info)
        results.append(geoip)

        # Log the location.
        try:
            Logger.log_verbose(
                "%s %s is located in %s"
                % (info.display_name, info.address, geoip))
        except Exception, e:
            fmt = traceback.format_exc()
            Logger.log_error("Error: %s" % str(e))
            Logger.log_error_more_verbose(fmt)

        # Return the results.
        return results


    #--------------------------------------------------------------------------
    @staticmethod
    def query_freegeoip(ip):
        Logger.log_more_verbose("Querying freegeoip.net for: " + ip)
        try:
            resp = requests.get("http://freegeoip.net/json/" + ip)
            if resp.status_code == 200:
                return json_decode(resp.content)
            if resp.status_code == 404:
                Logger.log_more_verbose(
                    "No results from freegeoip.net for IP: " + ip)
            else:
                Logger.log_more_verbose(
                    "Response from freegeoip.net for %s: %s" %
                        (ip, resp.content))
        except Exception:
            raise RuntimeError(
                "Freegeoip.net webservice is not available,"
                " possible network error?"
            )


    #--------------------------------------------------------------------------
    @staticmethod
    def query_google(latitude, longitude):
        coordinates = "%s, %s" % (latitude, longitude)
        Logger.log_more_verbose(
            "Querying Google Geocoder for: %s" % coordinates)
        try:
            g = geocoders.GoogleV3()
            r = g.reverse(coordinates)
            if r:
                return r[0][0].encode("UTF-8")
        except Exception, e:
            fmt = traceback.format_exc()
            Logger.log_error_verbose("Error: %s" % str(e))
            Logger.log_error_more_verbose(fmt)


    #--------------------------------------------------------------------------
    @staticmethod
    def query_skyhook(bssid):
        Logger.log_more_verbose(
            "Querying Skyhook for: %s" % bssid)
        try:
            r = Skyhook().locate(bssid)
            if r:
                xml = ET.fromstring(r)
                ns = "{http://skyhookwireless.com/wps/2005}"
                err = xml.find(".//%serror" % ns)
                if err is not None:
                    Logger.log_error_verbose(
                        "Response from Skyhook: %s" % err.text)
                    return
                return {
                    "latitude": float(xml.find(".//%slatitude" % ns).text),
                    "longitude": float(xml.find(".//%slongitude" % ns).text),
                    "hpe": float(xml.find(".//%shpe" % ns).text),
                    "state": xml.find(".//%sstate" % ns).text,
                    "state_code": xml.find(".//%sstate" % ns).get("code"),
                    "country": xml.find(".//%scountry" % ns).text,
                    "country_code": xml.find(".//%scountry" % ns).get("code"),
                }
        except Exception, e:
            fmt = traceback.format_exc()
            Logger.log_error_verbose("Error: %s" % str(e))
            Logger.log_error_more_verbose(fmt)
