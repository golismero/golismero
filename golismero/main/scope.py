#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Audit scope checking.
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

__all__ = ["AuditScope", "DummyScope"]

from ..api.data.resource.domain import Domain
from ..api.data.resource.ip import IP
from ..api.data.resource.url import URL
from ..api.net.dns import DNS
from ..api.net.web_utils import ParsedURL, split_hostname
from ..api.text.text_utils import to_utf8

from netaddr import IPAddress, IPNetwork
from socket import getaddrinfo, AF_INET, AF_INET6
from warnings import warn

import re


#------------------------------------------------------------------------------
class AbstractScope (object):


    #--------------------------------------------------------------------------
    def __init__(self, audit_config = None):
        """
        :param audit_config: (Optional) Audit configuration.
        :type audit_config: AuditConfig | None
        """
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def has_scope(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def addresses(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def domains(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def roots(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def web_pages(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    @property
    def targets(self):
        return self.addresses + self.domains + self.roots + self.web_pages


    #--------------------------------------------------------------------------
    def add_targets(self, audit_config, dns_resolution = 1):
        """
        :param audit_config: Audit configuration.
        :type audit_config: AuditConfig

        :param dns_resolution: DNS resolution mode.
            Use 0 to disable, 1 to enable only for new targets (default),
            or 2 to enable for all targets.
        :type dns_resolution: int
        """
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    def get_targets(self):
        """
        Get the audit targets as Data objects.

        :returns: Data objects.
        :rtype: list(Data)
        """
        result = []
        result.extend( IP(address) for address in self.addresses )
        result.extend( Domain(domain) for domain in self.domains )
        result.extend( Domain(root) for root in self.roots )
        result.extend( URL(url) for url in self.web_pages )
        return result


    #--------------------------------------------------------------------------
    def __str__(self):
        raise NotImplementedError()


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<%s>" % self


    #--------------------------------------------------------------------------
    def __contains__(self, target):
        """
        Tests if the given target is included in the current audit scope.

        :param target: Target. May be an URL, a hostname or an IP address.
        :type target: str

        :returns: True if the target is in scope, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError()


#------------------------------------------------------------------------------
class AuditScope (AbstractScope):
    """
    Audit scope.

    Example:

        >>> from golismero.api.config import Config
        >>> 'www.example.com' in Config.audit_scope
        True
        >>> 'www.google.com' in Config.audit_scope
        False
    """

    _re_is_domain = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\_\-\.]*[A-Za-z0-9]$")


    #--------------------------------------------------------------------------
    def __init__(self, audit_config = None):

        # This is where we'll keep the parsed targets.
        self.__domains   = set()   # Domain names.
        self.__roots     = set()   # Domain names for subdomain matching.
        self.__addresses = set()   # IP addresses.
        self.__web_pages = set()   # URLs.

        # Add the targets from the audit config if given.
        if audit_config is not None:
            self.add_targets(audit_config)


    #--------------------------------------------------------------------------
    @property
    def has_scope(self):
        return True


    #--------------------------------------------------------------------------
    @property
    def addresses(self):
        return sorted(self.__addresses)


    #--------------------------------------------------------------------------
    @property
    def domains(self):
        return sorted(self.__domains)


    #--------------------------------------------------------------------------
    @property
    def roots(self):
        return sorted(self.__roots)


    #--------------------------------------------------------------------------
    @property
    def web_pages(self):
        return sorted(self.__web_pages)


    #--------------------------------------------------------------------------
    def add_targets(self, audit_config, dns_resolution = 1):

        # Validate the arguments.
        if dns_resolution not in (0, 1, 2):
            raise ValueError(
                "Argument 'dns_resolution' can only be 0, 1 or 2,"
                " got %r instead" % dns_resolution)

        # Remember if subdomains are allowed.
        include_subdomains = audit_config.include_subdomains

        # We'll remember here what *new* domains were added, for IP resolution.
        new_domains = set()

        # For each user-supplied target string...
        for target in audit_config.targets:
            target = to_utf8(target)

            # If it's an IP address...
            try:
                # For IPv6 address
                if target.startswith("[") and target.endswith("]"):
                    IPAddress(target[1:-1], version=6)
                    address = target[1:-1]
                else:
                    # IPv4
                    IPAddress(target)
                    address = target
            except Exception:
                ##raise  # XXX DEBUG
                address = None
            if address is not None:

                # Keep the IP address.
                self.__addresses.add(address)

            # If it's an IP network...
            else:
                try:
                    network = IPNetwork(target)
                except Exception:
                    ##raise  # XXX DEBUG
                    network = None
                if network is not None:

                    # For each host IP address in range...
                    for address in network.iter_hosts():
                        address = str(address)

                        # Keep the IP address.
                        self.__addresses.add(address)

                # If it's a domain name...
                elif self._re_is_domain.match(target):

                    # Convert it to lowercase.
                    target = target.lower()

                    # Is the domain new?
                    if target not in self.__domains:

                        # Keep the domain name.
                        self.__domains.add(target)
                        new_domains.add(target)

                # If it's an URL...
                else:
                    try:
                        parsed_url = ParsedURL(target)
                        url = parsed_url.url
                    except Exception:
                        ##raise  # XXX DEBUG
                        url = None
                    if url is not None:

                        # Keep the URL.
                        self.__web_pages.add(url)

                        # If we allow parent folders...
                        if audit_config.allow_parent:

                            # Add the base URL too.
                            self.__web_pages.add(parsed_url.base_url)

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
                            ##raise  # XXX DEBUG
                            host = host.lower()
                            if host not in self.__domains:
                                self.__domains.add(host)
                                new_domains.add(host)

                    # If it's none of the above, fail.
                    else:
                        raise ValueError(
                            "I don't know what to do with this: %s" % target)

        # If subdomains are allowed, we must include the parent domains.
        if include_subdomains:
            for hostname in new_domains.copy():
                subdomain, domain, suffix = split_hostname(hostname)
                if subdomain:
                    prefix = ".".join( (domain, suffix) )
                    for part in reversed(subdomain.split(".")):
                        if prefix not in self.__roots and \
                           prefix not in self.__domains:
                            new_domains.add(prefix)
                        self.__domains.add(prefix)
                        self.__roots.add(prefix)
                        prefix = ".".join( (part, prefix) )
                else:
                    self.__roots.add(hostname)

        # Resolve each (new?) domain name and add the IP addresses as targets.
        if dns_resolution:
            if dns_resolution == 1:
                domains_to_resolve = new_domains
            else:
                domains_to_resolve = self.__domains
            for domain in domains_to_resolve:
                resolved = set(
                    entry[4][0]
                    for entry in getaddrinfo(domain, 80)
                    if entry[0] in (AF_INET, AF_INET6)
                )
                if resolved:
                    self.__addresses.update(resolved)
                else:
                    msg = "Cannot resolve domain name: %s" % domain
                    warn(msg, RuntimeWarning)


    #--------------------------------------------------------------------------
    def __str__(self):
        result = ["Audit scope:\n"]
        addresses = self.addresses
        if addresses:
            result.append("\nIP addresses:\n")
            for address in addresses:
                result.append("    %s\n" % address)
        domains = ["*." + domain for domain in self.roots]
        domains.extend(self.domains)
        if domains:
            result.append("\nDomains:\n")
            for domain in domains:
                result.append("    %s\n" % domain)
        web_pages = self.web_pages
        if web_pages:
            result.append("\nWeb pages:\n")
            for url in web_pages:
                result.append("    %s\n" % url)
        return "".join(result)


    #--------------------------------------------------------------------------
    def __contains__(self, target):

        # Trivial case.
        if not target:
            return False

        # Check the data type.
        if not isinstance(target, str):
            if not isinstance(target, unicode):
                raise TypeError("Expected str, got %r instead" % type(target))
            target = to_utf8(target)

        # Keep the original string for error reporting.
        original = target

        # If it's an URL...
        try:
            parsed_url = ParsedURL(target)
        except Exception:
            parsed_url = None
        if parsed_url is not None:
            if not parsed_url.scheme:
                parsed_url = None
            else:

                # Extract the host and use it as target.
                # We'll be doing some extra checks later on, though.
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
            in_scope = address in self.__addresses

        # If it's a domain name...
        elif self._re_is_domain.match(target):

            # Convert the target to lowercase.
            target = target.lower()

            # Test if the domain is one of the targets. If subdomains are
            # allowed, check if it's a subdomain of a target domain.
            in_scope = (
                target in self.__domains or
                any(
                    target.endswith("." + domain)
                    for domain in self.__roots
                )
            )

        # We don't know what this is, so we'll consider it out of scope.
        else:
            ##raise ValueError(
            ##    "Can't determine if this is out of scope or not: %r"
            ##    % original)
            warn(
                "Can't determine if this is out of scope or not: %r"
                    % original,
                stacklevel=2
            )
            return False

        # If it's in scope...
        if in_scope:

            # If it's an URL, check the path as well.
            # If not within the allowed paths, it's out of scope.
            if parsed_url is not None and \
                            parsed_url.scheme in ("http", "https", "ftp"):
                path = parsed_url.path
                for base_url in self.__web_pages:
                    parsed_url = ParsedURL(base_url)
                    if path.startswith(parsed_url.path) and \
                                parsed_url.scheme in ("http", "https", "ftp"):
                        return True
                return False

            # Return True if in scope.
            return True

        # Return False if out of scope.
        return False


#------------------------------------------------------------------------------
class DummyScope (AbstractScope):
    """
    Dummy scope tells you everything is in scope, all the time.
    """

    def __init__(self):
        pass

    @property
    def has_scope(self):
        return False

    @property
    def addresses(self):
        return []

    @property
    def domains(self):
        return []

    @property
    def roots(self):
        return []

    @property
    def web_pages(self):
        return []

    def get_targets(self):
        return []

    def __contains__(self, target):
        return True

    def __str__(self):
        return (
            "Audit scope:\n"
            "\n"
            "IP addresses:\n"
            "    *\n"
            "\n"
            "Domains:\n"
            "    *\n"
            "\n"
            "Web pages:\n"
            "    *\n"
        )
