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


from golismero.api.data import Data
from golismero.api.data.db import Database
from golismero.common import AuditConfig, OrchestratorConfig
from golismero.main.testing import PluginTester

from plugins.testing.scan.openvas import VulnscanManager
from threading import Semaphore
from functools import partial

host         = "192.168.56.101"
user         = "admin"
password     = "admin"
target       = "192.168.56.101"
profile      = "Full and fast"

global sem

#----------------------------------------------------------------------
def test_launch_scan():
    print "Testing launching an OpenVAS scan..."
    sem = Semaphore(0)
    manager = VulnscanManager(host, user, password)
    scan_id, target_id = manager.launch_scan(
        target, profile=profile,
        callback_end=partial(lambda x: x.release(), sem),
        callback_progress=callback_step
    )
    sem.acquire()
    print manager.get_results(scan_id)

def test_get_info():
    print "Testing OpenVAS manager properties..."
    manager = VulnscanManager(host, user, password)
    print "All scans"
    print manager.get_all_scans
    print "Finished scans"
    print manager.get_finished_scans
    print "Running scans"
    print manager.get_running_scans
    print "Available profiles"
    print manager.get_profiles


sem = None # For control the interval

def test_callback():
    print "Testing openvas lib callbacks..."

    sem = Semaphore(0)
    manager = VulnscanManager(host, user, password)

    # Launch
    manager.launch_scan(target, profile="empty",
                        callback_end=partial(lambda x: x.release(), sem),
                        callback_progress=callback_step)

    # Wait
    sem.acquire()

    print "Finished callback test!"

#----------------------------------------------------------------------
def callback_step(a):
    print "OpenVAS status: %s" % str(a)


#----------------------------------------------------------------------
def test_status():
    manager = VulnscanManager(host, user, password)

    print "Testing OpenVAS status..."
    print manager.get_progress("4aa8df2f-3b35-4c1e-8c26-74202f02dd12")


#----------------------------------------------------------------------
def test_import():
    print "Testing OpenVAS importer..."
    orchestrator_config = OrchestratorConfig()
    orchestrator_config.ui_mode = "disabled"
    audit_config = AuditConfig()
    audit_config.targets  = ["192.168.56.101"]
    audit_config.audit_db = "memory://"
    with PluginTester(orchestrator_config, audit_config) as t:
        t.run_plugin("import/xml", path.join(here, "test_openvas.xml"))
        results = Database.get_many( Database.keys(), Data.TYPE_VULNERABILITY )
        assert len(results) == 1
        v = results[0]
        assert v.level == "low"
        assert v.plugin_id == "import/xml"
        assert "Remote web server does not reply with 404 error code." in v.description


#----------------------------------------------------------------------
if __name__ == "__main__":
    test_import()
    test_callback()
    test_get_info()
    test_status()
    test_launch_scan()
