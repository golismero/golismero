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

import argparse
import os
import csv
import re

try:
    import cPickle as Pickle
except ImportError:
    import pickle as Pickle

from urllib2 import urlopen, URLError
from sys import exit
from time import sleep
from random import randint
from codecs import decode

from BeautifulSoup import BeautifulSoup
from chardet import detect


WPlugins_URL = "http://wordpress.org/plugins/browse/popular/page/%s/"

REGEX_PLUGIN_NAME = re.compile(r"(http://wordpress.org/plugins/)([a-zA-Z0-9\\\s_\-`!()\[\]{};:'.,<>?«»‘’]+)([/]*\">)([a-zA-Z0-9\\\s_\-`!()\[\]{};:'.,?«»‘’]*)",
                               re.I)  # -> Group 2 and 3
REGEX_PLUGIN_VERSION = re.compile(r"(Version</span>[\sa-zA-Z]*)([0-9\.]+)", re.I)  # -> Group 2


#------------------------------------------------------------------------------
def load_cve_info():
    """
    Generate the CVE with WordPress vulns related DB and return a dict with the CVE and their description.

    :return: dict with { CVE : DESCRIPTION}
    :rtype: dict(* -> str)
    """
    cve_url = "http://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=wordpress"

    try:
        wpage = urlopen(cve_url).read()
    except URLError, e:
        print "[!] Can't obtain CVE database."
        return None

    try:
        wpage = decode(wpage, detect(wpage)["encoding"])
    except UnicodeEncodeError, e:
        print "[!] Unicode error while processing CVE url. Error: %s." % e
        return None

    results = {}

    # Parse
    bs = BeautifulSoup(wpage)

    # For echa plugin
    for cve_item in bs.find("div", attrs={'id': 'TableWithRules'}).findAll("tr")[1:]:
        rows = cve_item.findAll("td")
        cve_number = rows[0].find("a")["href"].split("=")[1]
        cve_description = rows[1].text.replace("\n", " ")

        results[cve_number] = cve_description

    return results


#------------------------------------------------------------------------------
def generate_plugin_db(args):
    """"""
    file_out = args.OUTPUT_FILE
    cve_file = os.path.join(os.path.split(file_out)[0], "cve.dat")
    debug = args.DEBUG
    max_plugins = args.MAX_PLUGINS

    if os.path.isdir(file_out):
        print
        print "[!] Output file must be regular file, not a directory."
        print
        exit(1)

    # Get CVE info
    CVE_info = load_cve_info()

    # Dump the info
    Pickle.dump(CVE_info, open(cve_file, "wb"))

    with open(file_out, "w") as out:

        already_processed = []
        already_processed_append = already_processed.append

        csv_file = csv.writer(out)

        total_plugins = 1

        for i in xrange(1, 4000):

            # 3 tries for each request
            for x in xrange(1, 6):
                try:
                    url = WPlugins_URL % i
                    wpage = urlopen(url).read()
                except URLError, e:
                    print "[!] Error while getting URL: %s. Attempt %s." % (url, x)
                    sleep(randint(1, 4))

                    if x == 6:
                        exit(0)
                    else:
                        continue

            if debug:
                print "[i] Page %s/4000 (%s)" % (i, url)

            # Fix err
            try:
                wpage = decode(wpage, detect(wpage)["encoding"])
            except UnicodeEncodeError, e:
                print "[!] Unicode error while processing url '%s'. Error: %s." % (url, e)
                continue

            # Parse
            bs = BeautifulSoup(wpage)

            # For echa plugin
            for j, plugin_info in enumerate(bs.findAll("div", attrs={"class": "plugin-block"})):

                plugin_info = unicode(plugin_info)

                #
                # Plugin name and URL
                #
                plugin_n_t = REGEX_PLUGIN_NAME.search(plugin_info)
                plugin_url = None
                plugin_name = None
                if plugin_n_t is None:
                    print "[iii] REGEX_PLUGIN_NAME can't found info for string: \n-------\n%s" % plugin_info
                else:
                    plugin_url = plugin_n_t.group(2) if len(plugin_n_t.groups()) >= 2 else None
                    plugin_name = plugin_n_t.group(4) if len(plugin_n_t.groups()) >= 4 else None

                # Coding fixes
                if plugin_name:
                    try:
                        plugin_name = decode(plugin_name, detect(plugin_name)["encoding"])
                    except UnicodeError:
                        try:
                            plugin_name = plugin_name.decode("UTF-8")
                        except UnicodeError:
                            plugin_name = plugin_url
                else:
                    plugin_name = plugin_url

                #
                # Plugin version
                #
                plugin_version = REGEX_PLUGIN_VERSION.search(plugin_info)
                if plugin_version is None:
                    print "[iii] REGEX_PLUGIN_VERSION can't found info for string: \n-------\n%s" % plugin_info
                else:
                    plugin_version = plugin_version.group(2)

                # Plugin is repeated and already processed?
                if plugin_url in already_processed:
                    if debug:
                        print "  |-- [ii] Already processed plugin '%s'. Skipping" % plugin_url
                    continue

                #
                # We have all information to continue?
                #
                if plugin_url is None or plugin_version is None:
                    if debug:
                        print "   |-- [ii] Not enough information to store plugin for:\n%s" % plugin_info
                    continue

                if debug:
                    print "  |-- %s - Processing plugin: %s" % (total_plugins, plugin_url)

                # Looking for CVEs for this plugin
                cves = []
                for k, v in CVE_info.iteritems():
                    if plugin_name.lower() in v.lower():
                        cves.append(k)

                # Write to file
                try:
                    csv_file.writerow([plugin_url, plugin_name, plugin_version, "|".join(cves)])
                except UnicodeEncodeError:
                    csv_file.writerow([plugin_url, plugin_url, plugin_version, "|".join(cves)])

                # Save plugin
                already_processed_append(plugin_url)

                # Maximun number of plugins reached?
                total_plugins += 1

                if total_plugins >= max_plugins:
                    return


#------------------------------------------------------------------------------
def main(args):
    generate_plugin_db(args)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generates WordPress plugins file')
    parser.add_argument('-o', dest="OUTPUT_FILE", help="output file (default: plugin_list.txt)",
                        default=os.path.join(os.path.abspath(os.path.split(__file__)[0]), "plugin_list.txt"))
    parser.add_argument('-v', action="store_true", dest="DEBUG", help="enable debug information", default=False)
    parser.add_argument('--max', dest="MAX_PLUGINS", type=int, help="maximun number of plugins to get (default 2.000)",
                        default=2000)

    args = parser.parse_args()

    main(args)
