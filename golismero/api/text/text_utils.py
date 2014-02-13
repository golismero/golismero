#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Text manipulation utilities.
"""

__license__ = """
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

__all__ = [
    "char_count", "line_count", "word_count", "generate_random_string",
    "uncamelcase", "hexdump", "to_utf8", "split_first",
]

import re

from random import choice
from re import finditer
from string import ascii_letters, digits, printable


#------------------------------------------------------------------------------
def char_count(text):
    """
    :param text: Text.
    :type text: str

    :returns: Number of printable characters in text.
    :rtype: int
    """
    return sum(1 for _ in finditer(r"\w", text))


#------------------------------------------------------------------------------
def line_count(text):
    """
    :param text: Text.
    :type text: str

    :returns: Number of lines in text.
    :rtype: int
    """
    count = text.count("\n")
    if not text.endswith("\n"):
        count += 1
    return count


#------------------------------------------------------------------------------
def word_count(text):
    """
    :param text: Text.
    :type text: str

    :returns: Number of words in text.
    :rtype: int
    """
    return sum(1 for _ in finditer(r"\w+", text))


#------------------------------------------------------------------------------
def generate_random_string(length = 30):
    """
    Generates a random string of the specified length.

    The key space used to generate random strings are:

    - ASCII letters (both lowercase and uppercase).
    - Digits (0-9).

    >>> from golismero.api.text.text_utils import generate_random_string
    >>> generate_random_string(10)
    Asi91Ujsn5
    >>> generate_random_string(30)
    8KNLs981jc0h1ls8b2ks01bc7slgu2

    :param length: Desired string length.
    :type length: int
    """

    m_available_chars = ascii_letters + digits

    return "".join(choice(m_available_chars) for _ in xrange(length))


#------------------------------------------------------------------------------
# Adapted from: http://stackoverflow.com/a/2560017/426293
__uncamelcase_re = re.compile("%s|%s|%s" % (
    r"(?<=[A-Z])(?=[A-Z][a-z])",
    r"(?<=[^A-Z])(?=[A-Z])",
    r"(?<=[A-Za-z])(?=[^A-Za-z])",
))
def uncamelcase(string):
    """
    Converts a CamelCase string into a human-readable string.

    Examples::
        >>> uncamelcase("lowercase")
        'lowercase'
        >>> uncamelcase("Class")
        'Class'
        >>> uncamelcase("MyClass")
        'My Class'
        >>> uncamelcase("HTML")
        'HTML'
        >>> uncamelcase("PDFLoader")
        'PDF Loader'
        >>> uncamelcase("AString")
        'A String'
        >>> uncamelcase("SimpleXMLParser")
        'Simple XML Parser'
        >>> uncamelcase("GL11Version")
        'GL 11 Version'
        >>> uncamelcase("99Bottles")
        '99 Bottles'
        >>> uncamelcase("May5")
        'May 5'
        >>> uncamelcase("BFG9000")
        'BFG 9000'

    :param string: CamelCase string.
    :type string: str

    :returns: Human-readable string.
    :rtype: str
    """
    string = string.replace("_"," ")
    string = __uncamelcase_re.sub(" ", string)
    while "  " in string:
        string = string.replace("  ", " ")
    return string


#------------------------------------------------------------------------------
def hexdump(s):
    """
    Produce an hexadecimal output from a binary string.

    :param s: Binary string to dump.
    :type s: str

    :returns: Hexadecimal output.
    :rtype: str
    """
    a = []
    for i in xrange(0, len(s), 16):
        h1 = " ".join("%.2x" % ord(c) for c in s[i:i+8])
        h2 = " ".join("%.2x" % ord(c) for c in s[i+8:i+16])
        d = "".join(c if c in printable else "." for c in s[i:i+16])
        a.append("%-32s-%-32s %s\n" % (h1, h2, d))
    return "".join(a)


#------------------------------------------------------------------------------
def to_utf8(s):
    """
    Convert the given Unicode string into an UTF-8 encoded string.

    If the argument is already a normal Python string, nothing is done.
    So this function can be used as a filter to normalize string arguments.

    :param s: Unicode string to convert.
    :type s: basestring

    :returns: Converted string.
    :rtype: str
    """
    if isinstance(s, unicode):
        return s.encode("UTF-8")
    if type(s) is not str and isinstance(s, str):
        return str(s)
    return s


#------------------------------------------------------------------------------
# This function was borrowed from the urllib3 project.
#
# Urllib3 is copyright 2008-2012 Andrey Petrov and contributors (see
# CONTRIBUTORS.txt) and is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.php
# http://raw.github.com/shazow/urllib3/master/CONTRIBUTORS.txt
#
def split_first(s, delims):
    """
    Given a string and an iterable of delimiters, split on the first found
    delimiter. Return the two split parts and the matched delimiter.

    If not found, then the first part is the full input string.

    Example: ::

        >>> split_first('foo/bar?baz', '?/=')
        ('foo', 'bar?baz', '/')
        >>> split_first('foo/bar?baz', '123')
        ('foo/bar?baz', '', None)

    Scales linearly with number of delimiters.
    Not ideal for a large number of delimiters.

    .. warning: This function was borrowed from the urllib3 project.
                It may be removed in future versions of GoLismero.
    """
    min_idx = None
    min_delim = None
    for d in delims:
        idx = s.find(d)
        if idx < 0:
            continue

        if min_idx is None or idx < min_idx:
            min_idx = idx
            min_delim = d

    if min_idx is None or min_idx < 0:
        return s, '', None

    return s[:min_idx], s[min_idx+1:], min_delim
