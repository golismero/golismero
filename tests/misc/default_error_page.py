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

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

from golismero.api.logger import Logger
from golismero.api.data.vulnerability.information_disclosure.default_error_page import DefaultErrorPage
from golismero.api.text.matching_analyzer import get_diff_ratio
from golismero.api.data.information.http import HTTP_Response
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
# Plecost plugin extra files.
base_dir = os.path.split(os.path.abspath(__file__))[0]
plugin_dir = os.path.join(base_dir, "default_error_page_plugin")
plugin_data = os.path.join(plugin_dir, "signatures.dat")

del base_dir


#------------------------------------------------------------------------------
class DefaultErrorPagePlugin(TestingPlugin):
    """
    Find default error pages for the most common web servers.
    """


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [HTTP_Response]


    #--------------------------------------------------------------------------
    def run(self, info):

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
        for step, (server_name, server_page) in enumerate(signatures.iteritems()):

            # Update status
            progress = float(step) / total
            self.update_status(progress=progress)

            level = get_diff_ratio(response, server_page)
            Logger.log(level)
            if level > 0.55:  # magic number :)

                # Match found.
                vulnerability = DefaultErrorPage(url,
                                                 server_name,
                                                 title="Default error page for server '%s'" % server_name)

                return vulnerability



