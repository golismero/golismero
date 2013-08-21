#!/usr/bin/env python
# -*- coding: utf-8 -*-


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

__all__ = []


#------------------------------------------------------------------------------
# Fix the module load path when running as a portable script and after installation.

import os
from os import path
import sys
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
                # As a portable script: use our versions always
                sys.path.insert(0, thirdparty_libs)
                sys.path.insert(0, here)
            else:
                # When installing: prefer system version to ours
                sys.path.insert(0, here)
                sys.path.append(thirdparty_libs)
    _FIXED_PATH_ = True


#------------------------------------------------------------------------------
# Python version check.
# We must do it now before trying to import any more modules.
#
# Note: this is mostly because of argparse, if you install it
#       separately you can try removing this check and seeing
#       what happens (we haven't tested it!).

from golismero import show_banner
from sys import version_info, exit
if __name__ == "__main__":
    if version_info < (2, 7) or version_info >= (3, 0):
        show_banner()
        print "[!] You must use Python version 2.7"
        exit(1)


#------------------------------------------------------------------------------
# Imported modules

import argparse
import datetime

from collections import defaultdict
from ConfigParser import RawConfigParser
from getpass import getpass
from os import getenv, getpid
from thread import get_ident


#------------------------------------------------------------------------------
# GoLismero modules

from golismero.api.config import Config
from golismero.common import OrchestratorConfig, AuditConfig, \
                             get_profile, get_available_profiles
from golismero.database.auditdb import AuditDB
from golismero.main import launcher
from golismero.main.console import get_terminal_size, colorize, Console
from golismero.main.orchestrator import Orchestrator
from golismero.managers.pluginmanager import PluginManager
from golismero.managers.processmanager import PluginContext


#------------------------------------------------------------------------------
# Custom argparse actions

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        message += "\n\nUse -h or --help to show the full help text."
        return super(CustomArgumentParser, self).error(message)

# --enable-plugin
class EnablePluginAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parsed = [ (True, x.strip()) for x in values.split(",")]
        overrides = getattr(namespace, self.dest, [])
        overrides.extend(parsed)
        setattr(namespace, self.dest, overrides)

# --disable-plugin
class DisablePluginAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        parsed = [ (False, x.strip()) for x in values.split(",")]
        overrides = getattr(namespace, self.dest, [])
        overrides.extend(parsed)
        setattr(namespace, self.dest, overrides)

# --file
class LoadListFromFileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            with open(values, "rU") as f:
                tokens = []
                for line in f:
                    line = line.strip()
                    if not line or line[0] == "#":
                        continue
                    tokens.append(tokens)
        except Exception, e:
            parser.error("Error reading file: %s" % values)
        setattr(namespace, self.dest, tokens)

# --cookie-file
class ReadValueFromFileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            with open(values, "rU") as f:
                data = f.read()
        except IOError, e:
            parser.error("Can't read file %r. Error: %s" % (values, str(e)))
        setattr(namespace, self.dest, data)

# --plugin-arg
class SetPluginArgumentAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest, None)
        if d is None:
            d = []
            setattr(namespace, self.dest, d)
        try:
            plugin_name, token = values.split(":", 1)
            plugin_name = plugin_name.strip()
            key, value  = token.split("=", 1)
            key   = key.strip()
            value = value.strip()
            assert plugin_name
            assert key
            d.append( (plugin_name, key, value) )
        except Exception:
            parser.error("invalid plugin argument: %s" % values)


#------------------------------------------------------------------------------
# Command line parser using argparse

def cmdline_parser():

    # Fix the console width bug in argparse.
    try:
        os.environ["COLUMNS"] = str(get_terminal_size()[0])
    except Exception:
        pass

    parser = CustomArgumentParser(fromfile_prefix_chars="@")
    parser.add_argument("targets", metavar="TARGET", nargs="*", help="one or more target web sites")

    gr_main = parser.add_argument_group("main options")
    gr_main.add_argument("-f", "--file", metavar="FILE", action=LoadListFromFileAction, help="load a list of targets from a plain text file")
    gr_main.add_argument("--config", metavar="FILE", help="global configuration file")
    gr_main.add_argument("-p", "--profile", metavar="NAME", help="profile to use")
    gr_main.add_argument("--profile-list", action="store_true", default=False, help="list available profiles and quit")
    gr_main.add_argument("--ui-mode", metavar="MODE", help="UI mode")
    gr_main.add_argument("-v", "--verbose", action="count", help="increase output verbosity")
    gr_main.add_argument("-q", "--quiet", action="store_const", dest="verbose", const=0, help="suppress text output")
    gr_main.add_argument("--color", action="store_true", default=None, dest="colorize", help="use colors in console output")
    gr_main.add_argument("--no-color", action="store_false", default=None, dest="colorize", help="suppress colors in console output")
##    gr_main.add_argument("--forward-io", metavar="ADDRESS:PORT", help="forward all input and output to the given TCP address and port")

    gr_audit = parser.add_argument_group("audit options")
    gr_audit.add_argument("--audit-name", metavar="NAME", help="customize the audit name")
    gr_audit.add_argument("-db", "--audit-db", metavar="DATABASE", dest="audit_db", help="specify a database connection string")
    gr_audit.add_argument("-nd", "--no-db", dest="audit_db", action="store_const", const="memory://", help="do not store the results in a database")
    gr_audit.add_argument("-i", "--input", dest="imports", metavar="FILENAME", action="append", help="read results from external tools right before the audit")
    gr_audit.add_argument("-ni", "--no-input", dest="disable_importing", action="store_true", default=False, help="do not read results from external tools")

    gr_report = parser.add_argument_group("report options")
    gr_report.add_argument("-o", "--output", dest="reports", metavar="FILENAME", action="append", help="write the results of the audit to this file (use - for stdout)")
    gr_report.add_argument("-no", "--no-output", dest="disable_reporting", action="store_true", default=False, help="do not output the results")
    gr_report.add_argument("--only-vulns", action="store_true", default=None, dest="only_vulns", help="display only the vulnerabilities, instead of all the resources found")

    gr_net = parser.add_argument_group("network options")
    gr_net.add_argument("--max-connections", help="maximum number of concurrent connections per host")
    gr_net.add_argument("--allow-subdomains", action="store_true", default=None, dest="include_subdomains", help="include subdomains in the target scope")
    gr_net.add_argument("--forbid-subdomains", action="store_false", default=None, dest="include_subdomains", help="do not include subdomains in the target scope")
    gr_net.add_argument("--subdomain-regex", metavar="REGEX", help="filter subdomains using a regular expression")
    gr_net.add_argument("-r", "--depth", help="maximum spidering depth (use \"infinite\" for no limit)")
    gr_net.add_argument("-l", "--max-links", type=int, default=None, help="maximum number of links to analyze (0 => infinite)")
    gr_net.add_argument("--follow-redirects", action="store_true", default=None, dest="follow_redirects", help="follow redirects")
    gr_net.add_argument("--no-follow-redirects", action="store_false", default=None, dest="follow_redirects", help="do not follow redirects")
    gr_net.add_argument("--follow-first", action="store_true", default=None, dest="follow_first_redirect", help="always follow a redirection on the target URL itself")
    gr_net.add_argument("--no-follow-first", action="store_false", default=None, dest="follow_first_redirect", help="don't treat a redirection on a target URL as a special case")
    gr_net.add_argument("-pu","--proxy-user", metavar="USER", help="HTTP proxy username")
    gr_net.add_argument("-pp","--proxy-pass", metavar="PASS", help="HTTP proxy password")
    gr_net.add_argument("-pa","--proxy-addr", metavar="ADDRESS:PORT", help="HTTP proxy address in format: address:port")
    gr_net.add_argument("--cookie", metavar="COOKIE", help="set cookie for requests")
    gr_net.add_argument("--cookie-file", metavar="FILE", action=ReadValueFromFileAction, dest="cookie", help="load a cookie from file")
    gr_net.add_argument("--persistent-cache", action="store_true", dest="use_cache_db", default=True, help="use a persistent network cache [default]")
    gr_net.add_argument("--volatile-cache", action="store_false", dest="use_cache_db", help="use a volatile network cache")

    gr_plugins = parser.add_argument_group("plugin options")
    gr_plugins.add_argument("-a", "--plugin-arg", metavar="PLUGIN:KEY=VALUE", action=SetPluginArgumentAction, dest="plugin_args", help="pass an argument to a plugin")
    gr_plugins.add_argument("-e", "--enable-plugin", metavar="NAME", action=EnablePluginAction, default=[], dest="plugin_load_overrides", help="enable a plugin")
    gr_plugins.add_argument("-d", "--disable-plugin", metavar="NAME", action=DisablePluginAction, dest="plugin_load_overrides", help="disable a plugin")
    gr_plugins.add_argument("--max-process", metavar="N", type=int, default=None, help="maximum number of plugins to run concurrently")
    gr_plugins.add_argument("--plugins-folder", metavar="PATH", help="customize the location of the plugins" )
    gr_plugins.add_argument("--plugin-list", action="store_true", default=False, help="list available plugins and quit")
    gr_plugins.add_argument("--plugin-info", metavar="NAME", dest="plugin_name", help="show plugin info and quit")

    return parser


#------------------------------------------------------------------------------
# Start of program

def main():

    # Show the program banner.
    show_banner()

    # Get the command line parser.
    parser = cmdline_parser()

    # Parse the command line options.
    try:
        args = sys.argv[1:]
        envcfg = getenv("GOLISMERO_SETTINGS")
        if envcfg:
            args = parser.convert_arg_line_to_args(envcfg) + args
        P = parser.parse_args(args)

        # Load the Orchestrator options.
        cmdParams = OrchestratorConfig()
        if P.config:
            cmdParams.config_file = path.abspath(P.config)
            if not path.isfile(cmdParams.config_file):
                raise ValueError("File not found: %r" % cmdParams.config_file)
        if cmdParams.config_file:
            cmdParams.from_config_file(cmdParams.config_file, allow_profile = True)
        if P.profile:
            cmdParams.profile = P.profile
            cmdParams.profile_file = get_profile(cmdParams.profile)
        if cmdParams.profile_file:
            cmdParams.from_config_file(cmdParams.profile_file)
        cmdParams.from_object(P)
        cmdParams.plugin_load_overrides = P.plugin_load_overrides

        # Load the target audit options.
        auditParams = AuditConfig()
        auditParams.profile = cmdParams.profile
        auditParams.profile_file = cmdParams.profile_file
        auditParams.config_file = cmdParams.config_file
        if auditParams.config_file:
            auditParams.from_config_file(auditParams.config_file)
        if auditParams.profile_file:
            auditParams.from_config_file(auditParams.profile_file)
        auditParams.from_object(P)
        auditParams.plugin_load_overrides = P.plugin_load_overrides

        # If importing is turned off, remove the list of imports.
        if P.disable_importing:
            auditParams.imports = []

        # If reports are turned off, remove the list of reports.
        # Otherwise, if no reports are specified, default to screen report.
        if P.disable_reporting:
            auditParams.reports = []
        elif not auditParams.reports:
            auditParams.reports = ["-"]

        # If there are no targets but there's a database,
        # get the targets (scope) from the database.
        if not auditParams.targets and auditParams.audit_db:
            try:
                cfg = AuditDB.get_config_from_closed_database(
                    auditParams.audit_db, auditParams.audit_name)
                if cfg:
                    auditParams.targets = cfg.targets
                    auditParams.include_subdomains = cfg.include_subdomains
                    if cmdParams.verbose > 1:
                        if auditParams.targets:
                            print "Found the following targets in the database:"
                            for t in auditParams.targets:
                                print "--> " + t
                            print
            except Exception:
                pass
                ##raise    # XXX DEBUG

    # Show exceptions as command line parsing errors.
    except Exception, e:
        ##raise    # XXX DEBUG
        parser.error(str(e))

    # Get the plugins folder from the parameters.
    # If no plugins folder is given, use the default.
    plugins_folder = cmdParams.plugins_folder
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
                parser.error("Default plugins folder not found, aborting!")
        cmdParams.plugins_folder = plugins_folder


    #--------------------------------------------------------------------------
    # List plugins and quit.

    if P.plugin_list:
        Console.use_colors = cmdParams.colorize

        # Load the plugins list
        try:
            manager = PluginManager()
            manager.find_plugins(cmdParams)
        except Exception, e:
            print "[!] Error loading plugins list: %s" % str(e)
            exit(1)

        # Show the list of plugins.
        print colorize("-------------", "red")
        print colorize(" Plugin list",  "red")
        print colorize("-------------", "red")

        # Import plugins...
        import_plugins = manager.get_plugins("import")
        if import_plugins:
            print
            print colorize("-= Import plugins =-", "yellow")
            for name in sorted(import_plugins.keys()):
                info = import_plugins[name]
                print "\n%s:\n    %s" % (colorize(name[7:], "cyan"), info.description)

        # Testing plugins...
        testing_plugins = manager.get_plugins("testing")
        if testing_plugins:
            names = sorted(testing_plugins.keys())
            names = [x[8:] for x in names]
            stages = [ (v,k) for (k,v) in manager.STAGES.iteritems() ]
            stages.sort()
            for _, stage in stages:
                s = stage + "/"
                p = len(s)
                slice = [x[p:] for x in names if x.startswith(s)]
                if slice:
                    print
                    print colorize("-= %s plugins =-" % stage.title(), "yellow")
                    for name in slice:
                        info = testing_plugins["testing/%s/%s" % (stage, name)]
                        desc = info.description.strip()
                        desc = desc.replace("\n", "\n    ")
                        print "\n%s:\n    %s" % (colorize(name, "cyan"), desc)

        # Report plugins...
        report_plugins = manager.get_plugins("report")
        if report_plugins:
            print
            print colorize("-= Report plugins =-", "yellow")
            for name in sorted(report_plugins.keys()):
                info = report_plugins[name]
                desc = info.description.strip()
                desc = desc.replace("\n", "\n    ")
                print "\n%s:\n    %s" % (colorize(name[7:], "cyan"), desc)

        # UI plugins...
        ui_plugins = manager.get_plugins("ui")
        if ui_plugins:
            print
            print colorize("-= UI plugins =-", "yellow")
            for name in sorted(ui_plugins.keys()):
                info = ui_plugins[name]
                desc = info.description.strip()
                desc = desc.replace("\n", "\n    ")
                print "\n%s:\n    %s" % (colorize(name[3:], "cyan"), desc)

        if path.sep == "/":
            print
        exit(0)


    #--------------------------------------------------------------------------
    # Display plugin info and quit.

    if P.plugin_name:
        Console.use_colors = cmdParams.colorize

        # Load the plugins list.
        try:
            manager = PluginManager()
            manager.find_plugins(cmdParams)
        except Exception, e:
            print "[!] Error loading plugins list: %s" % str(e)
            exit(1)

        # Show the plugin information.
        try:
            try:
                m_plugin_info = manager.get_plugin_by_name(P.plugin_name)
            except KeyError:
                try:
                    m_found = manager.search_plugins(P.plugin_name)
                    if len(m_found) > 1:
                        print "[!] Error: which plugin did you mean?"
                        for plugin_name in m_found.iterkeys():
                            print "\t%s" % plugin_name
                        exit(1)
                    m_plugin_info = m_found.pop(m_found.keys()[0])
                except Exception:
                    raise KeyError(P.plugin_name)
            Config._context = PluginContext( orchestrator_pid = getpid(),
                                             orchestrator_tid = get_ident(),
                                                  plugin_info = m_plugin_info,
                                                    msg_queue = None )
            m_plugin_obj = manager.load_plugin_by_name(m_plugin_info.plugin_name)
            m_root = cmdParams.plugins_folder
            m_root = path.abspath(m_root)
            if not m_root.endswith(path.sep):
                m_root += path.sep
            m_location = m_plugin_info.descriptor_file[len(m_root):]
            a, b = path.split(m_location)
            b = colorize(b, "cyan")
            m_location = path.join(a, b)
            m_src = m_plugin_info.plugin_module[len(m_root):]
            a, b = path.split(m_src)
            b = colorize(b, "cyan")
            m_src = path.join(a, b)
            m_name = m_plugin_info.plugin_name
            p = m_name.rfind("/") + 1
            m_name = m_name[:p] + colorize(m_name[p:], "cyan")
            m_desc = m_plugin_info.description.strip()
            m_desc = m_desc.replace("\n", "\n    ")
            print "Information for plugin: %s" % colorize(m_plugin_info.display_name, "yellow")
            print "-" * len("Information for plugin: %s" % m_plugin_info.display_name)
            print "%s          %s" % (colorize("ID:", "green"), m_name)
            print "%s    %s" % (colorize("Location:", "green"), m_location)
            print "%s %s" % (colorize("Source code:", "green"), m_src)
            if m_plugin_info.plugin_class:
                print "%s  %s" % (colorize("Class name:", "green"), colorize(m_plugin_info.plugin_class, "cyan"))
            print "%s    %s" % (colorize("Category:", "green"), m_plugin_info.category)
            print "%s       %s" % (colorize("Stage:", "green"), m_plugin_info.stage)
            if m_plugin_info.description != m_plugin_info.display_name:
                print
                print "%s\n    %s" % (colorize("Description:", "green"), m_desc)
            if m_plugin_info.plugin_args:
                print
                print colorize("Arguments:", "green")
                for name, default in sorted(m_plugin_info.plugin_args.items()):
                    if name in m_plugin_info.plugin_passwd_args:
                        default = "****************"
                    print "\t%s -> %s" % (colorize(name, "cyan"), default)
        except KeyError:
            print "[!] Plugin name not found"
            exit(1)
        except ValueError:
            print "[!] Plugin name not found"
            exit(1)
        except Exception, e:
            print "[!] Error recovering plugin info: %s" % str(e)
            exit(1)

        if path.sep == "/":
            print
        exit(0)


    #--------------------------------------------------------------------------
    # List profiles and quit.

    if P.profile_list:
        Console.use_colors = cmdParams.colorize
        profiles = sorted(get_available_profiles())
        if not profiles:
            print "No available profiles!"
        else:
            print "-------------------"
            print " Available profiles"
            print "-------------------"
            print
            for name in profiles:
                try:
                    p = RawConfigParser()
                    p.read(get_profile(name))
                    desc = p.get("golismero", "description")
                except Exception:
                    desc = None
                if desc:
                    print "+ %s: %s" % (name, desc)
                else:
                    print "+ %s" % name

        if path.sep == "/":
            print
        exit(0)


    #--------------------------------------------------------------------------
    # Check if all options are correct.

    try:
        cmdParams.check_params()
        if auditParams.targets:
            auditParams.check_params()
    except Exception, e:
        ##raise # XXX DEBUG
        parser.error(str(e))

    try:

        # Load the plugins.
        # XXX FIXME for this we'd need the plugin manager
        # to be a singleton again, so we don't actually do
        # this twice - however the audit plugin managers
        # can't be singletons.
        manager = PluginManager()
        manager.find_plugins(cmdParams)

        # Sanitize the plugin arguments.
        try:
            if P.plugin_args:
                plugin_args = manager.parse_plugin_args(P.plugin_args)
            else:
                plugin_args = {}
        except KeyError, e:
            parser.error(str(e))

        # Prompt for passwords.
        for plugin_name in plugin_args.keys():
            plugin_info = manager.get_plugin_by_name(plugin_name)
            target_args = plugin_args[plugin_name]
            for key, value in target_args.items():
                if not value and key in plugin_info.plugin_passwd_args:
                    if len(plugin_info.plugin_passwd_args) > 1:
                        msg = "Enter password for %s (%s): "
                        msg %= (plugin_info.display_name, key)
                    else:
                        msg = "Enter password for %s: "
                        msg %= plugin_info.display_name
                    target_args[key] = getpass(msg)

        # Save the plugin arguments for the Orchestrator and the Audit.
        cmdParams.plugin_args = plugin_args
        if auditParams.targets:
            auditParams.plugin_args = plugin_args

        # Set the plugin arguments before loading the UI plugin.
        for plugin_name, plugin_args in cmdParams.plugin_args.iteritems():
            status = manager.set_plugin_args(plugin_name, plugin_args)
            if status != 0:     # should never happen, but just in case...
                if status == 1:
                    msg = "Unknown plugin: %s"
                elif status == 2:
                    msg = "Invalid arguments for plugin: %s"
                else:
                    msg = "Error setting arguments for plugin: %s"
                parser.error(msg % plugin_name)

        # Load the UI plugin.
        ui_plugin_name = "ui/" + cmdParams.ui_mode
        ui_plugin = manager.load_plugin_by_name(ui_plugin_name)

    # Show an error message if something goes wrong.
    except Exception, e:
        ##raise  # XXX DEBUG
        parser.error("error loading plugins: %s" % str(e))

    # Check the settings with the UI plugin.
    try:
        if auditParams.targets:
            ui_plugin.check_params(cmdParams, auditParams)
        else:
            ui_plugin.check_params(cmdParams)
    except Exception, e:
        ##raise # XXX DEBUG
        msg = str(e)
        if not msg:
            msg = "configuration error!"
        parser.error(msg)


    #--------------------------------------------------------------------------
    # Launch GoLismero.

    if auditParams.targets:
        launcher.run(cmdParams, auditParams)
    else:
        launcher.run(cmdParams)
    exit(0)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
