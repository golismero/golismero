#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

__license__="""
GoLismero 2.0 - The web knife.

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

__all__ = []


#------------------------------------------------------------------------------
# Fix the module load path.

import sys
from os import path

script = __file__
if path.islink(script):
    script = path.realpath(script)
here = path.split(path.abspath(script))[0]
assert here
thirdparty_libs = path.join(here, "thirdparty_libs")
assert path.exists(thirdparty_libs)
has_here = here in sys.path
has_thirdparty_libs = thirdparty_libs in sys.path
if not (has_here and has_thirdparty_libs):
    if has_here:
        sys.path.remove(here)
    if has_thirdparty_libs:
        sys.path.remove(thirdparty_libs)
    sys.path.insert(0, thirdparty_libs)
    sys.path.insert(0, here)


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

    # In OS X, python versions lower than 2.7.6 fails
    import platform
    if (
        platform.system() == "Darwin" and
        (version_info < (2,7,6) or version_info >= (3,0))
    ):
        show_banner()
        print (
            "[!] OS X can experiment some problems with Python versions lower than 2.7.6. It's recommended to upgrade"
            " http://www.python.org/download/releases/2.7.6/"
        )


#------------------------------------------------------------------------------
# Imported modules

import argparse
import os
import sys

from ConfigParser import RawConfigParser
from getpass import getpass
from glob import glob
from os import getenv, getpid
from thread import get_ident
from traceback import format_exc

# Hack to disable logging in SnakeMQ.
import snakemq
if path.sep == "\\":
    snakemq.init_logging(open("nul", "w"))
else:
    snakemq.init_logging(open("/dev/null", "w"))


#------------------------------------------------------------------------------
# GoLismero modules

from golismero.api.config import Config
from golismero.api.external import run_external_tool
from golismero.api.logger import Logger
from golismero.api.plugin import CATEGORIES, STAGES
from golismero.common import OrchestratorConfig, AuditConfig, get_profile, \
     get_available_profiles, get_default_plugins_folder
from golismero.main import launcher
from golismero.main.console import get_terminal_size, colorize, Console
from golismero.main.testing import PluginTester
from golismero.managers.pluginmanager import PluginManager
from golismero.managers.processmanager import PluginContext


#------------------------------------------------------------------------------
# Custom argparse actions

class ArgumentParserWithBanner(argparse.ArgumentParser):
    must_show_banner = True
    def error(self, message):
        if self.must_show_banner:
            self.must_show_banner = False
            show_banner()
        self.usage = None
        message += "\n\nUse -h to see the quick help, or --help to show the full help text."
        return super(ArgumentParserWithBanner, self).error(message)

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
                    tokens.append(line)
        except Exception:
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

# -h
class QuickHelpAction(argparse._HelpAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if parser.must_show_banner:
            parser.must_show_banner = False
            show_banner()
        parser._print_message(parser.quick_help)
        parser.exit()


#------------------------------------------------------------------------------
# Command line parser using argparse.

COMMANDS = (

    # Scanning.
    "SCAN",
    "RESCAN",
    "REPORT",
    "IMPORT",

    # Information.
    "PROFILES",
    "PLUGINS",
    "INFO",

    # Management.
    "LOAD",
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
            return [
                v for v in get_available_profiles()
                  if v.startswith(prefix)
            ]
        def plugins_completer(prefix, **kwargs):
            if ":" in prefix:
                return [prefix,]
            names = []
            base = get_default_plugins_folder()
            for cat in CATEGORIES:
                for (_, _, filenames) in os.walk(path.join(base, cat)):
                    for filename in filenames:
                        if filename.startswith(prefix):
                            name, ext = path.splitext(filename)
                            if ext.lower() == ".golismero":
                                names.append(name)
            return names

    parser = ArgumentParserWithBanner(fromfile_prefix_chars="@", add_help=False)

    cmd = parser.add_argument("command", metavar="COMMAND", help="action to perform")
    if autocomplete_enabled:
        cmd.completer = ChoicesCompleter(COMMANDS + tuple(x.lower() for x in COMMANDS))
    parser.add_argument("targets", metavar="TARGET", nargs="*", help="zero or more arguments, meaning depends on command")

    parser.add_argument("-h", action=QuickHelpAction, default=argparse.SUPPRESS, help="show this help message and exit")
    parser.add_argument("--help", action='help', default=argparse.SUPPRESS, help="show this help message and exit")

    gr_main = parser.add_argument_group("main options")
    cmd = gr_main.add_argument("-f", "--file", metavar="FILE", dest="targets", action=LoadListFromFileAction, help="load a list of targets from a plain text file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=False)
    cmd = gr_main.add_argument("--config", metavar="FILE", help="global configuration file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".conf",), directories=False)
    cmd = gr_main.add_argument("--user-config", metavar="FILE", help="per-user configuration file")
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
    cmd = gr_audit.add_argument("-db", "--audit-db", metavar="DATABASE", dest="audit_db", help="specify a database filename")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".db",), directories=False)
    gr_audit.add_argument("-nd", "--no-db", dest="audit_db", action="store_const", const=":memory:", help="do not store the results in a database")
    cmd = gr_audit.add_argument("-i", "--input", dest="imports", metavar="FILENAME", action="append", help="read results from external tools right before the audit")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".csv", ".xml", ".nessus"), directories=False)
    gr_audit.add_argument("-ni", "--no-input", dest="disable_importing", action="store_true", default=False, help="do not read results from external tools")
    gr_report = parser.add_argument_group("report options")
    cmd = gr_report.add_argument("-o", "--output", dest="reports", metavar="FILENAME", action="append", help="write the results of the audit to this file (use - for stdout)")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(allowednames=(".html", ".rst", ".txt"), directories=False)
    gr_report.add_argument("-no", "--no-output", dest="disable_reporting", action="store_true", default=False, help="do not output the results")
    gr_report.add_argument("--full", action="store_false", default=None, dest="only_vulns", help="produce fully detailed reports")
    gr_report.add_argument("--brief", action="store_true", dest="only_vulns", help="report only the highlights")

    gr_net = parser.add_argument_group("network options")
    gr_net.add_argument("--allow-subdomains", action="store_true", default=None, dest="include_subdomains", help="include subdomains in the target scope")
    gr_net.add_argument("--forbid-subdomains", action="store_false", default=None, dest="include_subdomains", help="do not include subdomains in the target scope")
    gr_net.add_argument("--parent", action="store_true", default=None, dest="allow_parent", help="include parent folders in the target scope")
    gr_net.add_argument("-np", "--no-parent", action="store_false", default=None, dest="allow_parent", help="do not include parent folders in the target scope")
    cmd = gr_net.add_argument("-r", "--depth", help="maximum spidering depth (use \"infinite\" for no limit)")
    if autocomplete_enabled:
        cmd.completer = ChoicesCompleter(("1", "200", "infinite",))
    gr_net.add_argument("--follow-redirects", action="store_true", default=None, dest="follow_redirects", help="follow redirects")
    gr_net.add_argument("--no-follow-redirects", action="store_false", default=None, dest="follow_redirects", help="do not follow redirects")
    gr_net.add_argument("--follow-first", action="store_true", default=None, dest="follow_first_redirect", help="always follow a redirection on the target URL itself")
    gr_net.add_argument("--no-follow-first", action="store_false", default=None, dest="follow_first_redirect", help="don't treat a redirection on a target URL as a special case")
    gr_net.add_argument("--max-connections", help="maximum number of concurrent connections per host")
    gr_net.add_argument("-l", "--max-links", type=int, default=None, help="maximum number of links to analyze (0 => infinite)")
    gr_net.add_argument("-pu","--proxy-user", metavar="USER", help="HTTP proxy username")
    gr_net.add_argument("-pp","--proxy-pass", metavar="PASS", help="HTTP proxy password")
    gr_net.add_argument("-pa","--proxy-addr", metavar="ADDRESS", help="HTTP proxy address")
    gr_net.add_argument("-pn","--proxy-port", metavar="PORT", help="HTTP proxy port number")
    gr_net.add_argument("--cookie", metavar="COOKIE", help="set cookie for requests")
    gr_net.add_argument("--user-agent", metavar="USER_AGENT", help="set a custom user agent or 'random' value")
    cmd = gr_net.add_argument("--cookie-file", metavar="FILE", action=ReadValueFromFileAction, dest="cookie", help="load a cookie from file")
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=False)
    gr_net.add_argument("--persistent-cache", action="store_true", dest="use_cache_db", default=True, help="use a persistent network cache [default]")
    gr_net.add_argument("--volatile-cache", action="store_false", dest="use_cache_db", help="use a volatile network cache")

    gr_plugins = parser.add_argument_group("plugin options")
    cmd = gr_plugins.add_argument("-a", "--plugin-arg", metavar="PLUGIN:KEY=VALUE", action=SetPluginArgumentAction, dest="raw_plugin_args", help="pass an argument to a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    cmd = gr_plugins.add_argument("-e", "--enable-plugin", metavar="PLUGIN", action=EnablePluginAction, default=[], dest="plugin_load_overrides", help="enable a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    cmd = gr_plugins.add_argument("-d", "--disable-plugin", metavar="PLUGIN", action=DisablePluginAction, dest="plugin_load_overrides", help="disable a plugin")
    if autocomplete_enabled:
        cmd.completer = plugins_completer
    gr_plugins.add_argument("--max-concurrent", metavar="N", type=int, default=None, help="maximum number of plugins to run concurrently")
    gr_plugins.add_argument("--plugin-timeout", metavar="N", type=float, default=None, help="timeout in seconds for the execution of a plugin")
    cmd = gr_plugins.add_argument("--plugins-folder", metavar="PATH", help="customize the location of the plugins" )
    if autocomplete_enabled:
        cmd.completer = FilesCompleter(directories=True)

    if autocomplete_enabled:
        autocomplete(parser)

    quick_help = (
        ################################################################################
        "\n"
        "  SCAN:\n"
        "    Perform a vulnerability scan on the given targets. Optionally import\n"
        "    results from other tools and write a report. The arguments that follow may\n"
        "    be domain names, IP addresses or web pages.\n"
        "\n"
        "  RESCAN:\n"
        "    Same as SCAN, but previously run tests are repeated. If the database is\n"
        "    new, this command is identical to SCAN.\n"
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
        "  LOAD:\n"
        "    Load a database dump from an earlier scan in SQL format. This command takes\n"
        "    no arguments. To specify input files use the -i switch.\n"
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

    parser.usage = parser.format_usage()[7:] + \
                   "\navailable commands:\n" + quick_help
    parser.quick_help = (
        "usage: %(prog)s COMMAND [TARGETS...] [--options]\n" \
        + quick_help) % {"prog": parser.prog}

    return parser


#------------------------------------------------------------------------------
def parse_plugin_args(manager, plugin_args):
    """
    Parse a list of tuples with plugin arguments as a dictionary of
    dictionaries, with plugin IDs sanitized.

    :param manager: Plugin manager.
    :type manager: PluginManager

    :param plugin_args: Arguments as specified in the command line.
    :type plugin_args: list(tuple(str, str, str))

    :returns: Sanitized plugin arguments. Dictionary mapping plugin
        names to dictionaries mapping argument names and values.
    :rtype: dict(str -> dict(str -> str))

    :raises KeyError: Plugin or argument not found.
    """
    parsed = {}
    for plugin_id, key, value in plugin_args:
        plugin_info = manager.guess_plugin_by_id(plugin_id)
        if not plugin_info:
            raise KeyError("Plugin not found: %s" % plugin_id)
        key = key.lower()
        if key not in plugin_info.plugin_args:
            raise KeyError(
                "Argument not found: %s:%s" % (plugin_id, key))
        try:
            target = parsed[plugin_info.plugin_id]
        except KeyError:
            parsed[plugin_info.plugin_id] = target = {}
        target[key] = value
    return parsed


#------------------------------------------------------------------------------
def build_config_from_cmdline():

    # Get the command line parser.
    parser = cmdline_parser()

    # Parse the command line options.
    try:
        args = sys.argv[1:]
        envcfg = getenv("GOLISMERO_SETTINGS")
        if envcfg:
            args = parser.convert_arg_line_to_args(envcfg) + args
        P, V = parser.parse_known_args(args)
        if P.targets:
            P.targets += V
        else:
            P.targets = V
        P.plugin_args = {}
        command = P.command.upper()
        if command in COMMANDS:
            P.command = command
            if command == "RESCAN":
                P.command = "SCAN"
                P.redo = True
            else:
                P.redo = False
        else:
            P.targets.insert(0, P.command)
            P.command = "SCAN"

        # Load the Orchestrator options.
        cmdParams = OrchestratorConfig()
        cmdParams.command = P.command
        if P.config:
            cmdParams.config_file = path.abspath(P.config)
            if not path.isfile(cmdParams.config_file):
                raise ValueError("File not found: %s" % cmdParams.config_file)
        if cmdParams.config_file:
            cmdParams.from_config_file(cmdParams.config_file,
                                       allow_profile = True)
        if P.user_config:
            cmdParams.user_config_file = path.abspath(P.user_config)
            if not path.isfile(cmdParams.user_config_file):
                raise ValueError(
                    "File not found: %s" % cmdParams.user_config_file)
        if cmdParams.user_config_file:
            cmdParams.from_config_file(cmdParams.user_config_file,
                                       allow_profile = True)
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
        auditParams.profile          = cmdParams.profile
        auditParams.profile_file     = cmdParams.profile_file
        auditParams.config_file      = cmdParams.config_file
        auditParams.user_config_file = cmdParams.user_config_file
        if auditParams.config_file:
            auditParams.from_config_file(auditParams.config_file)
        if auditParams.user_config_file:
            auditParams.from_config_file(auditParams.user_config_file)
        if auditParams.profile_file:
            auditParams.from_config_file(auditParams.profile_file)
        auditParams.from_object(P)
        auditParams.plugin_load_overrides = P.plugin_load_overrides

        # If importing is turned off, remove the list of imports.
        # FIXME this should be done by argparse in argument order!
        if P.disable_importing:
            auditParams.imports = []

        # If reports are turned off, remove the list of reports.
        # Otherwise, if no reports are specified, default to screen report.
        # FIXME this should be done by argparse in argument order!
        if P.disable_reporting:
            auditParams.reports = []
        elif (
            not auditParams.reports and
            (P.command != "REPORT" or not auditParams.targets)
        ):
            auditParams.reports = ["-"]
            if auditParams.only_vulns is None:
                auditParams.only_vulns = True

    # Show exceptions as command line parsing errors.
    except Exception, e:
        ##raise    # XXX DEBUG
        parser.error("arguments error: %s" % str(e))

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

    # Return the parser, options, and config objects.
    return parser, P, cmdParams, auditParams


#------------------------------------------------------------------------------
# Start of program.
def main():

    # Command implementations.
    command = {
        "PLUGINS":  command_plugins,  # List plugins and quit.
        "INFO":     command_info,     # Display plugin info and quit.
        "PROFILES": command_profiles, # List profiles and quit.
        "DUMP":     command_dump,     # Dump the database and quit.
        "LOAD":     command_load,     # Load a database dump and quit.
        "UPDATE":   command_update,   # Update GoLismero and quit.
    }

    # Parse the command line.
    parser, P, cmdParams, auditParams = build_config_from_cmdline()

    # Get the command implementation.
    implementation = command.get(P.command, command_run)

    # Run the command.
    implementation(parser, P, cmdParams, auditParams)


#------------------------------------------------------------------------------
def command_plugins(parser, P, cmdParams, auditParams):

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
            print "\n%s:\n    %s" % \
                  (colorize(name[7:], "cyan"), info.description)

    # Testing plugins...
    testing_plugins = manager.get_plugins("testing")
    if testing_plugins:
        names = sorted(testing_plugins.keys())
        names = [x[8:] for x in names]
        stages = [ (v,k) for (k,v) in STAGES.iteritems() ]
        stages.sort()
        for _, stage in stages:
            s = stage + "/"
            p = len(s)
            s_slice = [x[p:] for x in names if x.startswith(s)]
            if s_slice:
                print
                print colorize("-= %s plugins =-" % stage.title(), "yellow")
                for name in s_slice:
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


#------------------------------------------------------------------------------
def command_info(parser, P, cmdParams, auditParams):

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
        for info in plugin_infos:
            Config._context = PluginContext(
                         address = None,
                       msg_queue = None,
                orchestrator_pid = getpid(),
                orchestrator_tid = get_ident(),
                     plugin_info = info
            )
            try:
                manager.load_plugin_by_id(info.plugin_id)
            except Exception:
                pass
            m_root = cmdParams.plugins_folder
            m_root = path.abspath(m_root)
            if not m_root.endswith(path.sep):
                m_root += path.sep
            m_location = info.descriptor_file[len(m_root):]
            a, b = path.split(m_location)
            b = colorize(b, "cyan")
            m_location = path.join(a, b)
            m_src = info.plugin_module[len(m_root):]
            a, b = path.split(m_src)
            b = colorize(b, "cyan")
            m_src = path.join(a, b)
            m_name = info.plugin_id
            p = m_name.rfind("/") + 1
            m_name = m_name[:p] + colorize(m_name[p:], "cyan")
            m_desc = info.description.strip()
            m_desc = m_desc.replace("\n", "\n    ")
            to_print.append("")
            to_print.append("Information for plugin: %s" %
                colorize(info.display_name, "yellow"))
            to_print.append("-" * len("Information for plugin: %s" %
                info.display_name))
            to_print.append("%s          %s" %
                (colorize("ID:", "green"), m_name))
            to_print.append("%s    %s" %
                (colorize("Location:", "green"), m_location))
            to_print.append("%s %s" %
                (colorize("Source code:", "green"), m_src))
            if info.plugin_class:
                to_print.append("%s  %s" %
                    (colorize("Class name:", "green"),
                     colorize(info.plugin_class, "cyan")))
            to_print.append("%s    %s" %
                (colorize("Category:", "green"), info.category))
            to_print.append("%s       %s" %
                (colorize("Stage:", "green"), info.stage))
            if info.description != info.display_name:
                to_print.append("")
                to_print.append("%s\n    %s" %
                    (colorize("Description:", "green"), m_desc))
            if info.plugin_args:
                to_print.append("")
                to_print.append(colorize("Arguments:", "green"))
                for name, default in sorted(info.plugin_args.iteritems()):
                    if name in info.plugin_passwd_args:
                        default = "****************"
                    to_print.append("\t%s -> %s" %
                        (colorize(name, "cyan"), default))
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


#------------------------------------------------------------------------------
def command_profiles(parser, P, cmdParams, auditParams):
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


#------------------------------------------------------------------------------
def command_dump(parser, P, cmdParams, auditParams):
    if auditParams.is_new_audit():
        parser.error("missing audit database")
    if not P.reports:
        parser.error("missing output filename")
    if P.verbose != 0:
        print "Loading database: %s" % \
              colorize(auditParams.audit_db, "yellow")
    import sqlite3
    for filename in P.reports:
        if P.verbose != 0:
            print "Dumping to file: %s" % colorize(filename, "cyan")
        db = sqlite3.connect(auditParams.audit_db)
        try:
            with open(filename, 'w') as f:
                for line in db.iterdump():
                    f.write(line + "\n")
        finally:
            db.close()
    exit(0)


#------------------------------------------------------------------------------
def command_load(parser, P, cmdParams, auditParams):
    if not auditParams.is_new_audit():
        parser.error("audit database already exists")
    if not P.imports:
        parser.error("missing input filename")
    if len(P.imports) > 1:
        parser.error("only one input filename allowed")
    import sqlite3
    filename = P.imports[0]
    if P.verbose != 0:
        print "Loading from file: %s" % colorize(filename, "cyan")
    with open(filename, 'rU') as f:
        data = f.read()
    if P.verbose != 0:
        print "Creating database: %s" % \
              colorize(auditParams.audit_db, "yellow")
    db = sqlite3.connect(auditParams.audit_db)
    try:
        try:
            cursor = db.cursor()
            try:
                cursor.executescript(data)
                del data
                db.commit()
            finally:
                cursor.close()
        finally:
            db.close()
    except:
        parser.error("error loading database dump: " + str(sys.exc_value))
    exit(0)


#------------------------------------------------------------------------------
def command_update(parser, P, cmdParams, auditParams):

    # Fail if we got any arguments.
    if P.targets:
        parser.error("too many arguments")

    # Setup a dummy environment so we can call the API.
    with PluginTester(autoinit=False) as t:
        t.orchestrator_config.ui_mode = "console"
        t.orchestrator_config.verbose = cmdParams.verbose
        t.orchestrator_config.color   = cmdParams.color
        t.init_environment(mock_audit=False)

        # Flag to tell if we fetched new code.
        did_update = False

        # Run Git here to download the latest version.
        if cmdParams.verbose:
            Logger.log("Updating GoLismero...")
        if os.path.exists(os.path.join(here, ".git")):
            helper = _GitHelper(cmdParams.verbose)
            run_external_tool("git", ["pull"], cwd = here, callback = helper)
            did_update = helper.did_update
        elif cmdParams.verbose:
            Logger.log_error(
                "Cannot update GoLismero if installed from a zip file! You"
                " must install it from the Git repository to get updates.")

        # Update the TLD names.
        if cmdParams.verbose:
            Logger.log("Updating list of TLD names...")
        import tldextract
        tldextract.TLDExtract().update(True)

        # If no code was updated, just quit here.
        if not did_update:
            if cmdParams.verbose:
                Logger.log("Update complete.")
            exit(0)

        # Tell the user we're about to restart.
        if cmdParams.verbose:
            Logger.log("Reloading GoLismero...")

    # Unload GoLismero.
    import golismero.patches.mp
    golismero.patches.mp.undo()
    x = here
    if not x.endswith(os.path.sep):
        x += os.path.sep
    our_modules = {
        n: m for n, m in sys.modules.iteritems()
        if n.startswith("golismero.") or (
            hasattr(m, "__file__") and m.__file__.startswith(x)
        )
    }
    for n in our_modules.iterkeys():
        if n.startswith("golismero.") or n.startswith("plugin_"):
            del sys.modules[n]

    # Restart GoLismero.
    # Note that after this point we need to explicitly import the classes we
    # use, and make sure they're the newer versions of them. That means:
    # ALWAYS USE FULLY QUALIFIED NAMES FROM HERE ON.
    import golismero.api.logger
    import golismero.main.testing
    with golismero.main.testing.PluginTester(autoinit=False) as t:
        t.orchestrator_config.ui_mode = "console"
        t.orchestrator_config.verbose = cmdParams.verbose
        t.orchestrator_config.color   = cmdParams.color
        t.init_environment(mock_audit=False)

        # Call the plugin hooks.
        all_plugins = sorted(
            t.orchestrator.pluginManager.load_plugins().iteritems())
        for plugin_id, plugin in all_plugins:
            if hasattr(plugin, "update"):
                if cmdParams.verbose:
                    golismero.api.logger.Logger.log(
                        "Updating plugin %r..." % plugin_id)
                try:
                    t.run_plugin_method(plugin_id, "update")
                except Exception:
                    golismero.api.logger.Logger.log_error(format_exc())

        # Done!
        if cmdParams.verbose:
            golismero.api.logger.Logger.log("Update complete.")
        exit(0)

# Crappy way of telling if we actually did fetch new code.
class _GitHelper(object):
    def __init__(self, verbose):
        self.log = []
        self.verbose = verbose
    def __call__(self, msg):
        self.log.append(msg)
        if self.verbose:
            Logger.log(msg)
    @property
    def did_update(self):
        ##return True   # for testing
        return all("Already up-to-date." not in x for x in self.log)


#------------------------------------------------------------------------------
def command_run(parser, P, cmdParams, auditParams):

    # For the SCAN command, assume targets are URLs whenever feasible.
    if P.command == "SCAN":
        guessed_urls = []
        for target in auditParams.targets:
            if not "://" in target:
                guessed_urls.append("http://" + target)
        auditParams.targets.extend(guessed_urls)

    # For all other commands, disable the testing plugins.
    else:
        auditParams.plugin_load_overrides.append( (False, "testing") )

        # For the IMPORT command, targets are import files.
        if P.command == "IMPORT":
            auditParams.imports = auditParams.targets   # magic
            del auditParams.targets                     # magic

        # For the REPORT command, targets are report files.
        elif P.command == "REPORT":
            auditParams.reports = auditParams.targets   # magic
            del auditParams.targets                     # magic

        # If we reached this point, we have an internal error!
        else:
            raise RuntimeError("Unsupported command: %s" % P.command)

    # Expand wildcards for filenames on Windows.
    # On other platforms this is not needed,
    # as the shell already does it for us.
    if os.path.sep == "\\":
        auditParams._imports = expand_wildcards(auditParams._imports)
        auditParams._reports = expand_wildcards(auditParams._reports)

    try:

        # Load the plugins.
        manager = PluginManager()
        manager.find_plugins(cmdParams)

        # Sanitize the plugin arguments.
        try:
            if P.raw_plugin_args:
                P.plugin_args = parse_plugin_args(manager, P.raw_plugin_args)
        except KeyError, e:
            ##raise # XXX DEBUG
            parser.error("error parsing plugin arguments: %s" % str(e))

        # Prompt for passwords.
        for plugin_id in P.plugin_args.keys():
            plugin_info = manager.get_plugin_by_id(plugin_id)
            target_args = P.plugin_args[plugin_id]
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
        cmdParams.plugin_args   = P.plugin_args
        auditParams.plugin_args = P.plugin_args

        # Check the parameters.
        cmdParams.check_params()
        auditParams.check_params()

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
        elif msg == "No targets selected for audit.":
            msg = "no targets selected for audit " \
                  "(did you misspell the database filename?)"
        parser.error(msg)

    # Launch GoLismero.
    launcher.run(cmdParams, auditParams)
    exit(0)


#------------------------------------------------------------------------------
def expand_wildcards(filenames):
    expanded = []
    for filename in filenames:
        if "*" in filename or "?" in filename:
            expanded.extend(glob(filename))
        else:
            expanded.append(filename)
    return expanded


#------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
