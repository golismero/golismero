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
from golismero.api.data.resource.url import BaseUrl, Url
from golismero.api.logger import Logger
from golismero.api.net import NetworkException, NetworkOutOfScope
from golismero.api.net.http import HTTP
from golismero.api.net.web_utils import download, generate_error_page_url, fix_url
from golismero.api.plugin import TestingPlugin
from golismero.api.text.matching_analyzer import MatchingAnalyzer

import codecs
from urlparse import urljoin


#----------------------------------------------------------------------
class Robots(TestingPlugin):
    """
    This plugin analyzes robots.txt files looking for private pages.
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [BaseUrl]


    #----------------------------------------------------------------------
    def check_download(self, url, name, content_length, content_type):

        # Returns True to continue or False to cancel.
        return (

            # Check the file type is plain text.
            content_type and content_type.strip().lower().split(";")[0] == "text/plain" and

            # Check the file is not too big.
            content_length and content_length < 100000
        )


    #----------------------------------------------------------------------
    def check_response(self, request, url, status_code, content_length, content_type):

        # Returns True to continue or False to cancel.
        return (

            # No need to analyze if the response is not 200.
            status_code == "200" and

            # Check the data is some kind of text.
            content_type and content_type.strip().lower().startswith("text/") and

            # Check the page is not too big.
            content_length and content_length < 100000
        )


    #----------------------------------------------------------------------
    def recv_info(self, info):
        m_return = []

        m_url = info.url
        m_hostname = info.hostname
        m_url_robots_txt = urljoin(m_url, 'robots.txt')

        p = None
        try:
            msg = "Looking for robots.txt in: %s" % m_hostname
            Logger.log_more_verbose(msg)

            p = download(m_url_robots_txt, self.check_download)

        except NetworkOutOfScope:
            Logger.log_more_verbose("URL out of scope: %s" % (m_url_robots_txt))
            return
        except Exception, e:
            Logger.log_more_verbose("Error while processing %r: %s" % (m_url_robots_txt, str(e)))
            return

        # Check for errors
        if not p:
            Logger.log_more_verbose("No robots.txt found.")
            return


        u = Url(m_url_robots_txt, referer=m_url)
        p.add_resource(u)
        m_return.append(u)
        m_return.append(p)

        # Text with info
        m_robots_text = p.raw_data

        # Prepare for unicode
        try:
            if m_robots_text.startswith(codecs.BOM_UTF8):
                m_robots_text = m_robots_text.decode('utf-8').lstrip(unicode(codecs.BOM_UTF8, 'utf-8'))
            elif m_robots_text.startswith(codecs.BOM_UTF16):
                m_robots_text = m_robots_text.decode('utf-16')
        except UnicodeDecodeError:
            Logger.log_error_verbose("Error while parsing robots.txt: Unicode format error.")
            return

        # Extract URLs
        m_discovered_urls        = []
        m_discovered_urls_append = m_discovered_urls.append
        tmp_discovered           = None
        m_lines                  = m_robots_text.splitlines()

        # Var used to update the status
        m_lines_count            = len(m_lines)
        m_total                  = float(m_lines_count)

        for m_step, m_line in enumerate(m_lines):

            # Remove comments
            m_octothorpe = m_line.find('#')
            if m_octothorpe >= 0:
                m_line = m_line[:m_octothorpe]

            # Delete init spaces
            m_line = m_line.rstrip()

            # Ignore invalid lines
            if not m_line or ':' not in m_line:
                continue

            # Looking for URLs
            try:
                m_key, m_value = m_line.split(':', 1)
                m_key = m_key.strip().lower()
                m_value = m_value.strip()

                # Ignore wildcards
                if '*' in m_value:
                    continue

                if m_key in ('disallow', 'allow', 'sitemap') and m_value:
                    tmp_discovered = urljoin(m_url, m_value)
                    m_discovered_urls_append( tmp_discovered )
            except Exception,e:
                continue


        #
        # Filter results
        #

        # Generating error page
        m_error_page          = generate_error_page_url(m_url_robots_txt)
        m_response_error_page = HTTP.get_url(m_error_page, callback=self.check_response)
        if m_response_error_page:
            m_return.append(m_response_error_page)

            # Analyze results
            match = {}
            m_analyzer = MatchingAnalyzer(m_response_error_page.data)
            m_total = len(set(m_discovered_urls))
            for m_step, l_url in enumerate(set(m_discovered_urls)):
                progress = (float(m_step * 100) / m_total)
                self.update_status(progress=progress)
                l_url = fix_url(l_url, m_url)
                if l_url in Config.audit_scope:
                    l_p = HTTP.get_url(l_url, callback=self.check_response)  # FIXME handle exceptions!
                    if l_p:
                        match[l_url] = l_p
                        m_analyzer.append(l_p.data, url=l_url)

            # Generate results
            for i in m_analyzer.unique_texts:
                l_url = i.url
                l_p = match[l_url]
                m_result = Url(l_url, referer=m_url)
                m_result.add_information(l_p)
                m_return.append(m_result)
                m_return.append(l_p)

        # No tricky error page, assume the status codes work
        else:
            m_total = len(set(m_discovered_urls))
            for m_step, l_url in enumerate(set(m_discovered_urls)):
                progress = (float(m_step * 100) / m_total)
                self.update_status(progress=progress)
                l_url = fix_url(l_url, m_url)   # XXX FIXME
                try:
                    l_p = HTTP.get_url(l_url, callback=self.check_response)
                except NetworkOutOfScope:
                    continue
                except NetworkException:
                    continue
                if l_p:
                    m_result = Url(l_url, referer=m_url)
                    m_result.add_information(l_p)
                    m_return.append(m_result)
                    m_return.append(l_p)

        if m_return:
            Logger.log_more_verbose("Discovered %s URLs." % len(m_return))
        else:
            Logger.log_more_verbose("No URLs discovered.")

        return m_return
