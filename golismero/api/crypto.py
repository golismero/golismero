#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cryptographic utility functions.
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

__all__ = ["guess_hash", "validate_hash", "calculate_shannon_entropy"]

from math import log


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


#------------------------------------------------------------------------------
def guess_hash(hash_to_guess):
    """
    Guesses possible hash algorithms for the given hash.

    :param hash_to_guess: String with the hash to guess.
    :type hash_to_guess: str

    :returns: List of possible hash algorithms.
    :rtype: list(str)
    """
    matched = []
    for algo, signature in HASH_SIGNATURES.iteritems():
        (length, alnum, alpha, digit, lower, upper, match) = signature
        if not len(hash_to_guess) == length:
            continue
        if alnum is not None and hash_to_guess.isalnum() != alnum:
            continue
        if alpha is not None and hash_to_guess.isalpha() != alpha:
            continue
        if digit is not None and hash_to_guess.isdigit() != digit:
            continue
        if lower is not None and hash_to_guess.islower() != lower:
            continue
        if upper is not None and hash_to_guess.isupper() != upper:
            continue
        if match is not None:
            (begin, end, string) = match
            if hash_to_guess[begin:end] != string:
                continue
        matched.append(algo)
    matched.sort()
    return matched


#------------------------------------------------------------------------------
def validate_hash(hash_name, hash_value):
    """
    Verifies if the given hash value matches the hash algorithm.

    :param hash_name: Name of the hash algorithm.
    :type hash_name: str

    :param hash_value: String with the hash value to check.
    :type hash_value: str

    :returns: True if the algorithm and value match, False if they don't,
        None if the hash algorithm is not supported.
    :rtype: bool | None
    """
    hash_name = hash_name.lower()
    for algo, signature in HASH_SIGNATURES.iteritems():
        if hash_name == algo.lower():
            (length, alnum, alpha, digit, lower, upper, match) = signature
            if not len(hash_value) == length:
                return False
            if alnum is not None and hash_value.isalnum() != alnum:
                return False
            if alpha is not None and hash_value.isalpha() != alpha:
                return False
            if digit is not None and hash_value.isdigit() != digit:
                return False
            if lower is not None and hash_value.islower() != lower:
                return False
            if upper is not None and hash_value.isupper() != upper:
                return False
            if match is not None:
                (begin, end, string) = match
                if hash_value[begin:end] != string:
                    return False
            return True


#------------------------------------------------------------------------------
# The signatures used by the guess_hash() function.

HASH_SIGNATURES = {
    'ADLER32': (8, True, False, False, None, None, None),
    'CRC16': (4, True, False, None, None, None, None),
    'CRC32': (8, True, False, False, None, None, None),
    'DESUnix': (13, None, False, False, None, None, None),
    'DomainCachedCredentials': (32, True, False, False, None, None, None),
    'FCS16': (4, True, False, False, None, None, None),
    'GHash323': (8, True, False, True, None, None, None),
    'GHash325': (8, True, False, True, None, None, None),
    'GOSTR341194': (64, True, False, False, None, None, None),
    'Haval128': (32, True, False, False, None, None, None),
    'Haval160': (40, True, False, False, None, None, None),
    'Haval192': (48, True, False, False, None, None, None),
    'Haval224': (56, True, False, False, None, None, None),
    'Haval256': (64, True, False, False, None, None, None),
    'LineageIIC4': (34, True, False, False, None, None, (0, 2, '0x')),
    'MD2': (32, True, False, False, None, None, None),
    'MD4': (32, True, False, False, None, None, None),
    'MD5': (32, True, False, False, None, None, None),
    'MD5APR': (37, None, False, False, None, None, (0, 4, '$apr')),
    'MD5Half': (16, True, False, False, None, None, None),
    'MD5Unix': (34, False, False, False, None, None, (0, 3, '$1$')),
    'MD5Wordpress': (34, False, False, False, None, None, (0, 3, '$P$')),
    'MD5passsaltjoomla1': (49, False, False, False, None, None, (32, 33, ':')),
    'MD5passsaltjoomla2': (65, False, False, False, None, None, (32, 33, ':')),
    'MD5phpBB3': (34, False, False, False, None, None, (0, 3, '$H$')),
    'MySQL': (16, True, False, False, None, None, None),
    'MySQL160bit': (41, False, False, False, None, None, (0, 1, '*')),
    'MySQL5': (40, True, False, False, None, None, None),
    'NTLM': (32, True, False, False, None, None, None),
    'RAdminv2x': (32, True, False, False, None, None, None),
    'RipeMD128': (32, True, False, False, None, None, None),
    'RipeMD160': (40, True, False, False, None, None, None),
    'RipeMD256': (64, True, False, False, None, None, None),
    'RipeMD320': (80, True, False, False, None, None, None),
    'SAM': (65, False, False, False, False, None, (32, 33, ':')),
    'SHA1': (40, True, False, False, None, None, None),
    'SHA1Django': (52, False, False, False, None, None, (0, 5, 'sha1$')),
    'SHA1MaNGOS': (40, True, False, False, None, None, None),
    'SHA1MaNGOS2': (40, True, False, False, None, None, None),
    'SHA224': (56, True, False, False, None, None, None),
    'SHA256': (64, True, False, False, None, None, None),
    'SHA256Django': (78, False, False, False, None, None, (0, 6, 'sha256')),
    'SHA256s': (98, False, False, False, None, None, (0, 3, '$6$')),
    'SHA384': (96, True, False, False, None, None, None),
    'SHA384Django': (110, False, False, False, None, None, (0, 6, 'sha384')),
    'SHA512': (128, True, False, False, None, None, None),
    'SNEFRU128': (32, True, False, False, None, None, None),
    'SNEFRU256': (64, True, False, False, None, None, None),
    'Tiger128': (32, True, False, False, None, None, None),
    'Tiger160': (40, True, False, False, None, None, None),
    'Tiger192': (48, True, False, False, None, None, None),
    'Whirlpool': (128, True, False, False, None, None, None),
    'XOR32': (8, True, False, False, None, None, None),
}
