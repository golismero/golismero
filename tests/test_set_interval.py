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


from golismero.api.parallel import setInterval
from golismero.main.testing import PluginTester

from threading import Event
from time import gmtime, strftime, time


#------------------------------------------------------------------------------
num     = 10
handler = None
sem     = Event()
times   = []

def test_interval():
    with PluginTester():

        global handler

        print "Testing setInterval..."
        sem.clear()
        handler = helper_test_interval()
        sem.wait()

        assert all(
            int( times[index + 1] - times[index] ) == 2
            for index in xrange(len(times) - 1)
        )

@setInterval(2)
def helper_test_interval():
    global num

    if num < 1:
        print "--> Finish!"
        handler.set()
        sem.set()
    else:
        #print "[%s] Iteration %s" % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), str(num))
        print "--> %d: %s" % (num - 1, strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        num -= 1
        times.append(time())



if __name__ == "__main__":
    test_interval()
