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


# Import the base data types first.
from golismero.api.data import Data
from golismero.api.data.information import Information
from golismero.api.data.resource import Resource
from golismero.api.data.vulnerability import Vulnerability

# The local data cache.
from golismero.api.data import LocalDataCache

# The mock testing environment creator.
from golismero.main.testing import PluginTester


# Get the information and resource type IDs.
INFORMATION_TYPES = {
    getattr(Information, name)
    for name in dir(Information)
    if name.startswith("INFORMATION_")
}
RESOURCE_TYPES = {
    getattr(Resource, name)
    for name in dir(Resource)
    if name.startswith("RESOURCE_")
}


# Helper function to test for duplicate type ID numbers.
def helper_test_dupes(clazz, prefix, numbers):
    print "Testing %s" % clazz.__name__
    n_unknown = prefix + "UNKNOWN"
    unknown = getattr(clazz, n_unknown)
    assert unknown is 0
    for name in dir(clazz):
        if not name.startswith(prefix) or name == n_unknown:
            continue
        value = getattr(clazz, name)
        assert type(value) is int
        assert value not in numbers
        numbers.add(value)


# This test will make sure the data type ID numbers aren't repeated.
def test_data_type_unique_ids():
    print "Looking for duplicated data type IDs"

    # Test the base types.
    helper_test_dupes(Data, "TYPE_", set())

    # Test the subtypes.
    numbers = set()
    helper_test_dupes(Information, "INFORMATION_", numbers)
    helper_test_dupes(Resource, "RESOURCE_", numbers)

    # Make sure the base vulnerability type is "generic".
    assert Vulnerability.vulnerability_type == "generic"


# Helper function to load all data types.
def helper_load_data_types():
    data_types = []

    # Look for Python files in golismero/api/data.
    api_data = path.join(golismero, "golismero", "api", "data")
    api_data = path.abspath(api_data)
    print "Looking for modules in: %s" % api_data
    assert path.isdir(api_data)
    for root, folders, files in os.walk(api_data):
        for name in files:
            if name.startswith("_") or not name.endswith(".py"):
                continue

            # Get the module name from its file path.
            name = name[:-3]
            name = path.join(root, name)
            name = path.abspath(name)
            name = name[len(api_data):]
            if name.startswith(path.sep):
                name = name[1:]
            name = name.replace(path.sep, ".")
            name = "golismero.api.data." + name
            print "--> Loading %s" % name

            # Load the module and extract all its data types.
            module = __import__(name, globals(), locals(), ['*'])
            for name in dir(module):
                if name.startswith("_") or name in (
                    "Data",
                    "Information",
                    "Resource",
                    "Vulnerability",
                ):
                    continue
                clazz = getattr(module, name)
                if isinstance(clazz, type) and issubclass(clazz, Data) and clazz not in data_types:
                    print "------> Found %s" % name
                    data_types.append(clazz)

    return data_types


# This test will make sure all data types have a correct type ID.
def test_data_types_have_id():
    print
    print "Testing correctness of data type IDs..."
    data_types = helper_load_data_types()
    assert len(data_types) > 0
    for clazz in data_types:
        print "--> Checking %s" % clazz.__name__
        assert type(clazz.data_type) == int
        if issubclass(clazz, Information):
            assert clazz.data_type == Data.TYPE_INFORMATION
            assert type(clazz.information_type) == int
            if clazz.__module__ != "golismero.api.data.information":
                assert clazz.information_type != Information.INFORMATION_UNKNOWN
                assert clazz.information_type in INFORMATION_TYPES
            else:
                assert clazz.information_type == Information.INFORMATION_UNKNOWN
        elif issubclass(clazz, Resource):
            assert clazz.data_type == Data.TYPE_RESOURCE
            assert type(clazz.resource_type) == int
            if clazz.__module__ != "golismero.api.data.resource":
                assert clazz.resource_type != Resource.RESOURCE_UNKNOWN
                assert clazz.resource_type in RESOURCE_TYPES
            else:
                assert clazz.resource_type == Resource.RESOURCE_UNKNOWN
        elif issubclass(clazz, Vulnerability):
            assert clazz.data_type == Data.TYPE_VULNERABILITY
            assert type(clazz.vulnerability_type) == str
            if clazz.__module__ != "golismero.api.data.vulnerability":
                assert clazz.vulnerability_type != "generic"
        else:
            assert False  # A new base data class?
    print


# This test makes sure the links work properly.
def test_data_links():
    with PluginTester(autoinit=False) as t:
        t.audit_config.targets = ["http://www.example.com/"]
        t.orchestrator_config.ui_mode = "disabled"
        t.init_environment()
        helper_data_links()


# The actual test, without the boilerplate.
def helper_data_links():

    # Create some dummy data.
    from golismero.api.data.resource.url import Url
    from golismero.api.data.information.text import Text
    from golismero.api.data.vulnerability.information_disclosure.url_disclosure import UrlDisclosure
    d1 = Url("http://www.example.com/")
    d2 = Text("some text")
    d3 = UrlDisclosure(d1)
    d1.add_information(d2)

    # Test validate_link_minimums().
    print "Testing Data.validate_link_minimums()..."
    d1.validate_link_minimums()
    d2.validate_link_minimums()
    d3.validate_link_minimums()

    # Test the links property.
    print "Testing Data.links..."
    assert d1.links == {d2.identity, d3.identity}
    assert d2.links == {d1.identity}
    assert d3.links == {d1.identity}

    # Test the get_links method.
    print "Testing Data.get_links()..."
    assert d1.get_links(d1.data_type) == set()
    assert d1.get_links(d1.data_type, d1.resource_type) == set()
    assert d1.get_links(d2.data_type) == {d2.identity}
    assert d1.get_links(d2.data_type, d2.information_type) == {d2.identity}
    assert d1.get_links(d3.data_type) == {d3.identity}
    assert d1.get_links(d3.data_type, d3.vulnerability_type) == {d3.identity}
    assert d2.get_links(d2.data_type) == set()
    assert d2.get_links(d2.data_type, d2.information_type) == set()
    assert d2.get_links(d1.data_type) == {d1.identity}
    assert d2.get_links(d1.data_type, d1.resource_type) == {d1.identity}
    assert d2.get_links(d3.data_type) == set()
    assert d2.get_links(d3.data_type, d3.vulnerability_type) == set()
    assert d3.get_links(d3.data_type) == set()
    assert d3.get_links(d3.data_type, d3.vulnerability_type) == set()
    assert d3.get_links(d1.data_type) == {d1.identity}
    assert d3.get_links(d1.data_type, d1.resource_type) == {d1.identity}
    assert d3.get_links(d2.data_type) == set()
    assert d3.get_links(d2.data_type, d2.information_type) == set()

    # Test the linked_data property.
    # There should be no accesses to the database since all data is local.
    print "Testing Data.linked_data..."
    assert {x.identity for x in d1.linked_data} == {d2.identity, d3.identity}
    assert {x.identity for x in d2.linked_data} == {d1.identity}
    assert {x.identity for x in d3.linked_data} == {d1.identity}

    # Test the get_linked_data() method.
    # There should be no accesses to the database since all data is local.
    print "Testing Data.get_linked_data()..."
    assert {x.identity for x in d1.get_linked_data(d1.data_type)} == set()
    assert {x.identity for x in d1.get_linked_data(d1.data_type, d1.resource_type)} == set()
    assert {x.identity for x in d1.get_linked_data(d2.data_type)} == {d2.identity}
    assert {x.identity for x in d1.get_linked_data(d2.data_type, d2.information_type)} == {d2.identity}
    assert {x.identity for x in d1.get_linked_data(d3.data_type)} == {d3.identity}
    assert {x.identity for x in d1.get_linked_data(d3.data_type, d3.vulnerability_type)} == {d3.identity}
    assert {x.identity for x in d2.get_linked_data(d2.data_type)} == set()
    assert {x.identity for x in d2.get_linked_data(d2.data_type, d2.information_type)} == set()
    assert {x.identity for x in d2.get_linked_data(d1.data_type)} == {d1.identity}
    assert {x.identity for x in d2.get_linked_data(d1.data_type, d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d2.get_linked_data(d3.data_type)} == set()
    assert {x.identity for x in d2.get_linked_data(d3.data_type, d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.get_linked_data(d3.data_type)} == set()
    assert {x.identity for x in d3.get_linked_data(d3.data_type, d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.get_linked_data(d1.data_type)} == {d1.identity}
    assert {x.identity for x in d3.get_linked_data(d1.data_type, d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d3.get_linked_data(d2.data_type)} == set()
    assert {x.identity for x in d3.get_linked_data(d2.data_type, d2.information_type)} == set()

    # Test the associated_* properties.
    # There should be no accesses to the database since all data is local.
    print "Testing Data.associated_*..."
    assert {x.identity for x in d1.associated_resources} == set()
    assert {x.identity for x in d1.associated_informations} == {d2.identity}
    assert {x.identity for x in d1.associated_vulnerabilities} == {d3.identity}
    assert {x.identity for x in d2.associated_informations} == set()
    assert {x.identity for x in d2.associated_resources} == {d1.identity}
    assert {x.identity for x in d2.associated_vulnerabilities} == set()
    assert {x.identity for x in d3.associated_vulnerabilities} == set()
    assert {x.identity for x in d3.associated_resources} == {d1.identity}
    assert {x.identity for x in d3.associated_informations} == set()

    # Test the get_associated_*_by_category() methods.
    # There should be no accesses to the database since all data is local.
    print "Testing Data.get_associated_*_by_category()..."
    assert {x.identity for x in d1.get_associated_resources_by_category(d1.resource_type)} == set()
    assert {x.identity for x in d1.get_associated_informations_by_category(d2.information_type)} == {d2.identity}
    assert {x.identity for x in d1.get_associated_vulnerabilities_by_category(d3.vulnerability_type)} == {d3.identity}
    assert {x.identity for x in d2.get_associated_informations_by_category(d2.information_type)} == set()
    assert {x.identity for x in d2.get_associated_resources_by_category(d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d2.get_associated_vulnerabilities_by_category(d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.get_associated_vulnerabilities_by_category(d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.get_associated_resources_by_category(d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d3.get_associated_informations_by_category(d2.information_type)} == set()

    # Test TempDataStorage.on_finish().
    print "Testing LocalDataCache.on_finish() on ideal conditions..."
    result_before = [d1, d2, d3]
    result_after  = LocalDataCache.on_finish(result_before)
    assert set(result_before) == set(result_after)
    d1.validate_link_minimums()
    d2.validate_link_minimums()
    d3.validate_link_minimums()
    assert d1.links == {d2.identity, d3.identity}
    assert d2.links == {d1.identity}
    assert d3.links == {d1.identity}
    assert d1.get_links(d1.data_type) == set()
    assert d1.get_links(d1.data_type, d1.resource_type) == set()
    assert d1.get_links(d2.data_type) == {d2.identity}
    assert d1.get_links(d2.data_type, d2.information_type) == {d2.identity}
    assert d1.get_links(d3.data_type) == {d3.identity}
    assert d1.get_links(d3.data_type, d3.vulnerability_type) == {d3.identity}
    assert d2.get_links(d2.data_type) == set()
    assert d2.get_links(d2.data_type, d2.information_type) == set()
    assert d2.get_links(d1.data_type) == {d1.identity}
    assert d2.get_links(d1.data_type, d1.resource_type) == {d1.identity}
    assert d2.get_links(d3.data_type) == set()
    assert d2.get_links(d3.data_type, d3.vulnerability_type) == set()
    assert d3.get_links(d3.data_type) == set()
    assert d3.get_links(d3.data_type, d3.vulnerability_type) == set()
    assert d3.get_links(d1.data_type) == {d1.identity}
    assert d3.get_links(d1.data_type, d1.resource_type) == {d1.identity}
    assert d3.get_links(d2.data_type) == set()
    assert d3.get_links(d2.data_type, d2.information_type) == set()

    # XXX TODO: more tests!!!


# Run all tests from the command line.
if __name__ == "__main__":
    test_data_type_unique_ids()
    test_data_types_have_id()
    test_data_links()
