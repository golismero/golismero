#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  [AUTHOR OF PLUGIN]

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

#
# Uncomment the imports you need...
#
# PLUGIN API:
#
# - Access to the plugin configuration:
# from golismero.api.config import Config
#
# - Log writer:
# from golismero.api.logger import Logger
#
# DATA MODEL:
#
# - Information types:
# from golismero.api.data.information.html import HTML
# from golismero.api.data.information.text import Text
# from golismero.api.data.information.binary import Binary
#
# - Resource types:
# from golismero.api.data.resource.url import Url, BaseUrl, FolderUrl
# from golismero.api.data.resource.domain import Domain
#
# - Vulnerability types:
# from golismero.api.data.vulnerability.information_disclosure.url_disclosure import UrlDisclosure
# from golismero.api.data.vulnerability.suspicious.url import SuspiciousURL
#
# OTHER API FUNCTIONS:
#
# - Network connections and protocols:
# from golismero.api.net.protocol import NetworkAPI
#
# - Web helper functions.
# from golismero.api.net.web_utils import fix_url, check_auth, get_auth_obj, detect_auth_method, is_in_scope, generate_error_page_url, ParsedURL, HTMLElement, HTMLParser
#
# - Text helper functions:
# from golismero.api.text.text_utils import generate_random_string, split_first
#
# - Differential analyzer:
# from golismero.api.text.matching_analyzer import get_matching_level
#
# - Wordlists (for bruteforcing):
# from golismero.api.text.wordlist import WordListLoader
#


# Testing plugins are the ones that perform the security tests.
# This is the base class for all Testing plugins.
from golismero.api.plugin import TestingPlugin


#----------------------------------------------------------------------
class TemplatePlugin(TestingPlugin):

    # Don't forget to change your class name!
    # You can name it however you like, as long
    # as it derives from TestingPlugin.


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        #
        # Here you must specify which data types
        # does your plugin want to receive.
        #
        # Example:
        #
        # return [Url, BaseUrl]
        #
        return None  # Returning None causes all data to be received.


    #----------------------------------------------------------------------
    def recv_info(self, info):
        #
        #
        # PUT YOUR CODE HERE
        #
        #
        pass
