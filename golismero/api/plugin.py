#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the base classes for GoLismero plugins.

To write your own plugin, you must derive from one of the following base classes:

- :py:class:`.ImportPlugin`: To write a plugin to load results from other tools.
- :py:class:`.TestingPlugin`: To write a testing/hacking plugin.
- :py:class:`.ReportPlugin`: To write a plugin to report the results.
- :py:class:`.UIPlugin`: To write a User Interface plugin.
"""

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

__all__ = [
    "UIPlugin", "ImportPlugin", "TestingPlugin", "ReportPlugin",
    "PluginState", "get_plugin_info", "get_plugin_ids", "get_plugin_name",
    "get_stage_name", "get_stage_display_name",
    "get_plugin_type_display_name", "get_plugin_type_description",
    "CATEGORIES", "STAGES", "load_plugin_class_from_info",
    "load_plugin_class", "import_plugin",
]

from .config import Config
from .external import run_external_tool
from .logger import Logger
from .progress import Progress
from .shared import SharedMap
from ..messaging.codes import MessageCode

import imp
import inspect
import os.path
import re
import shlex


#------------------------------------------------------------------------------
def get_plugin_ids():
    """
    Get the plugin IDs.

    :returns: Plugin IDs.
    :rtype: set(str)
    """
    return Config._context.remote_call(MessageCode.MSG_RPC_PLUGIN_GET_IDS)


#------------------------------------------------------------------------------
def get_plugin_info(plugin_id = None):
    """
    Get the plugin information for the requested plugin.

    :param plugin_id: Full plugin ID.
        Example: "testing/recon/spider".
        Defaults to the calling plugin ID.
    :type plugin_id: str

    :returns: Plugin information.
    :rtype: PluginInfo

    :raises KeyError: The plugin was not found.
    """
    if not plugin_id or (Config.plugin_info and plugin_id == Config.plugin_id):
        return Config.plugin_info
    return Config._context.remote_call(
        MessageCode.MSG_RPC_PLUGIN_GET_INFO, plugin_id)


#------------------------------------------------------------------------------
def get_plugin_name(plugin_id = None):
    """
    Get the plugin display name given its ID.

    :param plugin_id: Full plugin ID.
        Example: "testing/recon/spider".
        Defaults to the calling plugin ID.
    :type plugin_id: str

    :returns: Plugin display name.
    :rtype: str

    :raises KeyError: The plugin was not found.
    """
    if not plugin_id:
        return Config.plugin_info.display_name
    if plugin_id == "GoLismero":
        return "GoLismero"
    return get_plugin_info(plugin_id).display_name


#------------------------------------------------------------------------------
_STAGE_NAMES = [
    "import",
    "recon", "scan", "attack", "intrude", "cleanup",
    "report",
]
def get_stage_name(stage_number):
    """
    Given a number starting from zero, get the stage name.
    This allows you to get the stage names in the proper order.
    Returns None if there is no stage with that number.
    """
    if stage_number >= 0:
        try:
            return _STAGE_NAMES[stage_number]
        except IndexError:
            pass


#------------------------------------------------------------------------------
_STAGE_DISPLAY_NAMES = {
    "start"   : "Starting",
    "import"  : "Importing",
    "recon"   : "Reconaissance",
    "scan"    : "Scanning (non-intrusive)",
    "attack"  : "Exploitation (intrusive)",
    "intrude" : "Post-exploitation",
    "cleanup" : "Cleanup",
    "report"  : "Reporting",
    "finish"  : "Finished",
    "cancel"  : "Cancelled",
}

def get_stage_display_name(stage):
    """
    Get a user friendly display name for the given stage.

    :param stage:
        Valid stages are:%s
    :type stage: str

    :returns: Display name for the stage.
    :rtype: str

    :raises KeyError: The given stage does not exist.
    """
    return _STAGE_DISPLAY_NAMES[ stage.strip().lower() ]

get_stage_display_name.__doc__ %= "".join(
    "\n         - %s" % x for x in _STAGE_DISPLAY_NAMES.iterkeys())


#------------------------------------------------------------------------------
_PLUGIN_TYPE_NAMES = {
    "import"  : "Import",
    "recon"   : "Reconnaisance",
    "scan"    : "Scan",
    "attack"  : "Attack",
    "intrude" : "Intrude",
    "cleanup" : "Cleanup",
    "report"  : "Report",
    "ui"      : "User Interface",
}

def get_plugin_type_display_name(plugin_type):
    """
    Get a user friendly display name for the given plugin type.

    :param plugin_type:
        Valid plugin types are:%s
    :type plugin_type: str

    :returns: Display name for the plugin type.
    :rtype: str

    :raises KeyError: The given plugin type does not exist.
    """
    return _PLUGIN_TYPE_NAMES[ plugin_type.strip().lower() ]

get_plugin_type_display_name.__doc__ %= "".join(
    "\n         - %s" % x for x in _PLUGIN_TYPE_NAMES.iterkeys())


#------------------------------------------------------------------------------
_PLUGIN_TYPE_DESCRIPTIONS = {
    "import"  : "Import plugins collect previously found resources from other"
                " tools and store them in the audit database right before the"
                " audit starts.",
    "recon"   : "Reconnaisance plugins perform passive, non-invasive"
                " information gathering tests on the targets.",
    "scan"    : "Scan plugins perform active, non-invasive information"
                " gathering tests on the targets.",
    "attack"  : "Attack plugins perform invasive tests on the targets to"
                " exploit vulnerabilities in them.",
    "intrude" : "Intrude plugins use the access gained by Attack plugins to"
                " extract privileged information from the targets.",
    "cleanup" : "Cleanup plugins undo whatever changes the previous plugins"
                " may have done on the targets.",
    "report"  : "Report plugins control how the audit results will be"
                " exported to different file formats.",
    "testing" : "Testing plugins are the ones that perform the security tests."
                " They are categorized by stage: recon, scan, attack, intrude"
                " and cleanup.",
    "ui"      : "User Interface plugins control the way in which the user"
                " interacts with GoLismero.",
}

def get_plugin_type_description(plugin_type):
    """
    Get a user-friendly description from a plugin type.

    :param plugin_type:
        Valid plugin types are:%s
    :type plugin_type: str

    :returns: Plugin type description.
    :rtype: str

    :raises KeyError: The given plugin type does not exist.
    """
    return _PLUGIN_TYPE_DESCRIPTIONS[ plugin_type.strip().lower() ]

get_plugin_type_description.__doc__ %= "".join(
    "\n         - %s" % x for x in _PLUGIN_TYPE_DESCRIPTIONS.iterkeys())


#------------------------------------------------------------------------------
class _PluginProgress (Progress):
    """
    Progress monitor for plugins.

    .. warning: Do not instance this class!
                Use self.progress in your plugin instead.
    """


    #--------------------------------------------------------------------------
    def _notify(self):
        percent = self.percent
        if percent:
            Config._context.send_status(percent)


#------------------------------------------------------------------------------
class PluginState (SharedMap):
    """
    Container of plugin state variables.

    State variables are stored in the audit database.
    That way plugins can maintain state regardless of which process
    (or machine!) is running them at any given point in time.
    """

    # Compatibility, remove once nobody is using this method.
    set = SharedMap.async_put


    #--------------------------------------------------------------------------
    def __init__(self, plugin_id = None):
        """
        :param plugin_id: Plugin ID.
            If ommitted, the calling plugin state variables are accessed.
        :type plugin_id: str
        """
        if not plugin_id:
            plugin_id = Config.plugin_id
        self._shared_id = plugin_id
        # We intentionally don't call the superclass constructor here.


    #--------------------------------------------------------------------------
    @property
    def plugin_id(self):
        """
        :returns: ID of the plugin these state variables belong to.
        :rtype: str
        """
        return self._shared_id


#------------------------------------------------------------------------------
class Plugin (object):
    """
    Base class for all plugins.
    """

    PLUGIN_TYPE_ABSTRACT = 0    # Not a real plugin type!
    PLUGIN_TYPE_UI       = 1
    PLUGIN_TYPE_IMPORT   = 2
    PLUGIN_TYPE_TESTING  = 3
    PLUGIN_TYPE_REPORT   = 4

    PLUGIN_TYPE = PLUGIN_TYPE_ABSTRACT


    #--------------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):
        """
        Initializes the plugin instance.

        .. warning::
            Do not override this method!
        """
        self = super(Plugin, cls).__new__(cls, *args, **kwargs)
        self.__progress = _PluginProgress()
        return self


    #--------------------------------------------------------------------------
    @property
    def state(self):
        """
        .. warning::
            Do not override this method!

        :returns: Shared plugin state variables.
        :rtype: PluginState
        """
        return PluginState()


    #--------------------------------------------------------------------------
    @property
    def progress(self):
        """
        .. warning::
            Do not override this method!

        :returns: Plugin progress notifier.
        :rtype: Progress
        """
        return self.__progress


    #--------------------------------------------------------------------------
    def update_status(self, progress = None):
        """
        Plugins can call this method to tell the user of the current
        progress of whatever the plugin is doing.

        .. warning::
            Do not override this method!

        .. note::
            This method may not be supported in future versions of GoLismero.

        :param progress: Progress percentage [0, 100] as a float,
                         or None to indicate progress can't be measured.
        :type progress: float | None
        """
        ##Config._context.send_status(progress)

        if progress is not None:
            self.progress.set_percent(progress)


#------------------------------------------------------------------------------
class _InformationPlugin (Plugin):
    """
    Information plugins are the ones that receive information, and may also
    send it back. Thus they can form feedback loops among each other.

    .. warning: This is an abstract class, do not use it!
    """


    #--------------------------------------------------------------------------
    def check_params(self):
        """
        Callback method to verify the plugin configuration and arguments.
        This allows plugins with mandatory arguments to disable themselves
        if said arguments are missing.

        There is no return value, but if an exception is raised the plugin
        will be disabled.

        :raises AttributeError: A critical configuration option is missing.
        :raises ValueError: A configuration option has an incorrect value.
        :raises TypeError: A configuration option has a value of a wrong type.
        :raises RuntimeError: A problem was found in the runtime environment.
        :raises Exception: An error occurred while validating the settings.
        """
        pass


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        """
        Returns one or more classes describing which data types are accepted by
        the run() method.

        By returning Data subclasses, your plugin indicates it wants to be
        notified of the creation of new objects (that is, the addition of new
        nodes in the graph). By returning Relationship classes, your plugin
        indicates it wants to be notified of new relationships between objects
        rather than the creation of new objects (that is, the addition of new
        vertices in the graph).

        If there is no return value, or the return value is None, the plugin
        receives every possible event. If the return value is an empty iterable
        the plugin receives no events.

        Example:

            # A plugin that is run every time a new URL object is created.
            def get_accepted_types(self):
                return URL

            # Run the plugin when new URL or Domain objects are created.
            def get_accepted_types(self):
                return URL, Domain

            # Run when a vulnerability is associated to a domain.
            def get_accepted_types(self):
                return Relationship(Vulnerability, Domain)

            # Run when a vulnerability is associated to an URL,
            # a base URL, or a folder URL.
            def get_accepted_types(self):
                return Relationship(Vulnerability, URL), \
                       Relationship(Vulnerability, BaseURL), \
                       Relationship(Vulnerability, FolderURL)

        :returns: Data types or relationships.
        :rtype: class | iterable(class) | None
        """
        raise NotImplementedError("Plugins must implement this method!")


    #--------------------------------------------------------------------------
    def run(self, info):
        """
        Callback method to receive data to be processed.

        This is the most important method of a plugin.
        Here's where most of the logic resides.

        :param info: Data to be processed.
        :type info: Data | Relationship
        """
        raise NotImplementedError("Plugins must implement this method!")


#------------------------------------------------------------------------------
class UIPlugin (_InformationPlugin):
    """
    User Interface plugins control the way in which
    the user interacts with GoLismero.

    This is the base class for all UI plugins.
    """

    PLUGIN_TYPE = Plugin.PLUGIN_TYPE_UI


    #--------------------------------------------------------------------------
    def check_params(self, options, *audits):
        """
        Callback method to verify the Orchestrator and initial Audit settings
        before launching GoLismero.

        .. warning: This method should only perform validation on the settings.
            No API calls can be made, since it's run from the launcher itself
            before GoLismero has finished starting up, so the plugin execution
            context is not yet initialized.

        :param options: Orchestrator settings.
        :type options: OrchestratorConfig

        :param audits: Audit settings.
        :type audits: AuditConfig

        :raises AttributeError: A critical configuration option is missing.
        :raises ValueError: A configuration option has an incorrect value.
        :raises TypeError: A configuration option has a value of a wrong type.
        :raises Exception: An error occurred while validating the settings.
        """
        pass


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return []                  # UI plugins get no data objects by default.


    #--------------------------------------------------------------------------
    def recv_msg(self, message):
        """
        Callback method to receive control messages to be processed.

        :param message: incoming message to process
        :type message: Message
        """
        raise NotImplementedError("Plugins must implement this method!")


#------------------------------------------------------------------------------
class ImportPlugin (Plugin):
    """
    Import plugins collect previously found resources from other tools
    and store them in the audit database right before the audit starts.

    This is the base class for all Import plugins.
    """

    PLUGIN_TYPE = Plugin.PLUGIN_TYPE_IMPORT


    #--------------------------------------------------------------------------
    def is_supported(self, input_file):
        """
        Determine if this plugin supports the requested file format.

        Tipically, here is where Import plugins examine the file extension.

        :param input_file: Input file to parse.
        :type input_file: str

        :returns: True if this plugin supports the format, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Plugins must implement this method!")


    #--------------------------------------------------------------------------
    def import_results(self, input_file):
        """
        Run plugin and import the results into the audit database.

        This is the entry point for Import plugins,
        where most of the logic resides.

        :param input_file: Input file to parse.
        :type input_file: str
        """
        raise NotImplementedError("Plugins must implement this method!")


#------------------------------------------------------------------------------
class TestingPlugin (_InformationPlugin):
    """
    Testing plugins are the ones that perform the security tests.

    This is the base class for all Testing plugins.
    """

    PLUGIN_TYPE = Plugin.PLUGIN_TYPE_TESTING


#------------------------------------------------------------------------------
class ReportPlugin (Plugin):
    """
    Report plugins control how results will be exported.

    This is the base class for all Report plugins.
    """

    PLUGIN_TYPE = Plugin.PLUGIN_TYPE_REPORT


    #--------------------------------------------------------------------------
    def is_supported(self, output_file):
        """
        Determine if this plugin supports the requested file format.

        Typically, here is where Report plugins examine the file extension.
        The default implementation (that is, when not overridden by a plugin)
        checks to see if the file extension matches that of a class variable
        called "EXTENSION". If this variable is not defined in your plugin
        class, then your plugin MUST override this method instead.

        :param output_file: Output file to generate.
        :type output_file: str

        :returns: True if this plugin supports the format, False otherwise.
        :rtype: bool
        """
        if hasattr(self, "EXTENSION"):
            return output_file and output_file.lower().endswith(self.EXTENSION)
        raise NotImplementedError(
            "Plugins must either define the EXTENSION class variable"
            " or override this method!")


    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        """
        Run plugin and generate the report.

        This is the entry point for Report plugins,
        where most of the logic resides.

        :param output_file: Output file to generate.
        :type output_file: str
        """
        raise NotImplementedError("Plugins must implement this method!")


    #--------------------------------------------------------------------------
    def launch_command(self, output_file):
        """
        Launch a build command, if any is defined in the plugin configuration.

        :param output_file: Output file for this report plugin.
        :type output_file: str
        """
        command = Config.plugin_args.get("command", "")
        if command:
            Logger.log_verbose("Launching command: %s" % command)
            args = shlex.split(command)
            for i in xrange(len(args)):
                token = args[i]
                p = token.find("$1")
                while p >= 0:
                    if p == 0 or (p > 0 and token[p-1] != "$"):
                        token = token[:p] + output_file + token[p+2:]
                    p = token.find("$1", p + len(output_file))
                args[i] = token
            cwd = os.path.split(output_file)[0]
            log = lambda x: Logger.log_verbose(
                x[:-1] if x.endswith("\n") else x)
            run_external_tool(args[0], args[1:], cwd=cwd, callback=log)


#------------------------------------------------------------------------------
# Plugin class loader.

# Plugin categories and their base classes.
CATEGORIES = {
    "import"  : ImportPlugin,
    "testing" : TestingPlugin,
    "report"  : ReportPlugin,
    "ui"      : UIPlugin,
}

# Testing plugin execution stages by name.
STAGES = {
    "recon"   : 1,    # Reconaissance stage.
    "scan"    : 2,    # Scanning (non-intrusive) stage.
    "attack"  : 3,    # Exploitation (intrusive) stage.
    "intrude" : 4,    # Post-exploitation stage.
    "cleanup" : 5,    # Cleanup stage.
}

def load_plugin_class(plugin_id):
    """
    Loads a plugin class given the plugin ID.

    :param plugin_id: Plugin ID.
    :type plugin_id: str

    :returns: Plugin class.
    :rtype: class

    :raises KeyError: The plugin was not found.
    :raises ImportError: The plugin class could not be loaded.
    """

    # Get the plugin info. Raises exception on error.
    plugin_info = get_plugin_info(plugin_id)

    # Load the plugin from the plugin info object.
    return load_plugin_class_from_info(plugin_info)

def load_plugin_class_from_info(info):
    """
    Loads a plugin class given the plugin information.

    :param info: Plugin information.
    :type info: PluginInfo

    :returns: Plugin class.
    :rtype: class

    :raises KeyError: The plugin was not found.
    :raises ImportError: The plugin class could not be loaded.
    """

    # Get the plugin ID.
    plugin_id = info.plugin_id

    # Get the source code file.
    source = info.plugin_module

    # Import the plugin module.
    module_fake_name = "plugin_" + re.sub(r"\W|^(?=\d)", "_", plugin_id)
    module = imp.load_source(module_fake_name, source)

    # Get the plugin class name.
    class_name = info.plugin_class

    # If we know the plugin class name, get the class.
    if class_name:
        try:
            clazz = getattr(module, class_name)
        except Exception:
            raise ImportError(
                "Plugin class %s not found in file: %s" %
                (class_name, source))

    # If we don't know the plugin class name, we need to find it.
    else:

        # Get the plugin base class for its category.
        base_class = CATEGORIES[ plugin_id[ : plugin_id.find("/") ] ]

        # Get all public symbols from the module.
        public_symbols = [
            getattr(module, symbol)
            for symbol in getattr(module, "__all__", [])
        ]
        if not public_symbols:
            public_symbols = [
                value
                for (symbol, value) in module.__dict__.iteritems()
                if not symbol.startswith("_")
            ]
            if not public_symbols:
                raise ImportError(
                    "Plugin class not found in file: %s" % source)

        # Find all public classes that derive from the base class.
        # NOTE: it'd be faster to stop on the first match,
        #       but then we can't check for ambiguities (see below)
        candidates = []
        bases = CATEGORIES.values()
        for value in public_symbols:
            try:
                if issubclass(value, base_class) and value not in bases:
                    candidates.append(value)
            except TypeError:
                pass

        # If there are no candidates, raise an exception.
        if not candidates:
            raise ImportError(
                "Plugin class not found in file: %s" % source)

        # If there's more than one candidate, filter out those that
        # weren't defined within this module (i.e. imported classes).
        if len(candidates) > 1:
            tmp = [
                c for c in candidates
                if c.__module__ == module.__name__
            ]
            if tmp:
                candidates = tmp

            # If we've still more than one candidate, raise an exception.
            if len(candidates) > 1:
                msg = (
                    "Error loading %r:"
                    " can't decide which plugin class to load: %s"
                ) % (source, ", ".join(c.__name__ for c in candidates))
                raise ImportError(msg)

        # Get the plugin class.
        clazz = candidates.pop()

    # Return the plugin class.
    return clazz

def import_plugin(source):
    """
    Import a sibling plugin given the relative path to its source code.

    :param source: Relative path to the source code.
    :type source: str

    :returns: Plugin module.
    :type: module

    :raises ImportError: The plugin module could not be loaded.
    """

    # Get the calling plugin module.
    caller = inspect.getmodule(inspect.stack()[1][0])

    # Get the target file relative to the calling plugin file.
    filename = os.path.dirname(caller.__file__)
    filename = os.path.join(filename, source)
    filename = os.path.abspath(filename)

    # Import the plugin module.
    module_fake_name = "plugin_" + re.sub(r"\W|^(?=\d)", "_", filename)
    return imp.load_source(module_fake_name, filename)
