#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from golismero.api.crypto import calculate_shannon_entropy
from golismero.api.data.resource.url import Url
from golismero.api.data.vulnerability.suspicious.url import SuspiciousURL
from golismero.api.plugin import TestingPlugin
from golismero.api.text.wordlist import WordListLoader


class SuspiciousURLPlugin(TestingPlugin):
    """
    Find suspicious words in URLs.
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        m_parsed_url = info.parsed_url
        m_results = []

        #------------------------------------------------------------------
        # Find suspicious URLs by matching against known substrings.

        # Load wordlists
        m_wordlist_middle     = WordListLoader.get_wordlist(Config.plugin_config['middle'])
        m_wordlist_extensions = WordListLoader.get_wordlist(Config.plugin_config['extensions'])

        # Add matching keywords at any positions of URL.
        m_results.extend([SuspiciousURL(info, x)
                          for x in m_wordlist_middle
                          if x in m_parsed_url.directory.split("/") or
                          x == m_parsed_url.filebase or
                          x == m_parsed_url.extension])

        # Add matching keywords at any positions of URL.
        m_results.extend([SuspiciousURL(info, x)
                          for x in m_wordlist_extensions
                          if m_parsed_url.extension == x])

        #------------------------------------------------------------------
        # Find suspicious URLs by calculating the Shannon entropy of the hostname.
        # Idea from: https://github.com/stricaud/urlweirdos/blob/master/src/urlw/plugins/shannon/__init__.py
        # TODO: test with unicode enabled hostnames!

        # Check the Shannon entropy for the hostname.
        hostname = info.parsed_url.hostname
        entropy = calculate_shannon_entropy(hostname)
        if entropy > 4.0:
            m_results.append( SuspiciousURL(info, hostname) )

        # Check the Shannon entropy for the subdomains.
        for subdomain in info.parsed_url.hostname.split('.'):
            if len(subdomain) > 3:
                entropy = calculate_shannon_entropy(subdomain)
                if entropy > 4.0:
                    m_results.append( SuspiciousURL(info, subdomain) )

        #------------------------------------------------------------------

        return m_results
