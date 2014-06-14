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

import os
from os import path
import re
from StringIO import StringIO

AUTO_FIX = False
##AUTO_FIX = True

def test_newlines_and_tabs():
    print "Testing the source code format..."

    # Regexp to detect separator lines.
    separator = re.compile(r"^ *\#\-+ *\n$")

    # Get the GoLismero folder.
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..")
    golismero = path.abspath(golismero)
    if not golismero.endswith(path.sep):
        golismero += path.sep

    # Recursively look for all .py files.
    # Skip the third party libs folder and tools folder.
    for root, directories, files in os.walk(golismero):
        if root.endswith(path.sep + "thirdparty_libs"):
            continue
        if (path.sep + "thirdparty_libs" + path.sep) in root:
            continue
        if root.endswith(path.sep + "tools"):
            continue
        if (path.sep + "tools" + path.sep) in root:
            continue
        for filename in files:
            if not filename.endswith(".py") and \
                    not filename.endswith(".golismero"):
                continue
            filename = path.join(root, filename)
            filename = path.abspath(filename)

            # Get the relative file name, for reporting.
            relative = filename[ len(golismero) : ]

            # Read the file bytes in binary mode.
            with open(filename, "rb") as fd:
                data = fd.read()

            # Skip 0 byte files.
            if not data:
                continue

            # If tab characters are present, warn about it.
            if "\t" in data:
                print "+ found tabs in file: %s" % relative

            # If newline characters are not in Linux format, warn about it.
            if "\r\n" in data:
                print "+ found Windows newlines in file: %s" % relative
                if AUTO_FIX:
                    data = data.replace("\r\n", "\n")
                    with open(filename, "wb") as fd:
                        fd.write(data)
            elif "\r" in data:
                print "+ found Mac newlines in file: %s" % relative
                if AUTO_FIX:
                    data = data.replace("\r", "\n")
                    with open(filename, "wb") as fd:
                        fd.write(data)

            # If the file doesn't end with a newline character, warn about it.
            if not data.endswith("\n") and not data.endswith("\r"):
                print "+ found file with no terminating newline: %s" % relative
                if AUTO_FIX:
                    data += "\n"
                    with open(filename, "wb") as fd:
                        fd.write(data)

            # If bad blank lines are found, warn about it.
            fake = StringIO(data)
            warned = False
            fixed = []
            for line in fake:
                if line.strip() == "" and line != "\n":
                    if not warned:
                        print "+ found file with bad blank lines: %s" \
                              % relative
                        warned = True
                    line = "\n"
                fixed.append(line)
            if warned and AUTO_FIX:
                data = "".join(fixed)
                with open(filename, "wb") as fd:
                    fd.write(data)

            # If broken separators are found, warn about it.
            fake = StringIO(data)
            warned = False
            fixed = []
            for line in fake:
                if separator.match(line):
                    if len(line) != 80:
                        if not warned:
                            print "+ found file with broken separators: %s" \
                                  % relative
                            warned = True
                        line = line.rstrip()
                        if len(line) < 79:
                            line += "-" * (80 - len(line))
                        else:
                            line = line[:79]
                        line += "\n"
                    if (len(fixed) < 2 or \
                            fixed[-1] != "\n" or fixed[-2] != "\n") and \
                                    not fixed[-1].lstrip().startswith("#"):
                        if not warned:
                            print "+ found file with broken separators: %s" \
                                  % relative
                            warned = True
                        if fixed[-1] != "\n":
                            fixed.append("\n")
                            fixed.append("\n")
                        elif fixed[-2] != "\n":
                            fixed.append("\n")
                    if len(fixed) > 2 and \
                                fixed[-1] == fixed[-2] == fixed[-3] == "\n":
                        if not warned:
                            print "+ found file with broken separators: %s" \
                                  % relative
                            warned = True
                        while len(fixed) > 2 and \
                                fixed[-1] == fixed[-2] == fixed[-3] == "\n":
                            fixed.pop()
                fixed.append(line)
            if warned and AUTO_FIX:
                data = "".join(fixed)
                with open(filename, "wb") as fd:
                    fd.write(data)

    # Done!
    print "...done!"

# Run the test from the command line.
if __name__ == "__main__":
    test_newlines_and_tabs()
