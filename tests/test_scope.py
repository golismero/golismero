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
here = path.split(path.abspath(__file__))[0]
if not here:  # if it fails use cwd instead
    here = path.abspath(os.getcwd())
golismero = path.join(here, "..")
thirdparty_libs = path.join(golismero, "thirdparty_libs")
if path.exists(thirdparty_libs):
    sys.path.insert(0, thirdparty_libs)
    sys.path.insert(0, golismero)


from golismero.api.config import Config
from golismero.api.net.dns import DNS
from golismero.common import AuditConfig, OrchestratorConfig
from golismero.main.testing import PluginTester

from socket import gethostbyname, gethostbyname_ex


def test_scope_example():
    print "Testing scope with: www.example.com"
    main_config = OrchestratorConfig()
    main_config.ui_mode = "disabled"
    main_config.use_colors = False
    audit_config = AuditConfig()
    audit_config.targets = ["http://www.example.com"]
    audit_config.include_subdomains = True
    with PluginTester(main_config, audit_config) as t:
        print Config.audit_scope

        for token, flag in (
            (None, False),
            ("", False),
            ("www.example.com", True),
            ("example.com", True),
            ("com", False),
            ("subdomain.example.com", True),
            ("subdomain.www.example.com", True),
            ("www.example.org", False),
            ("wwwexample.com", False),
            ("www.wrong.com", False),
            ("127.0.0.1", False),
            ("::1", False),
            ("[::1]", False),
            ("http://www.example.com", True),
            ("https://example.com", True),
            ("ftp://ftp.example.com", True),
            ("mailto://user@example.com", True),
            ##("user@example.com", True),
        ):
            assert ((token in Config.audit_scope) == flag), repr(token)

        assert gethostbyname("www.example.com") in Config.audit_scope
        for address in gethostbyname_ex("www.example.com")[2]:
            assert address in Config.audit_scope
        for register in DNS.get_a("www.example.com"):
            assert register.address in Config.audit_scope
        for register in DNS.get_aaaa("www.example.com"):
            assert register.address in Config.audit_scope
            assert "[%s]" % register.address in Config.audit_scope
        for register in DNS.get_a("www.google.com"):
            assert register.address not in Config.audit_scope
        for register in DNS.get_aaaa("www.google.com"):
            assert register.address not in Config.audit_scope
            assert "[%s]" % register.address not in Config.audit_scope


def test_scope_localhost():
    print "Testing scope with: localhost"
    main_config = OrchestratorConfig()
    main_config.ui_mode = "disabled"
    main_config.use_colors = False
    audit_config = AuditConfig()
    audit_config.targets = ["http://localhost/"]
    audit_config.include_subdomains = True
    audit_config.allow_parent = True
    with PluginTester(main_config, audit_config) as t:
        print Config.audit_scope

        for token, flag in (
            (None, False),
            ("", False),
            ("www.example.com", False),
            ("localhost.com", False),
            ("www.localhost.com", False),
            ("subdomain.localhost", True),
            ("127.0.0.1", True),
            ("::1", True),
            ("[::1]", True),
            ("http://localhost", True),
            ("https://localhost", True),
            ("ftp://ftp.localhost", True),
            ("mailto://user@localhost", True),
            ##("user@localhost", True),
        ):
            assert ((token in Config.audit_scope) == flag), repr(token)

        assert gethostbyname("localhost") in Config.audit_scope
        for address in gethostbyname_ex("localhost")[2]:
            assert address in Config.audit_scope
        for register in DNS.get_a("localhost"):
            assert register.address in Config.audit_scope
        for register in DNS.get_aaaa("localhost"):
            assert register.address in Config.audit_scope
            assert "[%s]" % register.address in Config.audit_scope
        for register in DNS.get_a("www.google.com"):
            assert register.address not in Config.audit_scope
        for register in DNS.get_aaaa("www.google.com"):
            assert register.address not in Config.audit_scope
            assert "[%s]" % register.address not in Config.audit_scope


# Run all tests from the command line.
if __name__ == "__main__":
    test_scope_localhost()
    test_scope_example()
