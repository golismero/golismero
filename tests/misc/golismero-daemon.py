#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Daemon for GoLismero.
"""

__license__="""
GoLismero 2.0 - The web knife.

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


#----------------------------------------------------------------------
# Python version check.
# We must do it now before trying to import any more modules.
#
# Note: this is mostly because of argparse, if you install it
#       separately you can try removing this check and seeing
#       what happens (we haven't tested it!).

import sys
from sys import version_info, exit
if __name__ == "__main__":
    if version_info < (2, 7) or version_info >= (3, 0):
        print "[!] You must use Python version 2.7"
        exit(1)


#----------------------------------------------------------------------
# Fix the module load path when running as a portable script and during installation.

import os
from os import path
try:
    _FIXED_PATH_
except NameError:
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    thirdparty_libs = path.join(here, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        has_here = here in sys.path
        has_thirdparty_libs = thirdparty_libs in sys.path
        if not (has_here and has_thirdparty_libs):
            if has_here:
                sys.path.remove(here)
            if has_thirdparty_libs:
                sys.path.remove(thirdparty_libs)
            if __name__ == "__main__":
                # As a portable script: use our versions always.
                sys.path.insert(0, thirdparty_libs)
                sys.path.insert(0, here)
            else:
                # When installing: prefer system version to ours.
                sys.path.insert(0, here)
                sys.path.append(thirdparty_libs)
    _FIXED_PATH_ = True


#----------------------------------------------------------------------
# Imported modules.

import daemon
from os import path


#----------------------------------------------------------------------
# GoLismero modules.

from golismero.api.config import Config
from golismero.common import OrchestratorConfig, AuditConfig, \
     get_profile, get_default_config_file
from golismero.main import launcher


#----------------------------------------------------------------------
# Start of program.

def main():

    # Get the config file name.
    config_file = get_default_config_file()
    if not config_file:
        raise RuntimeError("Could not find config file, aborting!")

    # Load the Orchestrator options.
    orchestrator_config = OrchestratorConfig()
    orchestrator_config.ui_mode = "web"
    orchestrator_config.color = False
    orchestrator_config.config_file = config_file
    orchestrator_config.from_config_file(orchestrator_config.config_file, allow_profile = True)
    if orchestrator_config.profile:
        orchestrator_config.profile_file = get_profile(orchestrator_config.profile)
        if orchestrator_config.profile_file:
            orchestrator_config.from_config_file(orchestrator_config.profile_file)
        else:
            raise RuntimeError("Could not find profile, aborting!")

    # Get the plugins folder from the parameters.
    # If no plugins folder is given, use the default.
    plugins_folder = orchestrator_config.plugins_folder
    if not plugins_folder:
        plugins_folder = path.abspath(__file__)
        plugins_folder = path.dirname(plugins_folder)
        plugins_folder = path.join(plugins_folder, "plugins")
        if not path.isdir(plugins_folder):
            from golismero import common
            plugins_folder = path.abspath(common.__file__)
            plugins_folder = path.dirname(plugins_folder)
            plugins_folder = path.join(plugins_folder, "plugins")
            if not path.isdir(plugins_folder):
                raise RuntimeError("Default plugins folder not found, aborting!")
        orchestrator_config.plugins_folder = plugins_folder

    # Check if all options are correct.
    orchestrator_config.check_params()

    # Launch GoLismero.
    launcher.run(orchestrator_config)


#------------------------------------------------------------
# Run as daemon.

if __name__ == '__main__':
    with daemon.DaemonContext():
        main()
