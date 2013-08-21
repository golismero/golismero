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

# Fix the module path.
import sys
import os
from os import path
try:
    _FIXED_PATH_
except NameError:
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..", "..")
    thirdparty_libs = path.join(golismero, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        sys.path.insert(0, thirdparty_libs)
        sys.path.insert(0, golismero)
    _FIXED_PATH_ = True

from golismero.main.testing import PluginTester

stage_names = {
    "import"  : "Import",
    "recon"   : "Reconnaisance",
    "scan"    : "Scan",
    "attack"  : "Attack",
    "intrude" : "Intrude",
    "cleanup" : "Cleanup",
    "report"  : "Report",
    "ui"      : "User Interface",
}

stage_descriptions = {
    "import"  : "Import plugins collect previously found resources from other tools and store them in the audit database right before the audit starts.",
    "recon"   : "Reconnaisance plugins perform passive, non-invasive information gathering tests on the targets.",
    "scan"    : "Scan plugins perform active, non-invasive information gathering tests on the targets.",
    "attack"  : "Attack plugins perform invasive tests on the targets to exploit vulnerabilities in them.",
    "intrude" : "Intrude plugins use the access gained by Attack plugins to extract privileged information from the targets.",
    "cleanup" : "Cleanup plugins undo whatever changes the previous plugins may have done on the targets.",
    "report"  : "Report plugins control how the audit results will be exported.",
    "ui"      : "User Interface plugins control the way in which the user interacts with GoLismero.",
}

if __name__ == '__main__':
    with PluginTester(autoinit = False) as t:
        t.orchestrator_config.use_colors = False
        t.orchestrator_config.verbose = 0
        t.orchestrator_config.max_process = 0
        t.init_environment()
        for stage in ("import", "recon", "scan", "attack", "intrude", "cleanup", "report", "ui"):
            with open(path.join(here, "source", stage + ".rst"), "w") as f:
                print >>f, stage_names[stage]
                print >>f, "*" * len(stage_names[stage])
                print >>f, ""
                print >>f, stage_descriptions[stage]
                print >>f, ""
                plugins = t.orchestrator.pluginManager.get_plugins(stage)
                for plugin_name in sorted(plugins.keys()):
                    plugin_info = plugins[plugin_name]
                    display_name = "%s (*%s*)" % (plugin_info.display_name, plugin_name[plugin_name.rfind("/")+1:])
                    print >>f, display_name
                    print >>f, "=" * len(display_name)
                    print >>f, ""
                    print >>f, plugin_info.description
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
                        print >>f, "**Argument name**%s **Default value**%s" % ((" " * (width_key - 17)), (" " * (width_value - 17)))
                        print >>f, "%s %s" % (("-" * width_key), ("-" * width_value))
                        for key, value in plugin_info.plugin_args.iteritems():
                            if key in plugin_info.plugin_passwd_args:
                                value = "\\*" * 16
                            pad_key = (" " * (width_key - len(key)))
                            pad_value = (" " * (width_value - len(value)))
                            print >>f, "%s%s %s%s" % (key, pad_key, value, pad_value)
                        print >>f, "%s %s" % (("=" * width_key), ("=" * width_value))
                        print >>f, ""
