#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

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
# Fix the module load path.

import os
from os import path
import sys

script = __file__
if path.islink(script):
    script = path.realpath(script)
here = path.split(path.abspath(script))[0]
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

from ConfigParser import RawConfigParser
from getpass import getpass
from os import getenv, getpid
from thread import get_ident


#------------------------------------------------------------------------------
# GoLismero modules

from golismero.api.config import Config
from golismero.api.external import run_external_tool
from golismero.api.logger import Logger
from golismero.common import OrchestratorConfig, AuditConfig, get_profile, \
     get_available_profiles, get_default_plugins_folder
from golismero.database.auditdb import AuditDB
from golismero.main import launcher
from golismero.main.console import get_terminal_size, colorize, Console
from golismero.main.orchestrator import Orchestrator
from golismero.main.testing import PluginTester
from golismero.managers.pluginmanager import PluginManager
from golismero.managers.processmanager import PluginContext


#------------------------------------------------------------------------------
# Custom argparse actions

class CustomArgumentParser(argparse.ArgumentParser):
    must_show_banner = True
    def error(self, message):
        if self.must_show_banner:
            self.must_show_banner = False
            show_banner()
        self.usage = None
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
            plugin_id, token = values.split(":", 1)
            plugin_id  = plugin_id.strip()
            key, value = token.split("=", 1)
            key   = key.strip()
            value = value.strip()
            assert plugin_id
            assert key
            d.append( (plugin_id, key, value) )
        except Exception:
            parser.error("invalid plugin argument: %s" % values)


#------------------------------------------------------------------------------
# Command line parser using argparse

COMMANDS = (

    # Scanning.
    "SCAN",
    "REPORT",
    "IMPORT",

    # Information.
    "PROFILES",
    "PLUGINS",
    "INFO",

    # Management.
    "DUMP",
    "UPDATE",
)

def cmdline_parser():

    # Fix the console width bug in argparse.
    try:
        os.environ["COLUMNS"] = str(get_terminal_size()[0])
    except Exception:
        pass

    # Use Bash autocompletion when available.
    try:
        from argcomplete import autocomplete
        from argcomplete.completers import ChoicesCompleter, FilesCompleter
        autocomplete_enabled = True
    except ImportError:
        autocomplete_enabled = False

    if autocomplete_enabled:
        def profiles_completer(prefix, **kwargs):
            return (v for v in get_available_profiles() if v.startswith(prefix))
        def plugins_completer(prefix, **kwargs):
            if ":" in prefix:
                return (prefix,)
            names = []
            base = get_default_plugins_folder()
            for cat in PluginManager.CATEGORIES:
                for (_, _, filenames) in os.walk(path.join(base, cat)):
                    for filename in filenames:
                        if filename.startswith(prefix):
                            name, ext = path.splitext(filename)
                            if ext.lower() == ".golismero":
                                names.append(name)
            return names

    parser = CustomArgumentParser(fromfile_prefix_chars="@")

    cmd = parser.add_argument("command", metavar="COMMAND", help="action to perform")
    if autocomplete_enabled:
        cmd.completer = ChoicesCompleter(COMMANDS + tuple(x.lower() for x in COMMANDS))
    parser.add_argument("targets", metavar="TARGET", nargs="*", help="zero or more arguments, meaning depends on command")

    gr_main = parser.add_argument_group("main options")
    cmd = gr_main.add_argument("-f", "--file", metavar="FILE", action=LoadListFromFileAction, help="load a list of targets from a plain text file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=False)
    cmd = gr_main.add_argument("--config", metavar="FILE", help="global configuration file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".conf",), directories=False)
    cmd = gr_main.add_argument("-p", "--profile", metavar="NAME", help="profile to use")
    if autocomplete_enabled:
        cmd.completer = profiles_completer
    cmd = gr_main.add_argument("--ui-mode", metavar="MODE", help="UI mode")
    if autocomplete_enabled:
        cmd.completer = ChoicesCompleter(("console", "disabled")) ##, "web"))
    gr_main.add_argument("-v", "--verbose", action="count", help="increase output verbosity")
    gr_main.add_argument("-q", "--quiet", action="store_const", dest="verbose", const=0, help="suppress text output")
    gr_main.add_argument("--color", action="store_true", default=None, dest="color", help="use colors in console output")
    gr_main.add_argument("--no-color", action="store_false", default=None, dest="color", help="suppress colors in console output")

    gr_audit = parser.add_argument_group("audit options")
    gr_audit.add_argument("--audit-name", metavar="NAME", help="customize the audit name")
    cmd = gr_audit.add_argument("-db", "--audit-db", metavar="DATABASE", dest="audit_db", help="specify a database connection string")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".db",), directories=False)
    gr_audit.add_argument("-nd", "--no-db", dest="audit_db", action="store_const", const="memory://", help="do not store the results in a database")
    cmd = gr_audit.add_argument("-i", "--input", dest="imports", metavar="FILENAME", action="append", help="read results from external tools right before the audit")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".csv", ".xml"), directories=False)
    gr_audit.add_argument("-ni", "--no-input", dest="disable_importing", action="store_true", default=False, help="do not read results from external tools")
    gr_report = parser.add_argument_group("report options")
    cmd = gr_report.add_argument("-o", "--output", dest="reports", metavar="FILENAME", action="append", help="write the results of the audit to this file (use - for stdout)")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".html", ".rst", ".txt"), directories=False)
    gr_report.add_argument("-no", "--no-output", dest="disable_reporting", action="store_true", default=False, help="do not output the results")
    gr_report.add_argument("--full", action="store_false", default=None, dest="only_vulns", help="produce fully detailed reports")
    gr_report.add_argument("--brief", action="store_true", dest="only_vulns", help="report only the highlights")

    gr_net = parser.add_argument_group("network options")
    gr_net.add_argument("--max-connections", help="maximum number of concurrent connections per host")
    gr_net.add_argument("--allow-subdomains", action="store_true", default=None, dest="include_subdomains", help="include subdomains in the target scope")
    gr_net.add_argument("--forbid-subdomains", action="store_false", default=None, dest="include_subdomains", help="do not include subdomains in the target scope")
    ##gr_net.add_argument("--subdomain-regex", metavar="REGEX", help="filter subdomains using a regular expression")
    cmd = gr_net.add_argument("-r", "--depth", help="maximum spidering depth (use \"infinite\" for no limit)")
    if autocomplete_enabled:
        cmd.completer = ChoicesCompleter(("infinite",))
    gr_net.add_argument("-l", "--max-links", type=int, default=None, help="maximum number of links to analyze (0 => infinite)")
    gr_net.add_argument("--follow-redirects", action="store_true", default=None, dest="follow_redirects", help="follow redirects")
    gr_net.add_argument("--no-follow-redirects", action="store_false", default=None, dest="follow_redirects", help="do not follow redirects")
    gr_net.add_argument("--follow-first", action="store_true", default=None, dest="follow_first_redirect", help="always follow a redirection on the target URL itself")
    gr_net.add_argument("--no-follow-first", action="store_false", default=None, dest="follow_first_redirect", help="don't treat a redirection on a target URL as a special case")
    gr_net.add_argument("-pu","--proxy-user", metavar="USER", help="HTTP proxy username")
    gr_net.add_argument("-pp","--proxy-pass", metavar="PASS", help="HTTP proxy password")
    gr_net.add_argument("-pa","--proxy-addr", metavar="ADDRESS:PORT", help="HTTP proxy address in format: address:port")
    gr_net.add_argument("--cookie", metavar="COOKIE", help="set cookie for requests")
    cmd = gr_net.add_argument("--cookie-file", metavar="FILE", action=ReadValueFromFileAction, dest="cookie", help="load a cookie from file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=False)
    gr_net.add_argument("--persistent-cache", action="store_true", dest="use_cache_db", default=True, help="use a persistent network cache [default]")
    gr_net.add_argument("--volatile-cache", action="store_false", dest="use_cache_db", help="use a volatile network cache")

    gr_plugins = parser.add_argument_group("plugin options")
    cmd = gr_plugins.add_argument("-a", "--plugin-arg", metavar="PLUGIN:KEY=VALUE", action=SetPluginArgumentAction, dest="plugin_args", help="pass an argument to a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    cmd = gr_plugins.add_argument("-e", "--enable-plugin", metavar="PLUGIN", action=EnablePluginAction, default=[], dest="plugin_load_overrides", help="enable a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    cmd = gr_plugins.add_argument("-d", "--disable-plugin", metavar="PLUGIN", action=DisablePluginAction, dest="plugin_load_overrides", help="disable a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    gr_plugins.add_argument("--max-concurrent", metavar="N", type=int, default=None, help="maximum number of plugins to run concurrently")
    cmd = gr_plugins.add_argument("--plugins-folder", metavar="PATH", help="customize the location of the plugins" )
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=True)

    if autocomplete_enabled:
        autocomplete(parser)

    parser.usage = parser.format_usage()[7:] + (
        ################################################################################
        "\n"
        "available commands:\n"
        "\n"
        "  SCAN:\n"
        "    Perform a vulnerability scan on the given targets. Optionally import\n"
        "    results from other tools and write a report. The arguments that follow may\n"
        "    be domain names, IP addresses or web pages.\n"
        "\n"
        "  PROFILES:\n"
        "    Show a list of available config profiles. This command takes no arguments.\n"
        "\n"
        "  PLUGINS:\n"
        "    Show a list of available plugins. This command takes no arguments.\n"
        "\n"
        "  INFO:\n"
        "    Show detailed information on a given plugin. The arguments that follow are\n"
        "    the plugin IDs. You can use glob-style wildcards.\n"
        "\n"
        "  REPORT:\n"
        "    Write a report from an earlier scan. This command takes no arguments.\n"
        "    To specify output files use the -o switch.\n"
        "\n"
        "  IMPORT:\n"
        "    Import results from other tools and optionally write a report, but don't\n"
        "    scan the targets. This command takes no arguments. To specify input files\n"
        "    use the -i switch.\n"
        "\n"
        "  DUMP:\n"
        "    Dump the database from an earlier scan in SQL format. This command takes no\n"
        "    arguments. To specify output files use the -o switch.\n"
        "\n"
        "  UPDATE:\n"
        "    Update GoLismero to the latest version. Requires Git to be installed and\n"
        "    available in the PATH. This command takes no arguments.\n"
        "\n"
        "examples:\n"
        "\n"
        "  scan a website and show the results on screen:\n"
        "    %(prog)s scan http://www.example.com\n"
        "\n"
        "  grab Nmap results, scan all hosts found and write an HTML report:\n"
        "    %(prog)s scan -i nmap_output.xml -o report.html\n"
        "\n"
        "  grab results from OpenVAS and show them on screen, but don't scan anything:\n"
        "    %(prog)s import -i openvas_output.xml\n"
        "\n"
        "  show a list of all available configuration profiles:\n"
        "    %(prog)s profiles\n"
        "\n"
        "  show a list of all available plugins:\n"
        "    %(prog)s plugins\n"
        "\n"
        "  show information on all bruteforcer plugins:\n"
        "    %(prog)s info brute_*\n"
        "\n"
        "  dump the database from a previous scan:\n"
        "    %(prog)s dump -db example.db -o dump.sql\n"
        "\n"
        ################################################################################
    )

    return parser


#------------------------------------------------------------------------------
# Start of program

def main():

    # Get the command line parser.
    parser = cmdline_parser()

    # Parse the command line options.
    try:
        args = sys.argv[1:]
        envcfg = getenv("GOLISMERO_SETTINGS")
        if envcfg:
            args = parser.convert_arg_line_to_args(envcfg) + args
        P = parser.parse_args(args)
        command = P.command.upper()
        if command in COMMANDS:
            P.command = command
        else:
            P.targets.insert(0, P.command)
            P.command = "SCAN"

        # Load the Orchestrator options.
        cmdParams = OrchestratorConfig()
        cmdParams.command = P.command
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

        # Enable console colors if requested.
        Console.use_colors = cmdParams.color

        # Show the program banner.
        parser.must_show_banner = False
        if cmdParams.verbose:
            show_banner()

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
        elif not auditParams.reports and P.command in ("SCAN", "REPORT"):
            auditParams.reports = ["-"]
            if auditParams.only_vulns is None:
                auditParams.only_vulns = True

    # Show exceptions as command line parsing errors.
    except Exception, e:
        ##raise    # XXX DEBUG
        parser.error(str(e))

    # Get the plugins folder from the parameters.
    # If no plugins folder is given, use the default.
    plugins_folder = cmdParams.plugins_folder
    if not plugins_folder:
        plugins_folder = path.abspath(script)
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

    if P.command == "PLUGINS":

        # Fail if we have arguments.
        if P.targets:
            parser.error("too many arguments")

        # Load the plugins list.
        try:
            manager = PluginManager()
            manager.find_plugins(cmdParams)
        except Exception, e:
            parser.error("error loading plugins list: %s" % str(e))

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

    if P.command == "INFO":

        # Fail if we don't have arguments.
        if not P.targets:
            parser.error("too few arguments")

        # Load the plugins list.
        try:
            manager = PluginManager()
            manager.find_plugins(cmdParams)
        except Exception, e:
            parser.error("error loading plugins list: %s" % str(e))

        # Show the plugin information.
        try:
            to_print = []
            plugin_infos = []
            for plugin_id in P.targets:
                m_found = manager.search_plugins_by_mask(plugin_id)
                plugin_infos.extend( m_found.values() )
            if not plugin_infos:
                raise KeyError()
            for m_plugin_info in plugin_infos:
                Config._context = PluginContext( orchestrator_pid = getpid(),
                                                 orchestrator_tid = get_ident(),
                                                      plugin_info = m_plugin_info,
                                                        msg_queue = None )
                m_plugin_obj = manager.load_plugin_by_id(m_plugin_info.plugin_id)
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
                m_name = m_plugin_info.plugin_id
                p = m_name.rfind("/") + 1
                m_name = m_name[:p] + colorize(m_name[p:], "cyan")
                m_desc = m_plugin_info.description.strip()
                m_desc = m_desc.replace("\n", "\n    ")
                to_print.append("")
                to_print.append("Information for plugin: %s" % colorize(m_plugin_info.display_name, "yellow"))
                to_print.append("-" * len("Information for plugin: %s" % m_plugin_info.display_name))
                to_print.append("%s          %s" % (colorize("ID:", "green"), m_name))
                to_print.append("%s    %s" % (colorize("Location:", "green"), m_location))
                to_print.append("%s %s" % (colorize("Source code:", "green"), m_src))
                if m_plugin_info.plugin_class:
                    to_print.append("%s  %s" % (colorize("Class name:", "green"), colorize(m_plugin_info.plugin_class, "cyan")))
                to_print.append("%s    %s" % (colorize("Category:", "green"), m_plugin_info.category))
                to_print.append("%s       %s" % (colorize("Stage:", "green"), m_plugin_info.stage))
                if m_plugin_info.description != m_plugin_info.display_name:
                    to_print.append("")
                    to_print.append("%s\n    %s" % (colorize("Description:", "green"), m_desc))
                if m_plugin_info.plugin_args:
                    to_print.append("")
                    to_print.append(colorize("Arguments:", "green"))
                    for name, default in sorted(m_plugin_info.plugin_args.items()):
                        if name in m_plugin_info.plugin_passwd_args:
                            default = "****************"
                        to_print.append("\t%s -> %s" % (colorize(name, "cyan"), default))
                to_print.append("")
        except KeyError:
            ##raise # XXX DEBUG
            parser.error("plugin ID not found")
        except ValueError:
            ##raise # XXX DEBUG
            parser.error("plugin ID not found")
        except Exception, e:
            ##raise # XXX DEBUG
            parser.error("error recovering plugin info: %s" % str(e))

        for line in to_print:
            print line
        exit(0)


    #--------------------------------------------------------------------------
    # List profiles and quit.

    if P.command == "PROFILES":
        if P.targets:
            parser.error("too many arguments")
        profiles = sorted(get_available_profiles())
        if not profiles:
            print "No available profiles!"
        else:
            print "--------------------"
            print " " + colorize("Available profiles", "yellow")
            print "--------------------"
            print
            for name in profiles:
                try:
                    p = RawConfigParser()
                    p.read(get_profile(name))
                    desc = p.get("golismero", "description")
                except Exception:
                    desc = None
                if desc:
                    print "+ %s: %s" % (colorize(name, "cyan"), desc)
                else:
                    print "+ %s" % colorize(name, "cyan")

        if path.sep == "/":
            print
        exit(0)


    #--------------------------------------------------------------------------
    # Dump the database and quit.

    if P.command == "DUMP":
        if auditParams.is_new_audit():
            parser.error("missing audit database")
        if not P.reports:
            parser.error("missing output filename")
        if P.verbose != 0:
            print "Loading database: %s" % \
                  colorize(auditParams.audit_db, "yellow")
        with PluginTester(autoinit=False, autodelete=False) as t:
            t.orchestrator_config.verbose = 0
            t.audit_config.audit_name = auditParams.audit_name
            t.audit_config.audit_db   = auditParams.audit_db
            t.init_environment()
            Console.use_colors = cmdParams.color
            for filename in P.reports:
                if P.verbose != 0:
                    print "Dumping to file: %s" % colorize(filename, "cyan")
                t.audit.database.dump(filename)
        exit(0)


    #--------------------------------------------------------------------------
    # Update GoLismero and quit.

    if P.command == "UPDATE":

        # Fail if we got any arguments.
        if P.targets:
            parser.error("too many arguments")

        # Setup a dummy environment so we can call the API.
        with PluginTester(autoinit=False) as t:
            t.orchestrator_config.ui_mode = "console"
            t.orchestrator_config.verbose = cmdParams.verbose
            t.orchestrator_config.color   = cmdParams.color
            t.init_environment(mock_audit=False)

            # Run Git here to download the latest version.
            if cmdParams.verbose:
                Logger.log("Updating GoLismero...")
            run_external_tool("git", ["pull"], cwd = here,
                callback = Logger.log if cmdParams.verbose else lambda x: x)

            # Update the NIST CPE database.
            if cmdParams.verbose:
                Logger.log("Updating NIST CPE database...")
            t.orchestrator.cpedb.update()
            t.orchestrator.cpedb.vacuum()

            # Done!
            Logger.log("Update complete.")
            exit(0)


    #--------------------------------------------------------------------------
    # Check if all options are correct.

    if P.command != "SCAN":
        auditParams.plugin_load_overrides.append( (False, "testing") )

    guessed_urls = []
    for target in auditParams.targets:
        if not "://" in target:
            guessed_urls.append("http://" + target)
    auditParams.targets.extend(guessed_urls)

    try:
        cmdParams.check_params()
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
        for plugin_id in plugin_args.keys():
            plugin_info = manager.get_plugin_by_id(plugin_id)
            target_args = plugin_args[plugin_id]
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
        cmdParams.plugin_args   = plugin_args
        auditParams.plugin_args = plugin_args

        # Set the plugin arguments before loading the UI plugin.
        for plugin_id, plugin_args in cmdParams.plugin_args.iteritems():
            status = manager.set_plugin_args(plugin_id, plugin_args)
            if status != 0:     # should never happen, but just in case...
                if status == 1:
                    msg = "Unknown plugin: %s"
                elif status == 2:
                    msg = "Invalid arguments for plugin: %s"
                else:
                    msg = "Error setting arguments for plugin: %s"
                parser.error(msg % plugin_id)

        # Load the UI plugin.
        ui_plugin_id = "ui/" + cmdParams.ui_mode
        ui_plugin = manager.load_plugin_by_id(ui_plugin_id)

    # Show an error message if something goes wrong.
    except Exception, e:
        ##raise  # XXX DEBUG
        parser.error("error loading plugins: %s" % str(e))

    # Check the settings with the UI plugin.
    try:
        ui_plugin.check_params(cmdParams, auditParams)
    except Exception, e:
        ##raise # XXX DEBUG
        msg = str(e)
        if not msg:
            msg = "configuration error!"
        parser.error(msg)


    #--------------------------------------------------------------------------
    # Launch GoLismero.

    launcher.run(cmdParams, auditParams)
    exit(0)


#------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
