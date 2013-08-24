#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Audit scope checking.
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

__all__ = ["AuditScope", "DummyScope"]

from ..api.data.resource.domain import Domain
from ..api.data.resource.ip import IP
from ..api.data.resource.url import Url
from ..api.net.dns import DNS
from ..api.net.web_utils import ParsedURL, split_hostname

from netaddr import IPAddress, IPNetwork

import re
import warnings


#------------------------------------------------------------------------------
class AuditScope (object):
    """
    Audit scope.

    Example:

        >>> from golismero.api.config import Config
        >>> 'www.example.com' in Config.audit_scope
        True
        >>> 'www.google.com' in Config.audit_scope
        False
    """

    _re_is_domain = re.compile(r"^[A-Za-z][A-Za-z0-9\_\-\.]*[A-Za-z0-9]$")


    #--------------------------------------------------------------------------
    def __init__(self, audit_config):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig
        """

        # This is where we'll keep the parsed targets.
        self.__domains   = set()   # Domain names.
        self.__addresses = set()   # IP addresses.
        self.__web_pages = set()   # URLs.

        # Remember if subdomains are allowed.
        self.__include_subdomains = audit_config.include_subdomains

        # For each user-supplied target string...
        for target in audit_config.targets:

            # If it's a domain name...
            if self._re_is_domain.match(target):

                # Convert it to lowercase.
                target = target.lower()

                # Keep the domain name.
                self.__domains.add(target)

                # Guess an URL from it.
                # FIXME: this should be smarter and use port scanning!
                self.__web_pages.add("http://%s/" % target)

            # If it's an IP address...
            else:
                try:
                    if target.startswith("[") and target.endswith("]"):
                        IPAddress(target[1:-1], version=6)
                        address = target[1:-1]
                    else:
                        IPAddress(target)
                        address = target
                except Exception:
                    address = None
                if address is not None:

                    # Keep the IP address.
                    self.__addresses.add(address)

                    # Guess an URL from it.
                    # FIXME: this should be smarter and use port scanning!
                    self.__web_pages.add("http://%s/" % address)

                # If it's an IP network...
                else:
                    try:
                        network = IPNetwork(target)
                    except Exception:
                        network = None
                    if network is not None:

                        # For each host IP address in range...
                        for address in network.iter_hosts():
                            address = str(address)

                            # Keep the IP address.
                            self.__addresses.add(address)

                            # Guess an URL from it.
                            # FIXME: this should be smarter and use port scanning!
                            self.__web_pages.add("http://%s/" % address)

                    # If it's an URL...
                    else:
                        try:
                            parsed_url = ParsedURL(target)
                            url = parsed_url.url
                        except Exception:
                            url = None
                        if url is not None:

                            # Keep the URL.
                            self.__web_pages.add(url)

                            # Extract the domain or IP address.
                            host = parsed_url.host
                            try:
                                if host.startswith("[") and host.endswith("]"):
                                    IPAddress(host[1:-1], version=6)
                                    host = host[1:-1]
                                else:
                                    IPAddress(host)
                                self.__addresses.add(host)
                            except Exception:
                                self.__domains.add( host.lower() )

        # If subdomains are allowed, we must include the parent domains.
        if self.__include_subdomains:
            for hostname in self.__domains.copy():
                subdomain, domain, suffix = split_hostname(hostname)
                if subdomain:
                    prefix = ".".join( (domain, suffix) )
                    for part in reversed(subdomain.split(".")):
                        self.__domains.add(prefix)
                        prefix = ".".join( (part, prefix) )

        # Resolve each domain name.
        dns_registers = []
        for domain in self.__domains:

            # Resolve the IPv4 addresses.
            dns_registers.extend( DNS.get_a(domain) )

            # Resolve the IPv6 addresses.
            dns_registers.extend( DNS.get_aaaa(domain) )

        # If no IP addresses could be resolved, abort the audit.
        if self.__domains and not dns_registers:
            raise RuntimeError(
                "No IP addresses could be resolved from"
                " the target domains, aborting audit!"
            )

        # Add the addresses to the set of target addresses.
        for register in dns_registers:
            self.__addresses.add(register.address)


    #--------------------------------------------------------------------------
    def get_targets(self):
        """
        Get the audit targets as Data objects.

        :returns: Data objects.
        :rtype: list(Data)
        """
        result = []
        result.extend( IP(address) for address in self.__addresses )
        result.extend( Domain(domain) for domain in self.__domains )
        result.extend( Url(url) for url in self.__web_pages )
        return result


    #--------------------------------------------------------------------------
    def __repr__(self):
        result = ["<Audit scope:\n"]
        if self.__addresses:
            result.append("\tIP addresses:\n")
            for address in sorted(self.__addresses):
                result.append("\t\t%s\n" % address)
        if self.__domains:
            result.append("\tDomains:\n")
            for domain in sorted(self.__domains):
                result.append("\t\t%s\n" % domain)
        if self.__web_pages:
            result.append("\tWeb pages:\n")
            for url in sorted(self.__web_pages):
                result.append("\t\t%s\n" % url)
        result.append(">")
        return "".join(result)


    #--------------------------------------------------------------------------
    def __contains__(self, target):
        """
        Tests if the given target is included in the current audit scope.

        :param target: Target. May be an URL, a hostname or an IP address.
        :type target: str

        :returns: True if the target is in scope, False otherwise.
        :rtype: bool
        """

        # Trivial case.
        if not target:
            return False

        # Check the data type.
        if not isinstance(target, str):
            if not isinstance(target, unicode):
                raise TypeError("Expected str, got %s instead" % type(target))
            target = str(target)

        # Keep the original string for error reporting.
        original = target

        # If it's an URL...
        try:
            parsed_url = ParsedURL(target)
        except Exception:
            parsed_url = None
        if parsed_url is not None:

            # Extract the host and use it as target.
            target = parsed_url.host

        # If it's an IP address...
        try:
            if target.startswith("[") and target.endswith("]"):
                IPAddress(target[1:-1], version=6)
                address = target[1:-1]
            else:
                IPAddress(target)
                address = target
        except Exception:
            address = None
        if address is not None:

            # Test if it's one of the target IP addresses.
            return address in self.__addresses

        # If it's a domain name...
        if self._re_is_domain.match(target):

            # Convert the target to lowercase.
            target = target.lower()

            # Test if the domain is one of the targets. If subdomains are
            # allowed, check if it's a subdomain of a target domain.
            return target in self.__domains or (
                self.__include_subdomains and
                any(target.endswith("." + domain) for domain in self.__domains)
            )

        # We don't know what this is, so we'll consider it out of scope.
        warnings.warn(
            "Can't determine if this is out of scope or not: %r" % original,
            stacklevel=2
        )
        return False


#------------------------------------------------------------------------------
class DummyScope (object):
    """
    Dummy scope tells you everything is in scope, all the time.
    """

    def __init__(self):
        pass

    def get_targets(self):
        return []

    def __contains__(self, target):
        return True
