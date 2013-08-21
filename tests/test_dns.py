#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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


# Fix the module path for the tests.
import sys
import os
from os import path
try:
    _FIXED_PATH_
except NameError:
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..")
    thirdparty_libs = path.join(golismero, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        sys.path.insert(0, thirdparty_libs)
        sys.path.insert(0, golismero)
    _FIXED_PATH_ = True


# Imports
from golismero.api.net.dns import *
from golismero.api.data.information.dns import *

HOSTS = ["ns1.google.com", "twitter.com", "bing.com", "tuenti.es", "facebook.com", "google.com", "terra.es"]

def test_all_registers():

    print

    for l_host in HOSTS:

        print "Host: %s" % l_host
        print "^" * (len(l_host) + 7)

        for l_dns_type in DnsRegister.DNS_TYPES:

            r = DNS.resolve(l_host, l_dns_type)
            if r:
                print "   Type: " + l_dns_type
                print "   " + ("=" * (len(l_dns_type ) + 6))

                for i, c in enumerate(r):
                    l_properties = [x for x in c.__dict__ if "__" in x]

                    for l_prop in l_properties:
                        l_p = l_prop.find("__") + 2
                        print "     - %s: %s" % (l_prop[l_p:], getattr(c, l_prop))

                print "   " + ("-" * 30)

#----------------------------------------------------------------------
def test_zone_transfer():
    print DNS.zone_transfer("173.194.34.224")
    print DNS.zone_transfer("zonetransfer.me", ["ns12.zoneedit.com"])

#----------------------------------------------------------------------
def test_a_aaaa():

    HOSTS = ["aaaa.terra.es"]

    for h in HOSTS:
        r = DNS.get_a(h, also_CNAME=True)

        for kk in r:

            if kk.type == "CNAME":
                print kk.target
            if kk.type == "A":
                print kk.address

        print ""

#----------------------------------------------------------------------
def test_ptr():
    """
    Try to make a inverse resolution
    """
    ips = ["173.194.34.197"] # google.com

    for ip in ips:
        for t in DNS.get_ptr(ip):
            print t.target


if __name__ == "__main__":
    print
    print "-" * 79
    test_all_registers()
    test_zone_transfer()
    test_a_aaaa()
    test_ptr()
    print "-" * 79
    print
