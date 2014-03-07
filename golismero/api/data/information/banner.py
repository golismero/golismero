#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service banner.
"""

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

__all__ = ["Banner"]

from . import Fingerprint
from .. import identity
from ..resource.domain import Domain
from ..resource.ip import IP
from ...text.text_utils import to_utf8

from warnings import warn


#------------------------------------------------------------------------------
class Banner(Fingerprint):
    """
    Service banner.
    """

    min_resources = 1


    #--------------------------------------------------------------------------
    def __init__(self, host, banner, port):
        """
        :param host: IP address or domain name where the banner was found.
        :type host: IP | Domain

        :param banner: Banner of the service.
        :type banner: str

        :param port: Port number of the service.
        :type port: int
        """

        # Sanitize the properties.
        if not isinstance(host, IP) and not isinstance(host, Domain):
            host = to_utf8(host)
            if isinstance(host, basestring):
                warn("Expected IP or Domain, got string instead",
                     RuntimeWarning)
                try:
                    host = IP(host)
                except Exception:
                    host = Domain(host)
            else:
                raise TypeError(
                    "Expected IP or Domain, got %r instead" % type(host))
        banner = to_utf8(banner)
        if type(banner) is not str:
            raise TypeError("Expected str, got %r instead" % type(banner))
        port = int(port)
        if port <= 0 or port >= 65536:
            raise ValueError("Invalid port number: %d" % port)

        # Save the properties.
        self.__banner = banner
        self.__port   = port

        # Parent constructor.
        super(Banner, self).__init__()

        # Link the banner to the host.
        host.add_information(self)


    #--------------------------------------------------------------------------
    @identity
    def banner(self):
        """
        :returns: Banner of the service.
        :rtype: str
        """
        return self.__banner


    #--------------------------------------------------------------------------
    @identity
    def port(self):
        """
        :returns: Port number of the service.
        :type port: int
        """
        return self.__port


    #--------------------------------------------------------------------------
    def get_ip_addresses(self):
        """
        :returns: Set of IP addresses where this banner was found.
        :rtype: set(str)
        """
        return {
            ip.address
            for ip in self.get_associated_resources_by_category(
                          IP.data_subtype)
        }


    #--------------------------------------------------------------------------
    def get_domains(self):
        """
        :returns: Set of domains where this banner was found.
        :rtype: set(str)
        """
        return {
            domain.name
            for domain in self.get_associated_resources_by_category(
                          Domain.data_subtype)
        }


    #--------------------------------------------------------------------------
    def get_hosts(self):
        """
        :returns: Set of IP addresses and domains where this banner was found.
        :rtype: set(str)
        """
        s = self.get_ip_addresses()
        s.update(self.get_domains())
        return s
