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

import sys
import os
from os import path

def test_newlines_and_tabs():
    print "Testing the source code format..."

    # Get the GoLismero folder.
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..")
    golismero = path.abspath(golismero)
    if not golismero.endswith(path.sep):
        golismero += path.sep

    # Recursively look for all .py files.
    # Skip the third party libs folder.
    for root, directories, files in os.walk(golismero):
        if root.endswith(path.sep + "thirdparty_libs"):
            continue
        if (path.sep + "thirdparty_libs" + path.sep) in root:
            continue
        for filename in files:
            if not filename.endswith(".py") and not filename.endswith(".golismero"):
                continue
            filename = path.join(root, filename)
            filename = path.abspath(filename)

            # Get the relative file name, for reporting.
            relative = filename[ len(golismero) : ]

            # Read the file bytes in binary mode.
            with open(filename, "rb") as fd:
                data = fd.read()

            # If tab characters are present, warn about it.
            if "\t" in data:
                print "+ found tabs in file: %s" % relative

            # If newline characters are not in Linux format, warn about it.
            if "\r\n" in data:
                print "+ found Windows newlines in file: %s" % relative
                ##data = data.replace("\r\n", "\n")
                ##with open(filename, "wb") as fd:
                ##    fd.write(data)
            elif "\r" in data:
                print "+ found Mac newlines in file: %s" % relative
                ##data = data.replace("\r", "\n")
                ##with open(filename, "wb") as fd:
                ##    fd.write(data)

    # Done!
    print "...done!"

# Run the test from the command line.
if __name__ == "__main__":
    test_newlines_and_tabs()
