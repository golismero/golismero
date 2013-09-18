#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fingerprint the operating system of a remote host.
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

from golismero.api.config import Config
from golismero.api.logger import Logger
from golismero.api.data import discard_data
from golismero.api.net.http import HTTP
from golismero.api.net.scraper import extract_from_html, extract_from_text
from golismero.api.plugin import TestingPlugin
from golismero.api.net.web_utils import ParsedURL, download
from golismero.api.text.wordlist import WordListLoader
from traceback import format_exc

from golismero.api.text.matching_analyzer import get_diff_ratio

# Resources
from golismero.api.data.resource.ip import IP
from golismero.api.data.resource.url import BaseUrl

# Informations
from golismero.api.data.information import Information
from golismero.api.data.information.os_fingerprint import OSFingerprint

import os
import os.path
import sys
from collections import Counter


# Import ping library.
cwd = os.path.abspath(os.path.split(__file__)[0])
cwd = os.path.join(cwd, "osfingerprint")
sys.path.insert(0, cwd)
try:
    from ping import do_ping_and_receive_ttl
finally:
    sys.path.remove(cwd)
del cwd


class OSFingerprinting(TestingPlugin):
    """
    Plugin to fingerprint the remote OS.
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [IP, BaseUrl]


    #----------------------------------------------------------------------
    def recv_info(self, info):
        """
        Main function for OS fingerprint. Get a domain or IP and return the fingerprint results.

        :param info: Folder URL.
        :type info: FolderUrl

        :return: OS Fingerprint.
        :rtype: OSFingerprint
        """

        #
        # Detection methods and their weights.
        #
        # The weight is a value between 1-5
        #

        FINGERPRINT_METHODS_OS_AND_VERSION = {
            'ttl'                  : {
                'function'   : self.ttl_platform_detection,
                'weight'     : 2
            }
        }

        FUNCTIONS = None # Fingerprint methods to run
        m_host    = None

        is_windows     = None

        if isinstance(info, IP):
            m_host = info.address
            FUNCTIONS = ['ttl']
        else: # BaseUrl
            m_host         = info.hostname
            FUNCTIONS      = ['ttl']

            # Try to detect if remote system is a Windows
            m_windows_host = "%s://%s:%s" % (info.parsed_url.scheme, info.parsed_url.host, info.parsed_url.port)
            is_windows     = self.is_URL_in_windows(m_windows_host)

        # Logging
        Logger.log_more_verbose("Starting OS fingerprinting plugin for site: %s" % m_host)


        m_counter = Counter()
        # Run functions
        for f in FUNCTIONS:
            l_function   = FINGERPRINT_METHODS_OS_AND_VERSION[f]['function']

            ### For future use
            ### l_weight     = FINGERPRINT_METHODS_OS_AND_VERSION[f]['weight']

            # Run
            results      = l_function(m_host)

            if results:
                for l_r in results:
                    m_counter[l_r] += 1


        # Return value
        m_return = None

        #
        # Filter the results
        #
        if len(m_counter) > 0:
            # Fooking for a windows system
            if is_windows: # If Windows is detected
                l_counter = Counter()

                # Extract windows systems
                for x, y in m_counter.iteritems():
                    if "windows" == x:
                        l_counter[x] += y

                # Replace the counter for the new
                m_counter = l_counter

            # Get most common systems
            l_most_common = m_counter.most_common(5)

            # First elemente will be the detected OS
            m_OS_family  = l_most_common[0][0][0]
            m_OS_version = l_most_common[0][0][1]

            # Next 4 will be the 'others'
            m_length = float(len(l_most_common))
            m_others = {"%s-%s" % (l_most_common[i][0][0], l_most_common[i][0][1]): float('{:.2f}'.format(l_most_common[i][1]/m_length)) for i in xrange(1, len(l_most_common), 1)}

            # create the data
            m_return = OSFingerprint(m_OS_family, m_OS_version, others=m_others)


        elif is_windows is not None:
            if is_windows: # Windows system detected
                m_return = OSFingerprint("windows")
            else: # *NIX system detected
                m_return = OSFingerprint("unix_or_compatible")

        # If there is information, associate it with the resource
        if m_return:
            info.add_information(m_return)


        return m_return


    #----------------------------------------------------------------------
    #
    # Platform detection methods
    #
    #----------------------------------------------------------------------
    def is_URL_in_windows(self, main_url):
        """
        Detect if platform is Windows or \*NIX. To do this, get the first link, in scope, and
        does two resquest. If are the same response, then, platform are Windows. Else are \*NIX.

        :returns: True, if the remote host is a Windows system. False is \*NIX or None if unknown.
        :rtype: bool
        """
        m_forbidden = (
            "logout",
            "logoff",
            "exit",
            "sigout",
            "signout",
        )

        # Get the main web page
        m_r = download(main_url, callback=self.check_download)
        if not m_r or not m_r.raw_data:
            return None
        discard_data(m_r)

        # Get the first link
        m_links = None
        try:
            if m_r.information_type == Information.INFORMATION_HTML:
                m_links = extract_from_html(m_r.raw_data, main_url)
            else:
                m_links = extract_from_text(m_r.raw_data, main_url)
        except TypeError,e:
            Logger.log_error_more_verbose("Plugin error: %s" % format_exc())
            return None

        if not m_links:
            return None

        # Get the first link of the page that's in scope of the audit
        m_first_link = None
        for u in m_links:
            if u in Config.audit_scope and not any(x in u for x in m_forbidden):
                m_first_link = u
                break

        if not m_first_link:
            return None

        # Now get two request to the links. One to the original URL and other
        # as upper URL.

        # Original
        m_response_orig  = HTTP.get_url(m_first_link, callback=self.check_response)  # FIXME handle exceptions!
        discard_data(m_response_orig)
        # Uppercase
        m_response_upper = HTTP.get_url(m_first_link.upper(), callback=self.check_response)  # FIXME handle exceptions!
        discard_data(m_response_upper)
        # Compare them
        m_orig_data      = m_response_orig.raw_response  if m_response_orig  else ""
        m_upper_data     = m_response_upper.raw_response if m_response_upper else ""
        m_match_level    = get_diff_ratio(m_orig_data, m_upper_data)

        # If the responses are equal by 90%, two URL are the same => Windows; else => *NIX
        m_return = None
        if m_match_level > 0.95:
            m_return = True
        else:
            m_return = False

        return m_return


    #----------------------------------------------------------------------
    def ttl_platform_detection(self, main_url):
        """
        This function tries to recognize the remote platform doing a ping and analyzing the
        TTL of IP header response.

        :param main_url: Base url to test.
        :type main_url: str

        :return: Possible platforms.
        :rtype: list(tuple(OS, version))
        """

        # Do a ping
        try:
            m_ttl               = do_ping_and_receive_ttl(ParsedURL(main_url).hostname, 2)

            # Load words for the wordlist
            l_wordlist_instance = WordListLoader.get_advanced_wordlist_as_dict(Config.plugin_config["wordlist_ttl"])
            # Looking for matches
            l_matches           = l_wordlist_instance.matches_by_value(m_ttl)

            if l_matches:
                m_ret = {}
                for v in l_matches:
                    sp = v.split("|")
                    k = sp[0].strip()
                    v = sp[1].strip()
                    m_ret[k] = v

                return [(k,v) for k,v in m_ret.iteritems()]
            else:
                return {}
        except EnvironmentError:
            Logger.log_error("[!] You can't run the platform detection plugin if you're not root.")
            return {}
        except Exception, e:
            Logger.log_error("[!] Platform detection failed, reason: %s" % e)
            return {}


    #----------------------------------------------------------------------
    #
    # Aux functions
    #
    #----------------------------------------------------------------------
    def check_download(self, url, name, content_length, content_type):

        # Returns True to continue or False to cancel.
        return (

            # Check the file type is text.
            content_type and content_type.strip().lower().startswith("text/") and

            # Check the file is not too big.
            content_length and content_length < 100000
        )


    def check_response(self, request, url, status_code, content_length, content_type):

        # Returns True to continue, False to cancel.
        return (

            # Check the content length is not too large.
            content_length is not None and content_length < 200000

        )
