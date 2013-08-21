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
    audit_config.targets = ["www.example.com"]
    audit_config.include_subdomains = True
    with PluginTester(main_config, audit_config) as t:

        assert None not in Config.audit_scope
        assert "" not in Config.audit_scope
        assert "www.example.com" in Config.audit_scope
        assert "example.com" in Config.audit_scope
        assert "com" not in Config.audit_scope
        assert "subdomain.example.com" in Config.audit_scope
        assert "subdomain.www.example.com" in Config.audit_scope
        assert "www.example.org" not in Config.audit_scope
        assert "wwwexample.com" not in Config.audit_scope
        assert "www.wrong.com" not in Config.audit_scope
        assert "127.0.0.1" not in Config.audit_scope
        assert "::1" not in Config.audit_scope
        assert "[::1]" not in Config.audit_scope
        assert "http://www.example.com" in Config.audit_scope
        assert "https://example.com" in Config.audit_scope
        assert "ftp://ftp.example.com" in Config.audit_scope
        assert "mailto://user@example.com" in Config.audit_scope
    ##    assert "user@example.com" in Config.audit_scope
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
    audit_config.targets = ["localhost"]
    audit_config.include_subdomains = True
    with PluginTester(main_config, audit_config) as t:

        assert None not in Config.audit_scope
        assert "" not in Config.audit_scope
        assert "www.example.com" not in Config.audit_scope
        assert "localhost.com" not in Config.audit_scope
        assert "www.localhost.com" not in Config.audit_scope
        assert "localhost" in Config.audit_scope
        assert "subdomain.localhost" in Config.audit_scope
        assert "127.0.0.1" in Config.audit_scope
        assert "::1" in Config.audit_scope
        assert "[::1]" in Config.audit_scope
        assert "http://localhost" in Config.audit_scope
        assert "mailto://user@localhost" in Config.audit_scope
    ##    assert "user@localhost" in Config.audit_scope
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
