#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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
from golismero.api.data.resource.url import BaseURL
from golismero.common import AuditConfig, OrchestratorConfig
from golismero.main.testing import PluginTester

from collections import defaultdict


def test_nikto():
    DEBUG = False
    ##DEBUG = True

    plugin_id = "testing/scan/nikto"
    csv_file = "test_nikto.csv"
    print "Testing plugin: %s" % plugin_id
    orchestrator_config = OrchestratorConfig()
    orchestrator_config.ui_mode = "console"
    audit_config = AuditConfig()
    audit_config.targets = ["http://www.example.com", "http://localhost"]
    audit_config.include_subdomains = False
    audit_config.enable_plugins = ["nikto"]
    audit_config.disable_plugins = ["all"]
    with PluginTester(orchestrator_config = orchestrator_config,
                      audit_config = audit_config) as t:

        print "Testing Nikto plugin parser..."
        plugin, plugin_info = t.get_plugin(plugin_id)
        Config._context._PluginContext__plugin_info = plugin_info
        try:
            r, c = plugin.parse_nikto_results(
                BaseURL("http://www.example.com/"), path.join(here, csv_file))
            if DEBUG:
                for d in r:
                    print "-" * 10
                    print repr(d)
            assert c == 6, c
            assert len(r) == 10, len(r)
            c = defaultdict(int)
            for d in r:
                c[d.__class__.__name__] += 1
            #print c
            assert c.pop("IP") == 1
            assert c.pop("URL") == 3
            assert c.pop("UncategorizedVulnerability") == 6
            assert len(c) == 0
        finally:
            Config._context._PluginContext__plugin_info = None

        print "Testing Nikto plugin against localhost..."
        r = t.run_plugin(plugin_id, BaseURL("http://localhost/"))
        for d in r:
            print "\t%r" % d


# Run all tests from the command line.
if __name__ == "__main__":
    test_nikto()
