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
from golismero.api.parallel import *
from golismero.main.testing import PluginTester

from thread import get_ident
from threading import enumerate as thread_list
from random import randint
from time import sleep, time


# Tests the parallel execution with random data.
def test_pmap():
    print "Testing parallel execution with random data..."
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.ui_mode = "disabled"
        t.audit_config.audit_db = ":memory:"
        t.init_environment()
        t_list = thread_list()
        func = lambda x: x
        for i in xrange(20):
            input_data   = [randint(-10, 10) for x in xrange(randint(10, 200))]
            output_data  = pmap(func, input_data)
            control_data = map(func, input_data)
            assert output_data == control_data
            assert input_data == output_data
        assert t_list == thread_list()


# Tests the parallel execution with random data and multiple parameters.
def test_pmap_multi():
    print "Testing parallel execution with random data and multiple parameters..."
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.ui_mode = "disabled"
        t.audit_config.audit_db = ":memory:"
        t.init_environment()
        t_list = thread_list()
        def func(*args):
            return sum( x for x in args if x is not None )
        for i in xrange(10):
            input_data = []
            for j in xrange(randint(2, 100)):
                args = [randint(-10, 10) for x in xrange(randint(10, 20))]
                input_data.append(args)
            output_data  = pmap(func, *input_data, pool_size=10)
            control_data = map(func, *input_data)
            assert output_data == control_data
        assert t_list == thread_list()


# Tests the parallel execution with errors.
def test_pmap_errors():
    print "Testing parallel execution with errors..."
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.ui_mode = "disabled"
        t.audit_config.audit_db = ":memory:"
        t.init_environment()
        t_list = thread_list()
        def func(x):
            if x & 1:
                raise ValueError("I don't like odd numbers!")
            return int(x / 2)
        def control(x):
            if x & 1:
                return None
            return int(x / 2)
        output_data  = pmap(func,   xrange(200))
        control_data = map(control, xrange(200))
        assert output_data == control_data
        assert t_list == thread_list()


# Tests the parallel execution with delays.
def test_pmap_delays():
    print "Testing parallel execution with delays..."
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.ui_mode = "disabled"
        t.audit_config.audit_db = ":memory:"
        t.init_environment()
        t_list = thread_list()
        def func(x):
            ##print "(%d)" % get_ident()
            sleep(1)
            return x
        def test(x):
            assert pmap(func, xrange(x)) == range(x)
        test(1)
        test(4)
        test(8)
        assert t_list == thread_list()


# Tests the parallel execution with large inputs.
def test_pmap_large_input():
    print "Testing parallel execution with large inputs..."
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.ui_mode = "disabled"
        t.audit_config.audit_db = ":memory:"
        t.init_environment()
        pmap(lambda x: x, range(1000))


# Run all tests from the command line.
if __name__ == "__main__":
    test_pmap()
    test_pmap_multi()
    test_pmap_errors()
    test_pmap_delays()
    test_pmap_large_input()
