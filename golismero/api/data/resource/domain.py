#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Domain name.
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

__all__ = ["Domain", "RootDomain"]

from . import Resource
from .. import identity
from ...config import Config
from ...net.web_utils import split_hostname
from ...text.text_utils import to_utf8

from netaddr import IPAddress

import re


#------------------------------------------------------------------------------
class Domain(Resource):
    """
    Domain name.

    This data type maps the root domain names
    to the IP addresses they resolve to.
    """

    data_subtype = "domain"

    _re_is_domain = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\_\-\.]*[A-Za-z0-9]$")


    #--------------------------------------------------------------------------
    def __init__(self, hostname):
        """
        :param hostname: Domain name.
        :type hostname: str
        """

        hostname = to_utf8(hostname)
        if not isinstance(hostname, str):
            raise TypeError(
                "Expected string, got %r instead" % type(hostname))
        if not hostname:
            raise ValueError("Missing hostname")

        # Check we've not confused an IP address for a hostname.
        try:
            if hostname.startswith("[") and hostname.endswith("]"):
                IPAddress(hostname[1:-1], version=6)
            else:
                IPAddress(hostname)
        except Exception:
            pass
        else:
            raise ValueError(
                "This is an IP address (%s) not a domain!" % hostname)

        # Make sure the hostname is valid.
        if not self._re_is_domain.match(hostname):
            raise ValueError("Invalid domain name: %r" % hostname)

        # Domain name.
        self.__hostname = hostname

        # Parent constructor.
        super(Domain, self).__init__()

        # Reset the crawling depth.
        self.depth = 0


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.hostname


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<Domain name=%r>" % self.hostname


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Domain Name"


    #--------------------------------------------------------------------------
    def is_in_scope(self, scope = None):
        if scope is None:
            scope = Config.audit_scope
        return self.hostname in scope


    #--------------------------------------------------------------------------
    @identity
    def hostname(self):
        """
        :return: Domain name.
        :rtype: str
        """
        return self.__hostname


    #--------------------------------------------------------------------------
    @property
    def root(self):
        """
        :return: Root domain. i.e: www.mysite.com -> mysite.com
        :rtype: str
        """
        _, domain, suffix = split_hostname(self.hostname)
        if suffix:
            return "%s.%s" % (domain, suffix)
        return domain


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        domain = self.hostname
        result = [RootDomain(self.root)]
        subdomain, domain, suffix = split_hostname(domain)
        if subdomain:
            prefix = ".".join( (domain, suffix) )
            for part in reversed(subdomain.split(".")):
                if prefix in Config.audit_scope:
                    result.append( Domain(prefix) )
                prefix = ".".join( (part, prefix) )
        return result


#------------------------------------------------------------------------------
class RootDomain(Domain):
    """
    Root domain name.

    This data type maps the domain names to the IP addresses they resolve to.
    """

    data_subtype = "root_domain"


    #--------------------------------------------------------------------------
    def __init__(self, hostname):

        # Parent constructor.
        super(RootDomain, self).__init__(hostname)

        # Make sure it's really a root domain.
        if self.hostname != self.root:
            raise ValueError(
                "Domain %s is not a root domain" % self.hostname)


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<Root Domain name=%r>" % self.hostname


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "Root Domain Name"


    #--------------------------------------------------------------------------
    @property
    def root(self):
        """
        Alias of "hostname", to ensure both Domain and RootDomain have
        the same interface.

        :return: Root domain.
        :rtype: str
        """
        return self.hostname


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        return [Domain(self.hostname)]
