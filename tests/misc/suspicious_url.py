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

from golismero.api.data.information import Information
from golismero.api.logger import Logger
from golismero.api.config import Config
from golismero.api.text.wordlist import WordListLoader, WordlistNotFound
from golismero.api.crypto import calculate_shannon_entropy
from golismero.api.data import Data
from golismero.api.data.information.html import HTML
from golismero.api.data.information.text import Text
from golismero.api.data.resource import Resource
from golismero.api.data.resource.url import URL
from golismero.api.data.vulnerability.suspicious.url import SuspiciousURLPath
from golismero.api.data.vulnerability.malware.malicious import MaliciousUrl
from golismero.api.plugin import TestingPlugin
from golismero.api.net.scraper import extract_from_html, extract_from_text

from traceback import format_exc


#------------------------------------------------------------------------------
class SuspiciousURLPlugin(TestingPlugin):
    """
    Find suspicious words in URLs.
    """


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [URL, HTML, Text]


    #--------------------------------------------------------------------------
    def run(self, info):

        if info.is_instance(URL):
            return self.analyze_url(info)
        return self.analyze_html(info)


    #--------------------------------------------------------------------------
    def analyze_url(self, info):

        m_parsed_url = info.parsed_url
        m_results = []

        Logger.log_more_verbose("Processing URL: %s" % m_parsed_url)


        #----------------------------------------------------------------------
        # Find suspicious URLs by matching against known substrings.

        # Load wordlists
        m_wordlist_middle     = WordListLoader.get_wordlist(Config.plugin_config['middle'])
        m_wordlist_extensions = WordListLoader.get_wordlist(Config.plugin_config['extensions'])

        # Add matching keywords at any positions of URL.
        m_results.extend([SuspiciousURLPath(info, x)
                          for x in m_wordlist_middle
                          if x in m_parsed_url.directory.split("/") or
                          x == m_parsed_url.filebase or
                          x == m_parsed_url.extension])

        # Add matching keywords at any positions of URL.
        m_results.extend([SuspiciousURLPath(info, x)
                          for x in m_wordlist_extensions
                          if m_parsed_url.extension == x])


        #----------------------------------------------------------------------
        # Find suspicious URLs by calculating the Shannon entropy of the hostname.
        # Idea from: https://github.com/stricaud/urlweirdos/blob/master/src/urlw/plugins/shannon/__init__.py
        # TODO: test with unicode enabled hostnames!

        # Check the Shannon entropy for the hostname.
        hostname = info.parsed_url.hostname
        entropy = calculate_shannon_entropy(hostname)
        if entropy > 4.0:
            m_results.append( SuspiciousURLPath(info, hostname) )

        # Check the Shannon entropy for the subdomains.
        for subdomain in info.parsed_url.hostname.split('.'):
            if len(subdomain) > 3:
                entropy = calculate_shannon_entropy(subdomain)
                if entropy > 4.0:
                    m_results.append( SuspiciousURLPath(info, subdomain) )

        return m_results


    #--------------------------------------------------------------------------
    def analyze_html(self, info):


        #----------------------------------------------------------------------
        # Get malware suspicious links.

        Logger.log_more_verbose("Processing HTML: %s" % info.identity)

        # Load the malware wordlist.
        wordlist_filename = Config.plugin_config["malware_sites"]
        try:
            wordlist = WordListLoader.get_advanced_wordlist_as_list(
                wordlist_filename)
        except WordlistNotFound:
            Logger.log_error("Wordlist '%s' not found.." % wordlist_filename)
            return
        except TypeError:
            Logger.log_error(
                "Wordlist '%s' is not a file." % wordlist_filename)
            return
        if not wordlist:
            Logger.log_error("Wordlist '%s' is empty." % wordlist_filename)

        Logger.log("1")

        # Get links
        base_urls = set()
        for url in info.find_linked_data(Data.TYPE_RESOURCE,
                                         Resource.RESOURCE_URL):
            m_url = url.url
            base_urls.add(m_url)
            if info.information_type == Information.INFORMATION_HTML:
                m_links = extract_from_html(info.raw_data, m_url)
                m_links.update( extract_from_text(info.raw_data, m_url) )
            elif info.information_type == Information.INFORMATION_PLAIN_TEXT:
                m_links = extract_from_text(info.raw_data, m_url)
            else:
                raise Exception("Internal error!")
        m_links.difference_update(base_urls)

        Logger.log("2")

        # If we have no links, abort now
        if not m_links:
            Logger.log_verbose("No output links found.")
            return

        # Do not follow URLs that contain certain keywords
        m_forbidden = WordListLoader.get_wordlist(
            Config.plugin_config["wordlist_no_spider"])
        m_urls_allowed = {
            url for url in m_links
            if url and not any(x in url for x in m_forbidden)
        }

        Logger.log("3")

        # Get only output links
        m_output_links = []
        for url in m_urls_allowed:
            try:
                if url not in Config.audit_scope:
                    m_output_links.append(url)
            except Exception, e:
                Logger.log_error_more_verbose(format_exc())

        Logger.log("4")

        wordlist_filtered = {
            x for x in wordlist
            if x and not x.startswith("#") and not x.startswith("[")
        }

        Logger.log("5")

        m_results = []
        l_malware_sites_found = m_urls_allowed.intersection(wordlist_filtered)
        Logger.log_more_verbose("Found links to possible malware sites:\n%s"
            % "\n".join(" - " + x for x in sorted(l_malware_sites_found)))
        for l_malware_site in l_malware_sites_found:

            # Out url
            u = URL(url = l_malware_site, referer = info.url)

            v = MaliciousUrl(u)
            v.add_resource(info)

            m_results.append(v)
            m_results.append(u)

        Logger.log("6")

        if m_results:
            Logger.log_verbose("Discovered %s links to malware sites."
                               % len(m_results))
        else:
            Logger.log_verbose("No output links to malware sites found.")

        return m_results
