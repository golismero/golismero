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

from golismero.api.config import Config
from golismero.api.data import discard_data
from golismero.api.data.information.banner import Banner
from golismero.api.data.information.geolocation import Geolocation
from golismero.api.data.information.html import HTML
from golismero.api.data.resource.domain import Domain
from golismero.api.data.resource.ip import IP
from golismero.api.logger import Logger
from golismero.api.plugin import TestingPlugin
from golismero.api.text.text_utils import to_utf8

from shodan import WebAPI

import datetime
import netaddr
import traceback


#------------------------------------------------------------------------------
class ShodanPlugin(TestingPlugin):
    """
    This plugin tries to perform passive reconnaissance on a target using
    the Shodan web API.
    """


    #--------------------------------------------------------------------------
    def check_params(self):

        # Make sure we have an API key.
        self.get_api_key()


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [IP]


    #--------------------------------------------------------------------------
    def get_api_key(self):
        key = Config.plugin_args.get("apikey", None)
        if not key:
            key = Config.plugin_config.get("apikey", None)
        if not key:
            raise ValueError(
                "Missing API key! Get one at:"
                " http://www.shodanhq.com/api_doc")
        return key


    #--------------------------------------------------------------------------
    def run(self, info):

        # This is where we'll collect the data we'll return.
        results = []

        # Skip unsupported IP addresses.
        if info.version != 4:
            return
        ip = info.address
        parsed = netaddr.IPAddress(ip)
        if parsed.is_loopback() or \
           parsed.is_private()  or \
           parsed.is_link_local():
            return

        # Query Shodan for this host.
        try:
            key = self.get_api_key()
            api = WebAPI(key)
            shodan = api.host(ip)
        except Exception, e:
            tb = traceback.format_exc()
            Logger.log_error("Error querying Shodan for host %s: %s" % (ip, str(e)))
            Logger.log_error_more_verbose(tb)
            return

        # Make sure we got the same IP address we asked for.
        if ip != shodan.get("ip", ip):
            Logger.log_error(
                "Shodan gave us a different IP address... weird!")
            Logger.log_error_verbose(
                "Old IP: %s - New IP: %s" % (ip, shodan["ip"]))
            ip = to_utf8( shodan["ip"] )
            info = IP(ip)
            results.append(info)

        # Extract all hostnames and link them to this IP address.
        # Note: sometimes Shodan sends IP addresses here! (?)
        seen_host = {}
        for hostname in shodan.get("hostnames", []):
            if hostname == ip:
                continue
            if hostname in seen_host:
                domain = seen_host[hostname]
            else:
                try:
                    try:
                        host = IP(hostname)
                    except ValueError:
                        host = Domain(hostname)
                except Exception:
                    tb = traceback.format_exc()
                    Logger.log_error_more_verbose(tb)
                seen_host[hostname] = host
                results.append(host)
                domain = host
            domain.add_resource(info)

        # Get the OS fingerprint, if available.
        os = to_utf8( shodan.get("os") )
        if os:
            Logger.log("Host %s is running %s" % (ip, os))
            pass  # XXX TODO we'll need to reverse lookup the CPE

        # Get the GPS data, if available.
        # Complete any missing data using the default values.
        try:
            latitude  = float( shodan["latitude"]  )
            longitude = float( shodan["longitude"] )
        except Exception:
            latitude  = None
            longitude = None
        if latitude is not None and longitude is not None:
            area_code = shodan.get("area_code")
            if not area_code:
                area_code = None
            else:
                area_code = str(area_code)
            country_code = shodan.get("country_code")
            if not country_code:
                country_code = shodan.get("country_code3")
                if not country_code:
                    country_code = None
                else:
                    country_code = str(country_code)
            else:
                country_code = str(country_code)
            country_name = shodan.get("country_name")
            if not country_name:
                country_name = None
            city = shodan.get("city")
            if not city:
                city = None
            dma_code = shodan.get("dma_code")
            if not dma_code:
                dma_code = None
            else:
                dma_code = str(dma_code)
            postal_code = shodan.get("postal_code")
            if not postal_code:
                postal_code = None
            else:
                postal_code = str(postal_code)
            region_name = shodan.get("region_name")
            if not region_name:
                region_name = None
            geoip = Geolocation(
                latitude, longitude,
                country_code = country_code,
                country_name = country_name,
                region_name = region_name,
                city = city,
                zipcode = postal_code,
                metro_code = dma_code,
                area_code = area_code,
            )
            results.append(geoip)
            geoip.add_resource(info)

        # Go through every result and pick only the latest ones.
        latest = {}
        for data in shodan.get("data", []):
            if (
                not "banner" in data or
                not "ip" in data or
                not "port" in data or
                not "timestamp" in data
            ):
                Logger.log_error("Malformed results from Shodan?")
                from pprint import pformat
                Logger.log_error_more_verbose(pformat(data))
                continue
            key = (
                data["ip"],
                data["port"],
                data["banner"],
            )
            try:
                timestamp = reversed(   # DD.MM.YYYY -> (YYYY, MM, DD)
                    map(int, data["timestamp"].split(".", 2)))
            except Exception:
                continue
            if key not in latest or timestamp > latest[key][0]:
                latest[key] = (timestamp, data)

        # Process the latest results.
        seen_isp_or_org = set()
        seen_html = set()
        for _, data in latest.values():

            # Extract all domains, but don't link them.
            for hostname in data.get("domains", []):
                if hostname not in seen_host:
                    try:
                        domain = Domain(hostname)
                    except Exception:
                        tb = traceback.format_exc()
                        Logger.log_error_more_verbose(tb)
                        continue
                    seen_host[hostname] = domain
                    results.append(domain)

            # We don't have any use for this information yet,
            # but log it so at least the user can see it.
            isp = to_utf8( data.get("isp") )
            org = to_utf8( data.get("org") )
            if org and org not in seen_isp_or_org:
                seen_isp_or_org.add(org)
                Logger.log_verbose(
                    "Host %s belongs to: %s"
                    % (ip, org)
                )
            if isp and (not org or isp != org) and isp not in seen_isp_or_org:
                seen_isp_or_org.add(isp)
                Logger.log_verbose(
                    "IP address %s is provided by ISP: %s"
                    % (ip, isp)
                )

            # Get the HTML content, if available.
            raw_html = to_utf8( data.get("html") )
            if raw_html:
                hash_raw_html = hash(raw_html)
                if hash_raw_html not in seen_html:
                    seen_html.add(hash_raw_html)
                    try:
                        html = HTML(raw_html)
                    except Exception:
                        html = None
                        tb = traceback.format_exc()
                        Logger.log_error_more_verbose(tb)
                    if html:
                        html.add_resource(info)
                        results.append(html)

            # Get the banner, if available.
            raw_banner = to_utf8( data.get("banner") )
            try:
                port = int( data.get("port", "0") )
            except Exception:
                port = 0
            if raw_banner and port:
                try:
                    banner = Banner(info, raw_banner, port)
                except Exception:
                    banner = None
                    tb = traceback.format_exc()
                    Logger.log_error_more_verbose(tb)
                if banner:
                    results.append(banner)

        # Was this host located somewhere else in the past?
        for data in reversed(shodan.get("data", [])):
            try:
                timestamp = reversed(   # DD.MM.YYYY -> (YYYY, MM, DD)
                    map(int, data["timestamp"].split(".", 2)))
                old_location = data.get("location")
                if old_location:
                    old_latitude  = old_location.get("latitude",  latitude)
                    old_longitude = old_location.get("longitude", longitude)
                    if (
                        old_latitude is not None and
                        old_longitude is not None and
                        (old_latitude != latitude or old_longitude != longitude)
                    ):

                        # Get the geoip information.
                        area_code = old_location.get("area_code")
                        if not area_code:
                            area_code = None
                        country_code = old_location.get("country_code")
                        if not country_code:
                            country_code = old_location.get("country_code3")
                            if not country_code:
                                country_code = None
                        country_name = old_location.get("country_name")
                        if not country_name:
                            country_name = None
                        city = old_location.get("city")
                        if not city:
                            city = None
                        postal_code = old_location.get("postal_code")
                        if not postal_code:
                            postal_code = None
                        region_name = old_location.get("region_name")
                        if not region_name:
                            region_name = None
                        geoip = Geolocation(
                            latitude, longitude,
                            country_code = country_code,
                            country_name = country_name,
                            region_name = region_name,
                            city = city,
                            zipcode = postal_code,
                            area_code = area_code,
                        )

                        # If this is the first time we geolocate this IP,
                        # use this information as it if were up to date.
                        if latitude is None or longitude is None:
                            latitude  = old_latitude
                            longitude = old_longitude
                            results.append(geoip)
                            geoip.add_resource(info)

                        # Otherwise, just log the event.
                        else:
                            discard_data(geoip)
                            where = str(geoip)
                            when = datetime.date(*timestamp)
                            msg = "Host %s used to be located at %s on %s."
                            msg %= (ip, where, when.strftime("%B %d, %Y"))
                            Logger.log_verbose(msg)

            except Exception:
                tb = traceback.format_exc()
                Logger.log_error_more_verbose(tb)

        # Return the results.
        return results
