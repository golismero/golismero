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
    "char_count", "line_count", "word_count",
    "generate_random_string", "calculate_shannon_entropy",
    "split_first"]

from math import log
from random import choice
from re import finditer
from string import ascii_letters, digits


#----------------------------------------------------------------------
def char_count(text):
    """
    :param text: Text.
    :type text: str

    :returns: Number of printable characters in text.
    :rtype: int
    """
    return sum(1 for _ in finditer(r"\w", text))


#----------------------------------------------------------------------
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


#----------------------------------------------------------------------
def word_count(text):
    """
    :param text: Text.
    :type text: str

    :returns: Number of words in text.
    :rtype: int
    """
    return sum(1 for _ in finditer(r"\w+", text))


#----------------------------------------------------------------------
def generate_random_string(length = 30):
    """
    Generates a random string of the specified length.

    The key space used to generate random strings are:

    - ASCII letters (both lowercase and uppercase).
    - Digits (0-9).

    >>> from golismero.text.text_utils import generate_random_string
    >>> generate_random_string(10)
    Asi91Ujsn5
    >>> generate_random_string(30)
    8KNLs981jc0h1ls8b2ks01bc7slgu2

    :param length: Desired string length.
    :type length: int
    """

    m_available_chars = ascii_letters + digits

    return "".join(choice(m_available_chars) for _ in xrange(length))


#----------------------------------------------------------------------
def calculate_shannon_entropy(string):
    """
    Calculates the Shannon entropy for the given string.

    :param string: String to parse.
    :type string: str

    :returns: Shannon entropy (min bits per byte-character).
    :rtype: float
    """
    if isinstance(string, unicode):
        string = string.encode("ascii")
    ent = 0.0
    if len(string) < 2:
        return ent
    size = float(len(string))
    for b in xrange(128):
        freq = string.count(chr(b))
        if freq > 0:
            freq = float(freq) / size
            ent = ent + freq * log(freq, 2)
    return -ent


#----------------------------------------------------------------------
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

    Scales linearly with number of delimiters. Not ideal for a large number of delimiters.

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
