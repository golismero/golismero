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


# Imports.
from golismero.api.data import Data
from golismero.api.data.information.text import Text
from golismero.api.data.resource.url import URL
from golismero.api.data.vulnerability.information_disclosure.url_disclosure \
    import UrlDisclosure
from golismero.api.text.text_utils import generate_random_string
from golismero.database.auditdb import AuditDB, BaseAuditDB, AuditSQLiteDB
from golismero.common import AuditConfig, OrchestratorConfig
from golismero.main.testing import PluginTester
import time
import os
import inspect


# Tests the audit DB interfaces.
def test_auditdb_interfaces():
    print "Testing the AuditDB interfaces..."
    from golismero.database import auditdb
    for name in dir(auditdb):
        if name[0] == "_":
            continue
        cls = getattr(auditdb, name)
        if inspect.isclass(cls) and cls is not AuditDB and cls is not BaseAuditDB and issubclass(cls, BaseAuditDB):
            print ("..." + cls.__name__),
            missing = {
                name for name in dir(cls) if (
                    name[0] != "_" and
                    name not in ("audit_name", "compact", "dump", "decode", "encode", "generate_audit_name", "get_config_from_closed_database", "mark_stage_finished_many") and
                    name not in cls.__dict__
                )
            }
            if missing:
                print "FAIL!"
                print "Missing methods: " + ", ".join(sorted(missing))
                assert False
            print "Ok."


# Tests the audit DB for consistency.
def test_auditdb_consistency():
    print "Testing consistency of in-memory database..."
    helper_test_auditdb_consistency_setup("fake_mem_audit", ":memory:")
    print "Testing consistency of disk database..."
    helper_test_auditdb_consistency_setup(None, ":auto:")

def helper_test_auditdb_consistency_setup(audit_name, audit_db):
    main_config = OrchestratorConfig()
    main_config.ui_mode = "disabled"
    audit_config = AuditConfig()
    audit_config.targets = ["www.example.com"]
    audit_config.audit_name = audit_name
    audit_config.audit_db = audit_db
    with PluginTester(main_config, audit_config) as t:
        print "--> Testing general consistency..."
        helper_test_auditdb_general_consistency(t.audit.database)
        print "--> Testing data consistency..."
        for x in xrange(100):
            key  = generate_random_string(10)
            data = generate_random_string(100)
            helper_test_auditdb_data_consistency(t.audit.database, key, data)

def helper_test_auditdb_general_consistency(db):

    # Test the shared sets.
    try:
        db.remove_shared_values("FAKE", ("FAKE",))
    except KeyError:
        pass
    db.add_shared_values("fake_set_id", (
        "string",
        u"unicode",
        100,
        200L,
        5.0,
        True,
        False,
        complex(1, 1),
        None,
        frozenset({"string", 100, 1.0}),
        (None, True, False),
    ))
    assert db.has_all_shared_values("fake_set_id", (
        "string",
        u"unicode",
        100,
        200L,
        5.0,
        True,
        False,
        complex(1, 1),
        None,
        frozenset({"string", 100, 1.0}),
        (None, True, False),
    ))
    assert db.has_any_shared_value("fake_set_id", (
        "string",
        "FAKE",
    ))
    assert all(db.has_each_shared_value("fake_set_id", (
        "string",
        u"unicode",
        100,
        200L,
        5.0,
        True,
        False,
        complex(1, 1),
        None,
        frozenset({"string", 100, 1.0}),
        (None, True, False),
    )))
    total = db.pop_shared_values("fake_set_id", 11)
    assert len(total) == 11
    assert set(total) == set((
        "string",
        u"unicode",
        100,
        200L,
        5.0,
        True,
        False,
        complex(1, 1),
        None,
        frozenset({"string", 100, 1.0}),
        (None, True, False),
    ))
    assert not db.has_any_shared_value("fake_set_id", total)
    db.add_shared_values("fake_set_id", total)
    assert db.has_all_shared_values("fake_set_id", total)
    popped = db.pop_shared_values("fake_set_id", 5)
    assert len(popped) == 5
    assert set(popped) == set(popped).intersection(total)
    db.add_shared_values("fake_set_id", popped)
    db.add_shared_values("fake_set_id", popped)
    db.remove_shared_values("fake_set_id", popped)
    assert not db.has_any_shared_value("fake_set_id", popped)
    db.remove_shared_values("fake_set_id", popped)
    popped_2 = db.pop_shared_values("fake_set_id", 1000000000)
    assert len(popped) + len(popped_2) == len(total)
    assert not set(popped).intersection(popped_2)
    assert set(popped + popped_2) == set(total)
    assert not db.pop_shared_values("fake_set_id", 1)

    # Test the shared maps.
    try:
        db.delete_mapped_values("FAKE", ("FAKE",))
    except KeyError:
        pass
    db.put_mapped_values("fake_map_id", (
        ("a_string", "string"),
        ("a_unicode_string", u"unicode"),
        ("an_integer", 100),
        ("a_long", 200L),
        ("a_float", 5.0),
        ("a_bool", True),
        ("another_bool", False),
        ("a_complex", complex(1, 1)),
        ("none", None),
        ("a_frozenset", frozenset({"string", 100, 1.0})),
        ("a_tuple", (None, True, False)),
    ))
    assert db.get_mapped_keys("fake_map_id") == set((
        "a_string",
        "a_unicode_string",
        "an_integer",
        "a_long",
        "a_float",
        "a_bool",
        "another_bool",
        "a_complex",
        "none",
        "a_frozenset",
        "a_tuple",
    ))
    assert db.get_mapped_values("fake_map_id", (
        "a_string",
        "a_unicode_string",
        "an_integer",
        "a_long",
        "a_float",
        "a_bool",
        "another_bool",
        "a_complex",
        "none",
        "a_frozenset",
        "a_tuple",
    )) == (
        "string",
        u"unicode",
        100,
        200L,
        5.0,
        True,
        False,
        complex(1, 1),
        None,
        frozenset({"string", 100, 1.0}),
        (None, True, False),
    )
    assert db.has_all_mapped_keys("fake_map_id", (
        "a_string",
        "a_unicode_string",
        "an_integer",
        "a_long",
        "a_float",
        "a_bool",
        "another_bool",
        "a_complex",
        "none",
        "a_frozenset",
        "a_tuple",
    ))
    assert not db.has_all_mapped_keys("fake_map_id", (
        "a_string",
        "FAKE",
    ))
    assert db.has_any_mapped_key("fake_map_id", (
        "a_string",
        "FAKE",
    ))
    assert all(db.has_each_mapped_key("fake_map_id", (
        "a_string",
        "a_unicode_string",
        "an_integer",
        "a_long",
        "a_float",
        "a_bool",
        "another_bool",
        "a_complex",
        "none",
        "a_frozenset",
        "a_tuple",
    )))
    assert db.swap_mapped_values("fake_map_id",
        (("a_string", u"unicode"), ("a_unicode_string", "string"))) == \
        (("string", u"unicode"))
    assert db.pop_mapped_values("fake_map_id", ("a_string", "a_unicode_string")) == \
           (u"unicode", "string")
    assert not db.has_any_mapped_key("fake_map_id", ("a_string", "a_unicode_string"))
    assert db.get_mapped_keys("fake_map_id") == set((
        "an_integer",
        "a_long",
        "a_float",
        "a_bool",
        "another_bool",
        "a_complex",
        "none",
        "a_frozenset",
        "a_tuple",
    ))
    try:
        print db.get_mapped_values("fake_map_id", ("a_string", "a_unicode_string", "a_float"))
        assert False
    except KeyError:
        pass
    db.delete_mapped_values("fake_map_id", ("a_string", "a_unicode_string", "a_float"))
    try:
        print db.get_mapped_values("fake_map_id", ("a_float",))
        assert False
    except KeyError:
        pass
    try:
        print db.pop_mapped_values("fake_map_id", ("a_long", "a_float"))
        assert False
    except KeyError:
        pass
    assert db.pop_mapped_values("fake_map_id", ("a_long",)) == (200L,)
    try:
        print db.pop_mapped_values("fake_map_id", ("a_long",))
        assert False
    except KeyError:
        pass
    db.put_mapped_values("fake_map_id", (
        ("an_integer", 500),
    ))
    assert db.pop_mapped_values("fake_map_id", ("an_integer",)) == (500,)
    try:
        print db.pop_mapped_values("fake_map_id", ("an_integer",))
        assert False
    except KeyError:
        pass

    # Make sure shared maps and sets can't be confused.
    assert not db.has_any_shared_value("fake_map_id", ("another_bool",))
    try:
        print db.get_mapped_values("fake_set_id", ("string",))
        assert False
    except KeyError:
        pass


def helper_test_auditdb_data_consistency(db, key, data):
    assert isinstance(db, BaseAuditDB)

    # Test the database start and end times.
    db.set_audit_times(None, None)
    assert db.get_audit_times() == (None, None)
    db.set_audit_start_time(1)
    assert db.get_audit_times() == (1, None)
    db.set_audit_stop_time(2)
    assert db.get_audit_times() == (1, 2)
    db.set_audit_start_time(None)
    assert db.get_audit_times() == (None, 2)
    db.set_audit_stop_time(None)
    assert db.get_audit_times() == (None, None)

    # Create some fake data and add it to the database.
    d1 = URL("http://www.example.com/" + key)
    d2 = Text(data)
    d3 = UrlDisclosure(d1)
    d1.add_information(d2)
    assert d1.links == {d2.identity, d3.identity}
    assert d2.links == {d1.identity}
    assert d3.links == {d1.identity}
    db.add_data(d1)
    db.add_data(d2)
    db.add_data(d3)

    # Test has_data_key().
    assert db.has_data_key(d1.identity)
    assert db.has_data_key(d2.identity)
    assert db.has_data_key(d3.identity)

    # Test get_data().
    d1p = db.get_data(d1.identity)
    d2p = db.get_data(d2.identity)
    d3p = db.get_data(d3.identity)
    assert d1p is not None
    assert d2p is not None
    assert d3p is not None
    assert d1p.identity == d1.identity
    assert d2p.identity == d2.identity
    assert d3p.identity == d3.identity
    assert d1p.links == d1.links, (d1p.links, d1.links)
    assert d2p.links == d2.links
    assert d3p.links == d3.links

    # Test get_data_types().
    assert db.get_data_types((d1.identity, d2.identity, d3.identity)) == {(d1.data_type, d1.resource_type), (d2.data_type, d2.information_type), (d3.data_type, d3.vulnerability_type)}, (db.get_data_types((d1.identity, d2.identity, d3.identity)), {(d1.data_type, d1.resource_type), (d2.data_type, d2.information_type), (d3.data_type, d3.vulnerability_type)})

    # Test get_data_count().
    assert db.get_data_count() == 3
    assert db.get_data_count(d1.data_type) == 1
    assert db.get_data_count(d2.data_type) == 1
    assert db.get_data_count(d3.data_type) == 1
    assert db.get_data_count(data_subtype = d1.resource_type) == 1
    assert db.get_data_count(data_subtype = d2.information_type) == 1
    assert db.get_data_count(data_subtype = d3.vulnerability_type) == 1

    # Test get_many_data().
    assert {x.identity for x in db.get_many_data((d1.identity, d2.identity, d3.identity))} == {d1.identity, d2.identity, d3.identity}

    # Test stage and plugin completion logic.
    # XXX TODO

    # Test remove_data().
    db.remove_data(d1.identity)
    db.remove_data(d2.identity)
    db.remove_data(d3.identity)
    assert not db.has_data_key(d1.identity)
    assert not db.has_data_key(d2.identity)
    assert not db.has_data_key(d3.identity)
    assert db.get_data_count() == 0
    assert db.get_data_count(d1.data_type) == 0
    assert db.get_data_count(d2.data_type) == 0
    assert db.get_data_count(d3.data_type) == 0
    assert db.get_data_count(d1.data_type, d1.resource_type) == 0
    assert db.get_data_count(d2.data_type, d2.information_type) == 0
    assert db.get_data_count(d3.data_type, d3.vulnerability_type) == 0
    assert db.get_data_count(data_subtype = d1.resource_type) == 0
    assert db.get_data_count(data_subtype = d2.information_type) == 0
    assert db.get_data_count(data_subtype = d3.vulnerability_type) == 0
    assert db.get_data_types((d1.identity, d2.identity, d3.identity)) == set()
    assert db.get_data(d1.identity) is None
    assert db.get_data(d2.identity) is None
    assert db.get_data(d3.identity) is None


# Benchmark for the disk database.
def test_auditdb_stress():

    print "Stress testing the memory database..."
    helper_auditdb_stress(10,   ":memory:")
    helper_auditdb_stress(20,   ":memory:")
    helper_auditdb_stress(30,   ":memory:")
    helper_auditdb_stress(100,  ":memory:")
    helper_auditdb_stress(1000, ":memory:")

    print "Stress testing the disk database..."
    helper_auditdb_stress(10)
    helper_auditdb_stress(20)
    helper_auditdb_stress(30)
    helper_auditdb_stress(100)
    helper_auditdb_stress(1000)

def helper_auditdb_stress(n, dbname = ":auto:"):
    main_config = OrchestratorConfig()
    main_config.ui_mode = "disabled"
    audit_config = AuditConfig()
    audit_config.targets = ["www.example.com"]
    audit_config.audit_db = dbname
    with PluginTester(main_config, audit_config) as t:
        disk = t.audit.database
        assert type(disk) is AuditSQLiteDB

        print "  Testing %d elements..." % (n * 3)
        t1 = time.time()

        print "  -> Writing..."
        for x in xrange(n):
            d1 = URL("http://www.example.com/" + generate_random_string())
            d2 = Text(generate_random_string())
            d3 = UrlDisclosure(d1)
            d1.add_information(d2)
            disk.add_data(d1)
            disk.add_data(d2)
            disk.add_data(d3)
        t2 = time.time()

        print "  -- Reading..."
        keys = disk.get_data_keys()
        assert len(keys) == (n * 3)
        for key in keys:
            assert disk.has_data_key(key)
            data = disk.get_data(key)
            assert data is not None
        keys = disk.get_data_keys(Data.TYPE_INFORMATION)
        assert len(keys) == n
        for key in keys:
            assert disk.has_data_key(key)
            data = disk.get_data(key)
            assert data is not None
            assert data.data_type == Data.TYPE_INFORMATION
            assert isinstance(data, Text)
        keys = disk.get_data_keys(Data.TYPE_RESOURCE)
        assert len(keys) == n
        for key in keys:
            assert disk.has_data_key(key)
            data = disk.get_data(key)
            assert data is not None
            assert data.data_type == Data.TYPE_RESOURCE
            assert isinstance(data, URL)
        keys = disk.get_data_keys(Data.TYPE_VULNERABILITY)
        assert len(keys) == n
        for key in keys:
            assert disk.has_data_key(key)
            data = disk.get_data(key)
            assert data is not None
            assert data.data_type == Data.TYPE_VULNERABILITY
            assert isinstance(data, UrlDisclosure)
        t3 = time.time()

        print "  <- Deleting..."
        for key in keys:
            disk.remove_data(key)
        t4 = time.time()

        print "  Write time:  %d seconds (%f seconds per element)" % (t2 - t1, (t2 - t1) / (n * 3.0))
        print "  Read time:   %d seconds (%f seconds per element)" % (t3 - t2, (t3 - t2) / (n * 3.0))
        print "  Delete time: %d seconds (%f seconds per element)" % (t4 - t3, (t4 - t3) / (n * 3.0))
        print "  Total time:  %d seconds (%f seconds per element)" % (t4 - t1, (t4 - t1) / (n * 3.0))


def test_auditdb_dump():
    main_config = OrchestratorConfig()
    main_config.ui_mode = "disabled"
    audit_config = AuditConfig()
    audit_config.targets = ["www.example.com"]
    audit_config.audit_db = "test_auditdb.db"
    with PluginTester(main_config, audit_config) as t:
        disk = t.audit.database
        assert t.audit.name == "test_auditdb"
        assert type(disk) is AuditSQLiteDB
        assert disk.filename == "test_auditdb.db"

        print "Testing the audit database dump..."
        print "  -> Writing..."
        for x in xrange(30):
            d1 = URL("http://www.example.com/" + generate_random_string())
            d2 = Text(generate_random_string())
            d3 = UrlDisclosure(d1)
            d1.add_information(d2)
            disk.add_data(d1)
            disk.add_data(d2)
            disk.add_data(d3)
            disk.mark_plugin_finished(d1.identity, "some_plugin")
            disk.mark_plugin_finished(d2.identity, "some_plugin")
            disk.mark_plugin_finished(d3.identity, "some_plugin")
            disk.mark_stage_finished(d1.identity, 1)
            disk.mark_stage_finished(d2.identity, 2)
            disk.mark_stage_finished(d3.identity, 3)
        disk.add_shared_values("fake_set_id", (
            "string",
            u"unicode",
            100,
            200L,
            5.0,
            True,
            False,
            complex(1, 1),
            None,
            frozenset({"string", 100, 1.0}),
            (None, True, False),
        ))
        disk.put_mapped_values("fake_map_id", (
            ("a_string", "string"),
            ("a_unicode_string", u"unicode"),
            ("an_integer", 100),
            ("a_long", 200L),
            ("a_float", 5.0),
            ("a_bool", True),
            ("another_bool", False),
            ("a_complex", complex(1, 1)),
            ("none", None),
            ("a_frozenset", frozenset({"string", 100, 1.0})),
            ("a_tuple", (None, True, False)),
        ))

        print "  -> Dumping..."
        disk.dump("test_auditdb.sql")


# Run all tests from the command line.
if __name__ == "__main__":
    test_auditdb_interfaces()
    test_auditdb_consistency()
    test_auditdb_dump()
    test_auditdb_stress()
