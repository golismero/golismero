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
from golismero.api.data.information import Information
from golismero.api.data.resource.email import Email
from golismero.api.data.resource.url import Url
from golismero.api.logger import Logger
from golismero.api.net import NetworkException
from golismero.api.net.scraper import extract_from_html, extract_from_text, extract_forms_from_html
from golismero.api.net.web_utils import download, parse_url
from golismero.api.plugin import TestingPlugin
from golismero.api.text.wordlist import WordListLoader

from traceback import format_exc
from warnings import warn


#------------------------------------------------------------------------------
class Spider(TestingPlugin):
    """
    This plugin is a web spider.
    """


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        m_return = []

        m_url = info.url

        Logger.log_verbose("Spidering URL: %s" % m_url)

        # Check if need follow first redirect, then follow the link.
        p = None
        try:
            allow_redirects = Config.audit_config.follow_redirects or \
                (info.depth == 0 and Config.audit_config.follow_first_redirect)
            p = download(m_url, self.check_download,
                         allow_redirects=allow_redirects)
        except NetworkException, e:
            Logger.log_error_verbose(
                "Error while processing %r: %s" % (m_url, str(e)))

        if not p:
            return m_return

        # Send back the data
        m_return.append(p)

        # TODO: If it's a 301 response, get the Location header

        # Get links
        m_forms = None
        if p.information_type == Information.INFORMATION_HTML:
            m_links = extract_from_html(p.raw_data, m_url)
            m_forms = extract_forms_from_html(p.raw_data, m_url)
            #m_links.update( extract_from_text(p.raw_data, m_url) )
        elif p.information_type == Information.INFORMATION_PLAIN_TEXT:
            m_links = extract_from_text(p.raw_data, m_url)
        else:
            return m_return
        try:
            m_links.remove(m_url)
        except Exception:
            pass

        # Do not follow URLs that contain certain keywords
        m_forbidden = [x for x in WordListLoader.get_wordlist(Config.plugin_config["wordlist_no_spider"])]
        m_urls_allowed = [
            url for url in m_links if not any(x in url for x in m_forbidden)
        ]
        m_urls_not_allowed = m_links.difference(m_urls_allowed)
        if m_urls_not_allowed:
            Logger.log_more_verbose("Skipped forbidden URLs:\n    %s" % "\n    ".join(sorted(m_urls_not_allowed)))

        # Do not follow URLs out of scope
        m_urls_in_scope = []
        m_broken = []
        for url in m_urls_allowed:
            try:
                if url in Config.audit_scope:
                    m_urls_in_scope.append(url)
            except Exception:
                m_broken.append(url)
        if m_broken:
            if len(m_broken) == 1:
                Logger.log_more_verbose("Skipped uncrawlable URL: %s" % m_broken[0])
            else:
                Logger.log_more_verbose("Skipped uncrawlable URLs:\n    %s" % "\n    ".join(sorted(m_broken)))
        m_out_of_scope_count = len(m_urls_allowed) - len(m_urls_in_scope) - len(m_broken)
        if m_out_of_scope_count:
            Logger.log_more_verbose("Skipped %d links out of scope." % m_out_of_scope_count)

        if m_urls_in_scope:
            Logger.log_verbose("Found %d links in URL: %s" % (len(m_urls_allowed), m_url))
        else:
            Logger.log_verbose("No links found in URL: %s" % m_url)

        # Convert to Url data type
        for u in m_urls_in_scope:
            try:
                p = parse_url(u)
                if p.scheme == "mailto":
                    m_resource = Email(p.netloc)
                elif p.scheme in ("http", "https"):
                    m_resource = Url(url = u, referer = m_url)
            except Exception:
                warn(format_exc(), RuntimeWarning)
            m_resource.add_resource(info)
            m_return.append(m_resource)

        # Get forms info
        if m_forms:
            m_forms_allowed = [
                url for url in m_forms
                if not any(x in url[0] for x in m_forbidden)
            ]
            m_forms_not_allowed = {
                x[0] for x in m_forms
            }.difference(x[0] for x in m_forms_allowed)
        else:
            m_forms_allowed = []
            m_forms_not_allowed = set()

        if m_forms_not_allowed:
            Logger.log_more_verbose("Skipped forbidden forms:\n    %s" % "\n    ".join(sorted(m_forms_not_allowed)))

        # Do not follow forms out of scope
        m_forms_in_scope = []
        m_broken = []
        for url in m_forms_allowed:
            try:
                if url[0] in Config.audit_scope:
                    m_forms_in_scope.append(url)
            except Exception:
                m_broken.append(url[0])

        if m_broken:
            if len(m_broken) == 1:
                Logger.log_more_verbose("Skipped uncrawlable forms: %s" % m_broken[0])
            else:
                Logger.log_more_verbose("Skipped uncrawlable forms:\n    %s" % "\n    ".join(sorted(m_broken)))
        m_out_of_scope_count = len(m_forms_allowed) - len(m_forms_in_scope) - len(m_broken)
        if m_out_of_scope_count:
            Logger.log_more_verbose("Skipped %d forms out of scope." % m_out_of_scope_count)

        if m_forms_in_scope:
            Logger.log_verbose("Found %d forms in URL: %s" % (len(m_forms_in_scope), m_url))
        else:
            Logger.log_verbose("No forms found in URL: %s" % m_url)

        # Convert to Url data type
        for u in m_forms_in_scope:
            try:
                url = u[0]
                method = u[1]
                params = {x["name"]: x["value"] for x in u[2]}

                m_resource = Url(url = url, referer = m_url, method=method, post_params=params)
            except Exception:
                warn(format_exc(), RuntimeWarning)
            m_resource.add_resource(info)
            m_return.append(m_resource)

        # Send the results
        return m_return


    #--------------------------------------------------------------------------
    def check_download(self, url, name, content_length, content_type):

        # Only accept content when the content type header is present.
        if not content_type:
            Logger.log_more_verbose(
                "Skipping URL, missing content type: %s" % url)
            return False

        # Is the content length present?
        if content_length is not None:

            # Check the file doesn't have 0 bytes.
            if content_length <= 0:
                Logger.log_more_verbose(
                    "Skipping URL, empty content: %s" % url)
                return False

            # Check the file is not too big.
            if content_type.strip().lower().startswith("text/"):
                if content_length > 100000:
                    Logger.log_more_verbose(
                        "Skipping URL, content too large (%d bytes): %s"
                        % (content_length, url))
                    return False
            else:
                if content_length > 5000000:
                    Logger.log_more_verbose(
                        "Skipping URL, content too large (%d bytes): %s"
                        % (content_length, url))
                    return False

            # Approved!
            return True

        # Content length absent but likely points to a directory index.
        parsed_url = parse_url(url)
        if not parsed_url.filename:

            # Approved!
            return True

        # Extension absent.
        if not parsed_url.extension:

            # Approved!
            return True

        # Match against a known list of valid HTML extensions.
        # See: http://en.wikipedia.org/wiki/List_of_file_formats#Webpage
        if parsed_url.extension in (
                ".xml", ".html", ".htm", ".xhtml", ".xht",
                ".mht", ".mhtml", ".maff", ".asp", ".aspx", ".bml",
                ".cfm", ".cgi", ".ihtml", ".jsp", ".las", ".lasso",
                ".lassoapp", ".pl", ".php", ".php3", ".phtml",
                ".rna", ".r", ".rnx", ".shtml", ".stm", ".atom",
                ".xml", ".eml", ".jsonld", ".metalink", ".met",
                ".rss", ".xml", ".markdown"):

            # Approved!
            return True

        # If URL path in blacklist?
        m_forbidden = [x for x in WordListLoader.get_wordlist(Config.plugin_config["wordlist_no_spider"])]
        if any(x in url for x in m_forbidden):
            return False

        # Success!
        return True
