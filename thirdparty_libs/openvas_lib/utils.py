# -*- coding: utf-8 -*-

from __future__ import print_function

"""
Utils functions, like timer and random string generator.
"""

import sys

from random import choice
from threading import Event, Timer
from string import ascii_letters, digits

__license__ = """
OpenVAS connector for OMP protocol.

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


if sys.version_info >= (3,):
    _range = range
else:
    _range = xrange

# ------------------------------------------------------------------------------
#
# Useful functions
#
# ------------------------------------------------------------------------------
def set_interval(interval, times=-1):
    """
	Decorator to execute a function periodically using a timer.
	The function is executed in a background thread.

	Example:

		>>> from time import gmtime, strftime
		>>> @set_interval(2) # Execute every 2 seconds until stopped.
		... def my_func():
		...     print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
		...
		>>> handler = my_func()
		2013-07-25 22:40:55
		2013-07-25 22:40:57
		2013-07-25 22:40:59
		2013-07-25 22:41:01
		>>> handler.set() # Stop the execution.
		>>> @set_interval(2, 3) # Every 2 seconds, 3 times.
		... def my_func():
		...     print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
		...
		>>> handler = my_func()
		2013-07-25 22:40:55
		2013-07-25 22:40:57
		2013-07-25 22:40:59
	"""
    # Validate the parameters.
    if isinstance(interval, int):
        interval = float(interval)
    elif not isinstance(interval, float):
        raise TypeError("Expected int or float, got %r instead" % type(interval))
    if not isinstance(times, int):
        raise TypeError("Expected int, got %r instead" % type(times))

    # Code adapted from: http://stackoverflow.com/q/5179467

    # This will be the actual decorator,
    # with fixed interval and times parameter
    def outer_wrap(function):
        if not callable(function):
            raise TypeError("Expected function, got %r instead" % type(function))

        # This will be the function to be
        # called
        def wrap(*args, **kwargs):

            stop = Event()

            # This is another function to be executed
            # in a different thread to simulate set_interval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = Timer(0, inner_wrap)
            t.daemon = True
            t.start()

            return stop

        return wrap

    return outer_wrap


# ----------------------------------------------------------------------
def generate_random_string(length=30):
    """
	Generates a random string of the specified length.

	The key space used to generate random strings are:

	- ASCII letters (both lowercase and uppercase).
	- Digits (0-9).
	"""
    m_available_chars = ascii_letters + digits

    return "".join(choice(m_available_chars) for _ in _range(length))
