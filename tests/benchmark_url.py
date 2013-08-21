#!/usr/bin/env python
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

# Fix the module load path.
if __name__ == "__main__":
    import os, sys
    from os import path
    root = path.split(path.abspath(__file__))[0]
    if not root:  # if it fails use cwd instead
        root = path.abspath(os.getcwd())
    root = path.abspath(path.join(root, ".."))
    thirdparty_libs = path.join(root, "thirdparty_libs")
    if not path.exists(path.join(root, "golismero")):
        raise RuntimeError("Can't find GoLismero!")
    sys.path.insert(0, thirdparty_libs)
    sys.path.insert(0, root)

from golismero.api.net.web_utils import parse_url

from timeit import Timer, default_repeat


#--------------------------------------------------------------------------
def _benchmark():
    return parse_url('http://example.com/path?query=string&param=value&orphan#fragment_id').url

# Some code borrowed from the timeit module.
def benchmark(number = 0, precision = 3, verbose = True):
    repeat = default_repeat
    t = Timer(_benchmark)
    if number == 0:
        # determine number so that 0.2 <= total time < 2.0
        for i in range(1, 10):
            number = 10**i
            try:
                x = t.timeit(number)
            except:
                t.print_exc()
                return 1
            if verbose:
                print "%d loops -> %.*g secs" % (number, precision, x)
            if x >= 0.2:
                break
    try:
        r = t.repeat(repeat, number)
    except:
        t.print_exc()
        return 1
    best = min(r)
    if verbose:
        print "raw times:", " ".join(["%.*g" % (precision, x) for x in r])
    print "%d loops," % number,
    usec = best * 1e6 / number
    if usec < 1000:
        print "best of %d: %.*g usec per loop" % (repeat, precision, usec)
    else:
        msec = usec / 1000
        if msec < 1000:
            print "best of %d: %.*g msec per loop" % (repeat, precision, msec)
        else:
            sec = msec / 1000
            print "best of %d: %.*g sec per loop" % (repeat, precision, sec)
    return None


#--------------------------------------------------------------------------
if __name__ == "__main__":
    benchmark()
