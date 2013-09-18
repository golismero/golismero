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
from golismero.api.net.web_utils import *
from golismero.api.text.text_utils import *


case_uncamelcase = [
    ("lowercase",         "lowercase"),
    ("Class",             "Class"),
    ("MyClass",           "My Class"),
    ("HTML",              "HTML"),
    ("PDFLoader",         "PDF Loader"),
    ("AString",           "A String"),
    ("SimpleXMLParser",   "Simple XML Parser"),
    ("GL11Version",       "GL 11 Version"),
    ("99Bottles",         "99 Bottles"),
    ("May5",              "May 5"),
    ("BFG9000",           "BFG 9000"),
]
def test_uncamelcase():
    print "Testing uncamelcase()..."
    for src, dst in case_uncamelcase:
        assert uncamelcase(src) == dst, (dst, uncamelcase(src))


# Run all tests from the command line.
if __name__ == "__main__":
    test_uncamelcase()
