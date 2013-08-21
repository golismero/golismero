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


# Imports.
from golismero.api.text.text_utils import generate_random_string
from golismero.database.cachedb import VolatileNetworkCache, PersistentNetworkCache
import time


# Fake audit name for the tests.
audit = "fake_audit"


# Tests the network caches consistency.
def test_cachedb_consistency():
    mem = VolatileNetworkCache()
    disk = PersistentNetworkCache()
    disk.clean(audit)
    try:

        print "Testing consistency of in-memory and disk caches..."
        for x in xrange(100):
            key = generate_random_string(10)
            data = generate_random_string(100)
            helper_test_cachedb_consistency(mem, key, data)
            helper_test_cachedb_consistency(disk, key, data)

        print "Testing disk cache compacting and dumping..."
        disk.compact()
        disk.dump("test_cachedb.sql")

        print "Cleaning up the memory cache..."
        mem.clean(audit)
        del mem

    finally:
        print "Cleaning up the disk cache..."
        try:
            disk.clean(audit)
        finally:
            disk.close()

def helper_test_cachedb_consistency(db, key, data):
    db.set(audit, key, data, protocol="http")
    db.set(audit, key, data, protocol="https")
    assert db.exists(audit, key, protocol="http")
    assert db.exists(audit, key, protocol="https")
    assert not db.exists(audit, key + "A", protocol="http")
    assert not db.exists(audit, key + "A", protocol="https")
    assert not db.exists(audit + "A", key + "A", protocol="http")
    assert not db.exists(audit + "A", key + "A", protocol="https")
    assert db.get(audit, key, protocol="http") == data
    assert db.get(audit, key, protocol="https") == data
    assert db.get(audit, key, protocol="HTTP") == data
    assert db.get(audit, key, protocol="https://www.example.com") == data
    assert db.get(audit, key + "A", protocol="http") is None
    assert db.get(audit, key + "A", protocol="https") is None
    assert db.get(audit + "A", key + "A", protocol="http") is None
    assert db.get(audit + "A", key + "A", protocol="https") is None
    db.remove(audit, key, protocol="http")
    assert not db.exists(audit, key, protocol="http")
    assert db.get(audit, key, protocol="http") is None
    assert db.exists(audit, key, protocol="https")
    assert db.get(audit, key, protocol="https") == data


# Benchmark for the disk cache.
def test_cachedb_stress():
    disk = PersistentNetworkCache()
    disk.clean(audit)
    try:

        print "Stress testing the disk cache..."
        helper_cachedb_stress(disk, 10)
        helper_cachedb_stress(disk, 20)
        helper_cachedb_stress(disk, 30)
        helper_cachedb_stress(disk, 100)

    finally:
        print "Cleaning up the disk cache..."
        try:
            disk.clean(audit)
        finally:
            disk.close()

def helper_cachedb_stress(disk, n):
    print "  Testing %d items..." % (n * 2)
    data1 = "A" * 10000000
    data2 = "B" * 10000000
    keys = set()
    for x in xrange(n):
        key = generate_random_string()
        keys.add(key)
    t1 = time.time()
    print "  -> Writing..."
    for key in keys:
        disk.set(audit, key, data1, protocol="http")
        disk.set(audit, key, data2, protocol="https")
    t2 = time.time()
    print "  -- Checking..."
    for key in keys:
        assert disk.exists(audit, key, protocol="http")
        assert disk.exists(audit, key, protocol="https")
    t3 = time.time()
    print "  <- Reading..."
    for key in keys:
        assert disk.get(audit, key, protocol="http") != disk.get(audit, key, protocol="https")
    t4 = time.time()
    print "  Write time: %d seconds (%f seconds per item)" % (t2 - t1, (t2 - t1) / (n * 2.0))
    print "  Check time: %d seconds (%f seconds per item)" % (t3 - t2, (t3 - t2) / (n * 2.0))
    print "  Read time:  %d seconds (%f seconds per item)" % (t4 - t3, (t4 - t3) / (n * 2.0))
    print "  Total time: %d seconds (%f seconds per item)" % (t4 - t1, (t4 - t1) / (n * 2.0))


# Run all tests from the command line.
if __name__ == "__main__":
    test_cachedb_consistency()
    test_cachedb_stress()
