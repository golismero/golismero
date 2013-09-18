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

__all__ = ["Domain"]

from . import Resource
from .. import identity
from ...config import Config
from ...net.web_utils import split_hostname

from netaddr import IPAddress


#------------------------------------------------------------------------------
class Domain(Resource):
    """
    Domain name.

    This data type maps the domain names to the IP addresses they resolve to.
    """

    resource_type = Resource.RESOURCE_DOMAIN


    #----------------------------------------------------------------------
    def __init__(self, hostname):
        """
        :param hostname: Domain name.
        :type hostname: str
        """

        if not isinstance(hostname, basestring):
            raise TypeError("Expected string, got %r instead" % type(hostname))
        hostname = str(hostname)

        # Check we've not confused an IP address for a hostname.
        try:
            if hostname.startswith("[") and hostname.endswith("]"):
                IPAddress(hostname[1:-1], version=6)
            else:
                IPAddress(hostname)
        except Exception:
            pass
        else:
            raise ValueError("This is an IP address (%s) not a domain!" % hostname)

        # Domain name.
        self.__hostname = hostname

        # Parent constructor.
        super(Domain, self).__init__()

        # Reset the crawling depth.
        self.depth = 0


    #----------------------------------------------------------------------
    def __str__(self):
        return self.hostname


    #----------------------------------------------------------------------
    def __repr__(self):
        return "<Domain name=%r>" % self.hostname


    #----------------------------------------------------------------------
    def is_in_scope(self):
        return self.hostname in Config.audit_scope


    #----------------------------------------------------------------------
    @identity
    def hostname(self):
        """
        :return: Domain name.
        :rtype: str
        """
        return self.__hostname


    #----------------------------------------------------------------------
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


    #----------------------------------------------------------------------

    @property
    def discovered(self):
        domain = self.hostname
        result = []
        subdomain, domain, suffix = split_hostname(domain)
        if subdomain:
            prefix = ".".join( (domain, suffix) )
            for part in reversed(subdomain.split(".")):
                if prefix in Config.audit_scope:
                    result.append( Domain(prefix) )
                prefix = ".".join( (part, prefix) )
        return result
