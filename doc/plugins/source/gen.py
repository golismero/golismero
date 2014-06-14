#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
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

# Fix the module path.
import sys
import os
from os import path
here = path.split(path.abspath(__file__))[0]
if not here:  # if it fails use cwd instead
    here = path.abspath(os.getcwd())
golismero = path.join(here, "..", "..")
thirdparty_libs = path.join(golismero, "thirdparty_libs")
if path.exists(thirdparty_libs):
    sys.path.insert(0, thirdparty_libs)
    sys.path.insert(0, golismero)

from golismero.api.plugin import get_plugin_type_display_name, get_plugin_type_description
from golismero.managers.pluginmanager import PluginManager
from golismero.common import OrchestratorConfig

categories = ("import", "recon", "scan", "attack", "intrude", "cleanup", "report", "ui")

index = """List of plugins
===============

These are the plugins shipped by default with GoLismero:

.. toctree::
   :maxdepth: 2

""".replace("\r\n", "\n")

def gen():
    pluginManager = PluginManager()
    pluginManager.find_plugins( OrchestratorConfig() )
    for plugin_type in categories:
        with open(path.join(here, plugin_type + ".rst"), "w") as f:
            name = get_plugin_type_display_name(plugin_type)
            print >>f, name
            print >>f, "*" * len(name)
            print >>f, ""
            print >>f, get_plugin_type_description(plugin_type)
            print >>f, ""
            plugins = pluginManager.get_plugins(plugin_type)
            if plugins:
                for plugin_id in sorted(plugins.keys()):
                    plugin_info = plugins[plugin_id]
                    display_name = "%s (*%s*)" % (plugin_info.display_name, plugin_id[plugin_id.rfind("/")+1:])
                    description = plugin_info.description
                    description = description.replace("\r\n", "\n")
                    description = description.replace("\n", "\n\n")
                    print >>f, display_name
                    print >>f, "=" * len(display_name)
                    print >>f, ""
                    print >>f, description
                    print >>f, ""
                    if plugin_info.plugin_args:
                        width_key = 17
                        width_value = 17
                        for key, value in plugin_info.plugin_args.iteritems():
                            if key in plugin_info.plugin_passwd_args:
                                value = "\\*" * 16
                            width_key = max(width_key, len(key))
                            width_value = max(width_value, len(value))
                        print >>f, "%s %s" % (("=" * width_key), ("=" * width_value))
                        print >>f, ("**Argument name**%s **Default value**%s" % ((" " * (width_key - 17)), (" " * (width_value - 17)))).rstrip()
                        print >>f, "%s %s" % (("-" * width_key), ("-" * width_value))
                        for key, value in plugin_info.plugin_args.iteritems():
                            value = value.replace("\r\n", "\n")
                            value = value.replace("\n", " ")
                            if key in plugin_info.plugin_passwd_args:
                                value = "\\*" * 16
                            pad_key = (" " * (width_key - len(key)))
                            pad_value = (" " * (width_value - len(value)))
                            print >>f, ("%s%s %s%s" % (key, pad_key, value, pad_value)).rstrip()
                        print >>f, ("%s %s" % (("=" * width_key), ("=" * width_value))).rstrip()
                        print >>f, ""
            else:
                print >>f, "There are currently no plugins in this category."
                print >>f, ""
        with open(path.join(here, plugin_type + ".rst"), "rU") as f:
            data = f.read()
        with open(path.join(here, plugin_type + ".rst"), "wb") as f:
            f.write(data)
    with open("index.rst", "wb") as f:
        f.write(index)
        for plugin_type in categories:
            f.write("   %s\n" % plugin_type)

if __name__ == '__main__':
    gen()
