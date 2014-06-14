#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Traceroute results.
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

__all__ = ["Traceroute", "Hop"]

from . import Fingerprint
from .. import identity
from ..resource.ip import IP
from ..resource.domain import Domain
from ...config import Config
from ...text.text_utils import to_utf8

from time import time


#------------------------------------------------------------------------------
class Hop (object):
    """
    Traceroute hop.
    """


    #--------------------------------------------------------------------------
    def __init__(self, address, rtt, hostname = None):
        """
        :param address: IP address.
        :type address: str

        :param rtt: Round trip time.
        :type rtt: float

        :param hostname: Hostname for this IP address. Optional.
        :type hostname: str | None
        """
        address  = to_utf8(address)
        hostname = to_utf8(hostname)
        if type(address) is not str:
            raise TypeError("Expected string, got %r instead" % type(address))
        if hostname is not None and type(hostname) is not str:
            raise TypeError("Expected string, got %r instead" % type(hostname))
        self.__address  = address
        self.__rtt      = float(rtt)
        self.__hostname = hostname


    #--------------------------------------------------------------------------
    def to_dict(self):
        return {
            "address":  self.__address,
            "rtt":      self.__rtt,
            "hostname": self.__hostname,
        }


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Network Route"


    #--------------------------------------------------------------------------
    @property
    def address(self):
        """
        :returns: IP address.
        :rtype: str
        """
        return self.__address


    #--------------------------------------------------------------------------
    @property
    def rtt(self):
        """
        :returns: Round trip time.
        :rtype: float
        """
        return self.__rtt


    #--------------------------------------------------------------------------
    @property
    def hostname(self):
        """
        :returns: Hostname for this IP address. Optional.
        :rtype: str | None
        """
        return self.__hostname


#------------------------------------------------------------------------------
class Traceroute(Fingerprint):
    """
    Traceroute results.
    """


    #--------------------------------------------------------------------------
    def __init__(self, ip, port, protocol, hops, timestamp = None):
        """
        :param ip: Scanned host's IP address.
        :type ip: IP

        :param port: Port used to trace the route.
        :type port: int

        :param protocol: Protocol used to trace the route.
            One of: "TCP", "UDP", "ICMP".
        :type protocol: str

        :param hops: Traceroute results.
            Missing hops are represented with None.
        :type hops: tuple( Hop | None, ... )

        :param timestamp: Timestamp for these traceroute results.
            Defaults to the current time.
        :type timestamp: float
        """

        # Sanitize and store the properties.
        try:
            self.__timestamp = float(timestamp) if timestamp else time()
            assert isinstance(ip, IP), type(ip)
            self.__address   = ip.address
            port = int(port)
            assert 0 < port < 65536, port
            self.__port = port
            protocol = str(protocol).upper()
            assert protocol in ("TCP", "UDP", "ICMP"), protocol
            self.__protocol = protocol
            hops = tuple(hops)
            for hop in hops:
                assert hop is None or isinstance(hop, Hop), type(hop)
            self.__hops = hops
        except Exception:
            ##raise # XXX DEBUG
            raise ValueError("Malformed traceroute results!")

        # Call the superclass constructor.
        super(Traceroute, self).__init__()

        # Now we can associate the traceroute results to the IP address.
        self.add_resource(ip)


    #--------------------------------------------------------------------------
    def to_dict(self):
        d = super(Traceroute, self).to_dict()
        d["hops"] = [
            (h.to_dict() if h is not None else None)
            for h in self.__hops
        ]
        return d


    #--------------------------------------------------------------------------
    @property
    def display_properties(self):
        props = super(Traceroute, self).display_properties
        del props["[DEFAULT]"]["Hops"]
        props["[DEFAULT]"]["Route"] = str(self)
        return props


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
    def port(self):
        """
        :returns: Port used to trace the route.
        :rtype: int
        """
        return self.__port


    #--------------------------------------------------------------------------
    @identity
    def protocol(self):
        """
        :returns: Protocol used to trace the route.
            One of: "TCP", "UDP", "ICMP".
        :rtype: str
        """
        return self.__protocol


    #--------------------------------------------------------------------------
    @identity
    def hops(self):
        """
        :returns: Traceroute results.
            Missing hops are represented with None.
        :rtype: tuple( Hop | None, ... )
        """
        return self.__hops


    #--------------------------------------------------------------------------
    @identity
    def timestamp(self):
        """
        :returns: Timestamp for these traceroute results.
        :rtype: float
        """
        return self.__timestamp


    #--------------------------------------------------------------------------
    def __str__(self):
        if self.hops:
            s = "Route to %s (%s %s):\n\n"
        else:
            s = "No route to %s (%s %s)."
        s %= (self.address, self.protocol, self.port)
        if self.hops:
            w = len(str(len(self.hops)))
            f = "%%%dd %%15s %%4.2f %%s" % w
            m = "%%%dd             ***     *** ***" % w
            s += "\n".join(
                (
                    f % (i, h.address, h.rtt, h.hostname)
                    if h is not None
                    else m % i
                )
                for i, h in enumerate(self.hops)
            )
        return s


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        result = []
        for hop in self.hops:
            if hop is not None:
                if hop.address in Config.audit_scope:
                    result.append( IP(hop.address) )
                if hop.hostname and hop.hostname in Config.audit_scope:
                    result.append( Domain(hop.hostname) )
        return result
