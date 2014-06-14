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


# Import the base data types first.
from golismero.api.data import Data
from golismero.api.data.information import Information
from golismero.api.data.resource import Resource
from golismero.api.data.vulnerability import Vulnerability

# The local data cache.
from golismero.api.data import LocalDataCache

# The mock testing environment creator.
from golismero.main.testing import PluginTester


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


# This test will make sure all data types have a correct, unique type ID.
def test_data_types_have_id():
    seen_types = set()
    print
    print "Testing correctness of data type IDs..."
    data_types = helper_load_data_types()
    assert len(data_types) > 0
    for clazz in data_types:
        print "--> Checking %s (%s)" % (clazz.__name__, clazz.data_subtype)
        assert type(clazz.data_type) == int
        if issubclass(clazz, Information):
            assert clazz.data_type == Data.TYPE_INFORMATION
            assert clazz.data_subtype == clazz.information_type
            assert type(clazz.data_subtype) == str
            assert clazz.data_subtype.startswith("information/")
        elif issubclass(clazz, Resource):
            assert clazz.data_type == Data.TYPE_RESOURCE
            assert clazz.data_subtype == clazz.resource_type
            assert type(clazz.data_subtype) == str
            assert clazz.data_subtype.startswith("resource/")
        elif issubclass(clazz, Vulnerability):
            assert clazz.data_type == Data.TYPE_VULNERABILITY
            assert clazz.data_subtype == clazz.vulnerability_type
            assert type(clazz.data_subtype) == str
            assert clazz.data_subtype.startswith("vulnerability/")
        else:
            assert False, clazz  # A new base data class?
        assert clazz.data_subtype.endswith("/abstract") or \
               clazz.data_subtype not in seen_types, clazz.data_subtype
        seen_types.add(clazz.data_subtype)
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
    from golismero.api.data.resource.url import URL
    from golismero.api.data.information.text import Text
    from golismero.api.data.vulnerability.information_disclosure.url_disclosure import UrlDisclosure
    d1 = URL("http://www.example.com/")
    d2 = Text("some text")
    d3 = UrlDisclosure(d1)
    d1.add_information(d2)

    # Test data_type, data_subtype, etc.
    print "Testing Data type checks..."
    assert d1.data_type == Data.TYPE_RESOURCE
    assert d1.data_subtype == URL.data_subtype
    assert d1.resource_type == d1.data_subtype
    assert d2.data_type == Data.TYPE_INFORMATION
    assert d2.data_subtype == Text.data_subtype
    assert d2.information_type == d2.data_subtype
    assert d3.data_type == Data.TYPE_VULNERABILITY
    assert d3.data_subtype == UrlDisclosure.data_subtype
    assert d3.vulnerability_type == d3.data_subtype

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
    assert {x.identity for x in d1.find_linked_data(d1.data_type)} == set()
    assert {x.identity for x in d1.find_linked_data(d1.data_type, d1.resource_type)} == set()
    assert {x.identity for x in d1.find_linked_data(d2.data_type)} == {d2.identity}
    assert {x.identity for x in d1.find_linked_data(d2.data_type, d2.information_type)} == {d2.identity}
    assert {x.identity for x in d1.find_linked_data(d3.data_type)} == {d3.identity}
    assert {x.identity for x in d1.find_linked_data(d3.data_type, d3.vulnerability_type)} == {d3.identity}
    assert {x.identity for x in d2.find_linked_data(d2.data_type)} == set()
    assert {x.identity for x in d2.find_linked_data(d2.data_type, d2.information_type)} == set()
    assert {x.identity for x in d2.find_linked_data(d1.data_type)} == {d1.identity}
    assert {x.identity for x in d2.find_linked_data(d1.data_type, d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d2.find_linked_data(d3.data_type)} == set()
    assert {x.identity for x in d2.find_linked_data(d3.data_type, d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.find_linked_data(d3.data_type)} == set()
    assert {x.identity for x in d3.find_linked_data(d3.data_type, d3.vulnerability_type)} == set()
    assert {x.identity for x in d3.find_linked_data(d1.data_type)} == {d1.identity}
    assert {x.identity for x in d3.find_linked_data(d1.data_type, d1.resource_type)} == {d1.identity}
    assert {x.identity for x in d3.find_linked_data(d2.data_type)} == set()
    assert {x.identity for x in d3.find_linked_data(d2.data_type, d2.information_type)} == set()

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
    result = LocalDataCache.on_finish([d2, d3], d1)
    assert set(result) == set([d1, d2, d3])
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
    test_data_types_have_id()
    test_data_links()
