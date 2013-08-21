#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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


# Fix the module path for the tests.
import sys
import os
from os import path
try:
    _FIXED_PATH_
except NameError:
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "../../..")
    thirdparty_libs = path.join(golismero, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        sys.path.insert(0, thirdparty_libs)
        sys.path.insert(0, golismero)
    _FIXED_PATH_ = True



from golismero.api.data import Data
from golismero.api.data.db import Database
from golismero.api.data.resource import Resource
from os.path import join, dirname


from django.template import Template, loader, Context
import django.conf



#----------------------------------------------------------------------
def main(output_file):
    """"""
    django.conf.settings.configure(
        TEMPLATE_DIRS = (join(dirname(__file__), '.'),)
    )

    c = Context()
    t = loader.get_template(template_name="template.html")

    #
    # Fill the context
    #

    # Audit name
    c['audit_name']        = "Test audit name"
    c['execution_time']    = 10
    c['summary_vulns']     = {'total': 26, 'high' : 10 , 'middle': 5, 'low': 10, 'informational': 1}


    c['info_by_resource']  = [
        {
            # Resource type URL
            'resource_type' : "URL",
            'info'          : [
                # Resource 1
                {
                    # Index of row
                    'index'  :  '1',

                    # Resource info
                    'resource' : {
                        'URI'       : "http",
                        'main_info' : "http://www.mytest.site.com",
                        'prop' : [
                            {
                                'name'  : '',
                                'value' : ''
                             }
                        ]
                    },

                    # Vulns
                    'vulns'  : [
                        {
                            'level'   : 'high',
                            'number'  : '4'
                        }
                    ]
                },

                # Resource 2
                {
                    # Index of row
                    'index'  :  '2',

                    # Resource info
                    'resource' : {
                        'URI'       : "http",
                        'main_info' : "http://www.othersite.com"
                    },

                    # Vulns
                    'vulns'  : [
                        {
                            'level'   : 'high',
                            'number'  : '2'
                        },
                        {
                            'level'   : 'middle',
                            'number'  : '23'
                        },
                        {
                            'level'   : 'low',
                            'number'  : '1'
                        }
                    ]
                }
            ]
        }
    ]

    #
    # Write the output
    #
    m_rendered = t.render(c)

    f = open(output_file, "w")
    f.write("%s" % m_rendered.encode("utf-8"))
    f.close()

if __name__ == "__main__":
    main(join(dirname(__file__),"results.html"))