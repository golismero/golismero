#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
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

__doc__ = """

This scripts convert and URL wordlist into a simple wordlist with only the domains.

"""
import os
import argparse
from urlparse import urlparse, urlsplit


#------------------------------------------------------------------------------
def main(args):
    """"""

    file_output   = args.FILE_OUTPUT
    file_in       = args.WORDLIST_IN

    print "[*] Preparing for parsing file: %s" % file_in

    w_filtered        = set()
    w_filtered_add    = w_filtered.add

    # Read file
    with open(file_in, "rU") as f:

        for l in iter(f.readline, ''):
            prefix = l.replace("\n", "").strip()

            # Break for comments
            if prefix.startswith("#"):
                continue

            # Parse URL
            try:
                hostname = urlsplit(prefix).netloc
                hostname = ".".join(hostname.split(".")[-2:])
            except ValueError: # Error parsing
                print "[i] Error parsing URL '%s' to check poisoned dns." % prefix
                continue

            # store
            w_filtered_add("%s\n" % hostname)

    # Write results
    with open(file_output, "w") as f:
        f.writelines(w_filtered)

    print "[*] Parsed %s URLs." % len(w_filtered)


if __name__=='__main__':

    parser = argparse.ArgumentParser(description='Generates a filtered wordlist of malware wordlist.')
    parser.add_argument('-o', dest="FILE_OUTPUT", help="file output place.", required=True)
    parser.add_argument('-i', dest="WORDLIST_IN", help="wordlist file input.", required=True)

    args = parser.parse_args()

    main(args)
