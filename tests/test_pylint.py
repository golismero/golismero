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

def test_pylint():

    # Fix the module load path for the test.
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..")
    golismero = path.abspath(golismero)
    thirdparty_libs = path.join(golismero, "thirdparty_libs")
    pythonpath = list(sys.path)
    pythonpath.insert(0, thirdparty_libs)
    pythonpath.insert(0, golismero)
    os.environ['PYTHONPATH'] = path.pathsep.join(pythonpath)

    # False positives to filter out.
    try:
        with open(path.join(here, "test_pylint.txt"), "r") as fd:
            FALSE_POSITIVES = [ x.strip() for x in fd if x.strip() ]
    except IOError:
        FALSE_POSITIVES = []

    try:

        # Run PyLint against the sources and save the log.
        print "Running PyLint..."
        with open("_tmp_pylint.log", "w") as log:
            from pylint import epylint as lint
            pwd = os.getcwd()
            os.chdir("..")
            lint.py_run('-E -f parseable golismero', False, log, None, script="pylint")
            os.chdir(pwd)

        # Clean up the log, filter out the false positives, and write the log to disk.
        print "Cleaning up the PyLint log..."
        if not golismero.endswith(path.sep):
            golismero += path.sep
        false_pos = set()
        with open("_tmp_pylint.log", "r") as log:
            with open("pylint.log", "w") as output:
                for line in log:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("*************"):
                        continue
                    if ": Warning (W): FIXME" in line or \
                       ": Warning (W): TODO" in line or \
                       ": Warning (W): XXX" in line:
                        continue
                    if line.startswith(golismero):
                        line = line[ len(golismero) : ]
                    try:
                        p = line.find(":")
                        q = line.find(":", p + 1)
                        f = line[ : p ]
                        d = line[ q : ]
                        n = int( line[ p + 1 : q ] )
                        if os.sep != "/":
                            f = f.replace(os.sep, "/")
                        line = f + line[ p : ]
                        found = False
                        for false in FALSE_POSITIVES:
                            if not false:
                                continue
                            fp = false.find(":")
                            fq = false.find(":", fp + 1)
                            ff = false[ : fp ]
                            fd = false[ fq : ]
                            fn = int( false[ fp + 1 : fq ] )
                            if f == ff and d == fd: ## and (fn - 10) <= n <= (fn + 10):
                                found = True
                                false_pos.add( (ff, fn, fd) )
                                break
                        if found:
                            continue
                    except Exception:
                        pass
                    output.write(line)
                    output.write("\n")
                    output.flush()

        # Update the false positives.
        if false_pos:
            with open(path.join(here, "test_pylint.txt"), "w") as out:
                for (ff, fn, fd) in sorted(false_pos):
                    false = "%s:%d%s\n" % (ff, fn, fd)
                    out.write(false)

    finally:

        # Delete the temporary file.
        try:
            os.unlink("_tmp_pylint.log")
        except:
            pass
        print "Done!"


# Run the test from the command line.
if __name__ == "__main__":
    test_pylint()
