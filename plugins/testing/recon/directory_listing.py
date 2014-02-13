#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

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

import os
import re

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

from golismero.api.logger import Logger
from golismero.api.data.vulnerability.information_disclosure.directory_listing import DirectoryListing
from golismero.api.data.information.http import HTTP_Response
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
# Plecost plugin extra files.
base_dir = os.path.split(os.path.abspath(__file__))[0]
plugin_dir = os.path.join(base_dir, "directory_listing_plugin")
plugin_data = os.path.join(plugin_dir, "signatures.dat")

del base_dir


#------------------------------------------------------------------------------
class DirectoryListingPlugin(TestingPlugin):
    """
    This plugin detect and try to discover directory listing in folders and Urls.
    """


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return [HTTP_Response]


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        if not isinstance(info, HTTP_Response):
            return

        response = info.data
        url = list(info.associated_resources)[0]

        # Load signatures
        try:
            signatures = pickle.load(open(plugin_data, "rb"))
        except pickle.PickleError:
            signatures = {}

        # Starting the search
        total = float(len(signatures))

        for step, (server_name, regex) in enumerate(signatures.iteritems()):

            # Update status
            progress = (step / total) * 100
            self.update_status(progress=progress)

            if re.search(regex, response):

                # Match found.
                vulnerability = DirectoryListing(url,
                                                 server_name,
                                                 title="Directory listing for server '%s'" % server_name)

                return vulnerability



