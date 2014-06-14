#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Portscan results.
"""

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

__all__ = ["Portscan"]

from . import Fingerprint
from .. import identity
from ..resource.ip import IP

from time import time


#------------------------------------------------------------------------------
class Portscan(Fingerprint):
    """
    Portscan results.
    """


    #--------------------------------------------------------------------------
    def __init__(self, ip, ports, timestamp = None):
        """
        :param ip: Scanned host's IP address.
        :type ip: IP

        :param ports: Portscan results.
            A set of tuples, each tuple containing the following data for
            each scanned port: state, protocol, port. The state is a string
            with one of the following values: "OPEN, "CLOSED" or "FILTERED".
            The protocol is a string with one of the following values: "TCP"
            or "UDP". The port is an integer from 0 to 65536, not included.
        :type ports: set( tuple(str, str, int), ... )

        :param timestamp: Timestamp for these portscan results.
            Defaults to the current time.
        :type timestamp: float
        """

        # Sanitize and store the properties.
        try:
            assert isinstance(ip, IP), type(ip)
            self.__address   = ip.address
            self.__timestamp = float(timestamp) if timestamp else time()
            sane    = set()
            visited = set()
            for state, protocol, port in ports:
                state    = str( state.upper() )
                protocol = str( protocol.upper() )
                port     = int(port)
                assert state in ("OPEN", "CLOSED", "FILTERED"), state
                assert protocol in ("TCP", "UDP"), state
                assert 0 < port < 65536, port
                key = (protocol, port)
                assert key not in visited, key
                visited.add(key)
                sane.add( (state, protocol, port) )
            self.__ports = frozenset(sane)
        except Exception:
            ##raise # XXX DEBUG
            raise ValueError("Malformed portscan results!")

        # Call the superclass constructor.
        super(Portscan, self).__init__()

        # Now we can associate the portscan results to the IP address.
        self.add_resource(ip)


    #--------------------------------------------------------------------------
    @identity
    def address(self):
        """
        :returns: Scanned host's IP address.
        :rtype: str
        """
        return self.__address


    #--------------------------------------------------------------------------
    @identity
    def ports(self):
        """
        :returns: Portscan results.
            A set of tuples, each tuple containing the following data for
            each scanned port: state, protocol, port. The state is a string
            with one of the following values: "OPEN, "CLOSED" or "FILTERED".
            The protocol is a string with one of the following values: "TCP"
            or "UDP". The port is an integer from 0 to 65536, not included.
        :rtype: frozenset( tuple(str, str, int), ... )
        """
        return self.__ports


    #--------------------------------------------------------------------------
    @identity
    def timestamp(self):
        """
        :returns: Timestamp for these portscan results.
        :rtype: float
        """
        return self.__timestamp


    #--------------------------------------------------------------------------
    def __str__(self):
        return "\n".join("%-8s %-3s %d" % p for p in sorted(self.ports))


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Port Scan Results"


    #--------------------------------------------------------------------------
    @property
    def open_tcp_ports(self):
        """
        :returns: Open TCP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "OPEN" and protocol == "TCP"
        ]
        ports.sort()
        return ports


    #--------------------------------------------------------------------------
    @property
    def closed_tcp_ports(self):
        """
        :returns: Closed TCP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "CLOSED" and protocol == "TCP"
        ]
        ports.sort()
        return ports


    #--------------------------------------------------------------------------
    @property
    def filtered_tcp_ports(self):
        """
        :returns: Filtered TCP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "FILTERED" and protocol == "TCP"
        ]
        ports.sort()
        return ports


    #--------------------------------------------------------------------------
    @property
    def open_udp_ports(self):
        """
        :returns: Open UDP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "OPEN" and protocol == "UDP"
        ]
        ports.sort()
        return ports


    #--------------------------------------------------------------------------
    @property
    def closed_udp_ports(self):
        """
        :returns: Closed UDP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "CLOSED" and protocol == "UDP"
        ]
        ports.sort()
        return ports


    #--------------------------------------------------------------------------
    @property
    def filtered_udp_ports(self):
        """
        :returns: Filtered UDP ports.
        :rtype: list(int)
        """
        ports = [
            port for state, protocol, port in self.ports
            if state == "FILTERED" and protocol == "UDP"
        ]
        ports.sort()
        return ports
