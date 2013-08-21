#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'Priscilla', the GoLismero plugin manager.
"""

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

__all__ = ["PluginManager", "PluginInfo"]

from .rpcmanager import implementor
from ..api.plugin import UIPlugin, ImportPlugin, TestingPlugin, ReportPlugin
from ..common import Configuration, OrchestratorConfig, AuditConfig
from ..messaging.codes import MessageCode

from collections import defaultdict
from ConfigParser import RawConfigParser
from keyword import iskeyword
from os import path, walk

import re
import fnmatch
import imp
import warnings


#----------------------------------------------------------------------
# Helpers for instance creation without calling __init__().
class _EmptyNewStyleClass (object):
    pass


#----------------------------------------------------------------------
# RPC implementors for the plugin manager API.

@implementor(MessageCode.MSG_RPC_PLUGIN_GET_NAMES)
def rpc_plugin_get_names(orchestrator, audit_name, *args, **kwargs):
    if audit_name:
        return orchestrator.auditManager.get_audit(audit_name).pluginManager.get_plugin_names(*args, **kwargs)
    return orchestrator.pluginManager.get_plugin_names(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_PLUGIN_GET_INFO)
def rpc_plugin_get_info(orchestrator, audit_name, *args, **kwargs):
    if audit_name:
        return orchestrator.auditManager.get_audit(audit_name).pluginManager.get_plugin_by_name(*args, **kwargs)
    return orchestrator.pluginManager.get_plugin_by_name(*args, **kwargs)


#----------------------------------------------------------------------
class PluginInfo (object):
    """
    Plugin descriptor object.
    """

    @property
    def plugin_name(self):
        """
        :returns: Plugin name.
        :rtype: str
        """
        return self.__plugin_name

    @property
    def descriptor_file(self):
        """
        :returns: Plugin descriptor file name.
        :rtype: str
        """
        return self.__descriptor_file

    @property
    def category(self):
        """
        :returns: Plugin category.
        :rtype: str
        """
        return self.__plugin_name.split("/")[0].lower()

    @property
    def stage(self):
        """
        :returns: Plugin stage name.
        :rtype: int
        """
        if self.category == "testing":
            return PluginManager.get_stage_name_from_value(self.__stage_number)
        return self.category

    @property
    def stage_number(self):
        """
        :returns: Plugin stage number.
        :rtype: int
        """
        return self.__stage_number

    @property
    def dependencies(self):
        """
        :returns: Plugin dependencies.
        :rtype: tuple(str...)
        """
        return self.__dependencies

    @property
    def recursive(self):
        """
        :returns: True if the plugin is recursive, False otherwise.
        :rtype: bool
        """
        return self.__recursive

    @property
    def plugin_module(self):
        """
        :returns: Plugin module file name.
        :rtype: str
        """
        return self.__plugin_module

    @property
    def plugin_class(self):
        """
        :returns: Plugin class name.
        :rtype: str
        """
        return self.__plugin_class

    @property
    def plugin_args(self):
        """
        :returns: Plugin arguments.
        :rtype: dict(str -> str)
        """
        return self.__plugin_args

    @property
    def plugin_passwd_args(self):
        """
        :returns: Plugin password argument names.
        :rtype: set(str)
        """
        return self.__plugin_passwd_args

    @property
    def plugin_config(self):
        """
        :returns: Plugin configuration.
        :rtype: dict(str -> str)
        """
        return self.__plugin_config

    @property
    def plugin_extra_config(self):
        """
        :returns: Plugin extra configuration.
        :rtype: dict(str -> dict(str -> str))
        """
        return self.__plugin_extra_config

    @property
    def display_name(self):
        """
        :returns: Display name to be shown to the user.
        :rtype: str
        """
        return self.__display_name

    @property
    def description(self):
        """
        :returns: Description of this plugin's functionality.
        :rtype: str
        """
        return self.__description

    @property
    def version(self):
        """
        :returns: Version of this plugin.
        :rtype: str
        """
        return self.__version

    @property
    def author(self):
        """
        :returns: Author of this plugin.
        :rtype: str
        """
        return self.__author

    @property
    def copyright(self):
        """
        :returns: Copyright of this plugin.
        :rtype: str
        """
        return self.__copyright

    @property
    def license(self):
        """
        :returns: License for this plugin.
        :rtype: str
        """
        return self.__license

    @property
    def website(self):
        """
        :returns: Web site where you can download the latest version of this plugin.
        :rtype: str
        """
        return self.__website


    #----------------------------------------------------------------------
    def __init__(self, plugin_name, descriptor_file, global_config):
        """
        Load a plugin descriptor file.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param descriptor_file: Descriptor file (with ".golismero" extension).
        :type descriptor_file: str

        :param global_config: Orchestrator settings.
        :type global_config: OrchestratorConfig
        """

        # Store the plugin name.
        self.__plugin_name = plugin_name

        # Make sure the descriptor filename is an absolute path.
        descriptor_file = path.abspath(descriptor_file)

        # Store the descriptor filename.
        self.__descriptor_file = descriptor_file

        # Parse the descriptor file.
        parser = RawConfigParser()
        parser.read(descriptor_file)

        # Read the "[Core]" section.
        try:
            self.__display_name = parser.get("Core", "Name")
        except Exception:
            self.__display_name = plugin_name
        try:
            plugin_module       = parser.get("Core", "Module")
        except Exception:
            plugin_module       = path.splitext(path.basename(descriptor_file))[0]
        try:
            plugin_class        = parser.get("Core", "Class")
        except Exception:
            plugin_class        = None
        try:
            stage               = parser.get("Core", "Stage")
        except Exception:
            stage               = None
        try:
            dependencies        = parser.get("Core", "Dependencies")
        except Exception:
            dependencies        = None
        try:
            recursive           = parser.get("Core", "Recursive")
        except Exception:
            recursive           = "no"

        # Parse the stage name to get the number.
        if not stage:
            try:
                category, subcategory = plugin_name.split("/")[:2]
                category = category.strip().lower()
                subcategory = subcategory.strip().lower()
                if category == "testing":
                    self.__stage_number = PluginManager.STAGES[subcategory]
                else:
                    self.__stage_number = 0
            except Exception:
                self.__stage_number = 0
        else:
            try:
                self.__stage_number = PluginManager.STAGES[stage.lower()]
            except KeyError:
                try:
                    self.__stage_number = int(stage)
                    if self.__stage_number not in PluginManager.STAGES.values():
                        raise ValueError()
                except Exception:
                    msg = "Error parsing %r: invalid execution stage: %r"
                    raise ValueError(msg % (descriptor_file, stage))

        # Sanitize the plugin module pathname.
        if not plugin_module.endswith(".py"):
            plugin_module += ".py"
        if path.sep != "/":
            plugin_module = plugin_module.replace("/", path.sep)
        if path.isabs(plugin_module):
            msg = "Error parsing %r: plugin module path is absolute"
            raise ValueError(msg % descriptor_file)
        plugin_folder = path.split(descriptor_file)[0]
        plugin_module = path.abspath(path.join(plugin_folder, plugin_module))
        plugins_root  = path.abspath(global_config.plugins_folder)
        if not plugins_root.endswith(path.sep):
            plugins_root += path.sep
        if not plugin_module.startswith(plugins_root):
            msg = "Error parsing %r: plugin module (%s) is located outside the plugins folder (%s)"
            raise ValueError(msg % (descriptor_file, plugin_module, plugins_root))

        # Sanitize the plugin classname.
        if plugin_class is not None:
            plugin_class = re.sub(r"\W|^(?=\d)", "_", plugin_class.strip())
            if iskeyword(plugin_class):
                msg = "Error parsing %r: plugin class (%s) is a Python reserved keyword"
                raise ValueError(msg % (plugin_class, descriptor_file))

        # Store the plugin module and class.
        self.__plugin_module = plugin_module
        self.__plugin_class  = plugin_class

        # Parse the list of dependencies.
        if not dependencies:
            self.__dependencies = ()
        else:
            self.__dependencies = tuple(sorted( {x.strip() for x in dependencies.split(",")} ))

        # Parse the recursive flag.
        try:
            self.__recursive = Configuration.boolean(recursive)
        except Exception:
            msg = "Error parsing %r: invalid recursive flag: %r"
            raise ValueError(msg % (descriptor_file, recursive))

        # Read the "[Description]" section.
        try:
            self.__description = parser.get("Documentation", "Description")
        except Exception:
            self.__description = self.__display_name
        try:
            self.__version     = parser.get("Documentation", "Version")
        except Exception:
            self.__version     = "?.?"
        try:
            self.__author      = parser.get("Documentation", "Author")
        except Exception:
            self.__author      = "Anonymous"
        try:
            self.__copyright   = parser.get("Documentation", "Copyright")
        except Exception:
            self.__copyright   = "No copyright information"
        try:
            self.__license     = parser.get("Documentation", "License")
        except Exception:
            self.__license     = "No license information"
        try:
            self.__website     = parser.get("Documentation", "Website")
        except Exception:
            self.__website     = "https://github.com/golismero"

        # Load the plugin arguments as a Python dictionary.
        # This section is optional.
        self.__plugin_passwd_args = set()
        self.__plugin_args        = {}
        try:
            args = parser.items("Arguments")
        except Exception:
            args = ()
        for key, value in args:
            if key.startswith("*"):
                key = key[1:].strip()
                self.__plugin_passwd_args.add(key)
            self.__plugin_args[key] = value

        # Load the plugin configuration as a Python dictionary.
        # This section is optional.
        try:
            self.__plugin_config = dict( parser.items("Configuration") )
        except Exception:
            self.__plugin_config = dict()

        # Load the plugin extra configuration sections as a dict of dicts.
        # All sections not parsed above will be included here.
        self.__plugin_extra_config = dict()
        for section in parser.sections():
            if section not in ("Core", "Documentation", "Configuration"):
                options = dict( (k.lower(), v) for (k, v) in parser.items(section) )
                self.__plugin_extra_config[section] = options

        # Override the plugin configuration from the global config file(s).
        self.__read_config_file(global_config.config_file)
        self.__read_config_file(global_config.profile_file)


    #----------------------------------------------------------------------
    def __copy__(self):
        raise NotImplementedError("Only deep copies, please!")


    #----------------------------------------------------------------------
    def __deepcopy__(self):

        # Create a new empty object.
        instance = _EmptyNewStyleClass()
        instance.__class__ = self.__class__

        # Copy the properties.
        instance.__plugin_name         = self.__plugin_name
        instance.__descriptor_file     = self.__descriptor_file
        instance.__display_name        = self.__display_name
        instance.__stage_number        = self.__stage_number
        instance.__recursive           = self.__recursive
        instance.__plugin_module       = self.__plugin_module
        instance.__plugin_class        = self.__plugin_class
        instance.__dependencies        = self.__dependencies
        instance.__description         = self.__description
        instance.__version             = self.__version
        instance.__author              = self.__author
        instance.__copyright           = self.__copyright
        instance.__license             = self.__license
        instance.__website             = self.__website
        instance.__plugin_args         = self.__plugin_args.copy()
        instance.__plugin_config       = self.__plugin_config.copy()
        instance.__plugin_extra_config = {
            k: v.copy()
            for (k, v) in self.__plugin_extra_config.iteritems()
        }

        # Return the new instance.
        return instance


    #----------------------------------------------------------------------
    def customize_for_audit(self, audit_config):
        """
        Return a new PluginInfo instance with its configuration overriden
        by the audit settings.

        :param audit_config: Audit settings.
        :type audit_config: AuditConfig

        :returns: New, customized PluginInfo instance.
        :rtype: PluginInfo
        """

        # Check the argument type.
        if not isinstance(audit_config, AuditConfig):
            raise TypeError("Expected AuditConfig, got %s instead" % type(audit_config))

        # Make a customized copy and return it.
        new_instance = self.__deepcopy__()
        new_instance.__read_config_file(audit_config.config_file)
        new_instance.__read_config_file(audit_config.profile_file)
        return new_instance


    #----------------------------------------------------------------------
    def __read_config_file(self, config_file):
        """
        Private method to override plugin settings from a config file.

        :param config_file: Configuration file.
        :type config_file: str
        """

        # Dumb check.
        if not config_file:
            return

        # Sections beginning with the plugin name are for this plugin.
        section_prefix = self.__plugin_name

        # Parse the config file.
        config_parser = RawConfigParser()
        config_parser.read(config_file)

        # Go through each section.
        for section in config_parser.sections():

            # If the section name is exactly the plugin name,
            # copy the settings to the plugin configuration.
            if section == section_prefix:
                target = self.__plugin_config

            # The section name can also be the plugin name and
            # the plugin config file section separated by a colon.
            elif ":" in section:
                a, b = section.split(":", 1)
                a, b = a.strip(), b.strip()
                if a == section_prefix:

                    # Override the arguments.
                    if b == "Arguments":
                        target = self.__plugin_args

                    # Same as just using the plugin name.
                    elif b == "Configuration":
                        target = self.__plugin_config

                    # Special sections Core and Documentation can't
                    # be overridden by config files.
                    elif b in ("Core", "Documentation"):
                        msg = "Ignored section [%s] of file %s"
                        warnings.warn(msg % (section, config_file))
                        continue

                    # Override the plugin extra configuration.
                    try:
                        target = self.__plugin_extra_config[b]
                    except KeyError:
                        target = self.__plugin_extra_config[b] = dict()

            # All other sections are ignored.
            else:
                continue

            # Copy the settings.
            target.update( config_parser.items(section) )


    #----------------------------------------------------------------------
    def _fix_classname(self, plugin_class):
        """
        Protected method to update the class name if found during plugin load.
        (Assumes it's always valid, so no sanitization is performed).

        .. warning: This method is called internally by GoLismero,
                    do not call it yourself!

        :param plugin_class: Plugin class name.
        :type plugin_class: str
        """
        self.__plugin_class = plugin_class


#----------------------------------------------------------------------
class PluginManager (object):
    """
    Plugin Manager.
    """


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

    # Minimum and maximum stage numbers.
    min_stage = min(*STAGES.values())
    max_stage = max(*STAGES.values())
    assert sorted(STAGES.itervalues()) == range(min_stage, max_stage + 1)


    #----------------------------------------------------------------------
    def __init__(self):

        # Dictionary to collect the info for each plugin found
        self.__plugins = {}    # plugin name -> plugin info

        # Dictionary to cache the plugin instances
        self.__cache = {}


    #----------------------------------------------------------------------
    @classmethod
    def get_stage_name_from_value(cls, value):
        """
        :param value: Stage value. See STAGES.
        :type value: int

        :returns: Stage name.
        :rtype: str

        :raise KeyError: Stage value not found.
        """
        for name, val in cls.STAGES.iteritems():
            if value == val:
                return name
        raise KeyError("Stage value not found: %r" % value)


    #----------------------------------------------------------------------
    def find_plugins(self, orchestrator_config):
        """
        Find plugins in the given folder.

        The folder must contain one subfolder for each plugin category,
        inside which are the plugins.

        Each plugin is defined in a file with the ".golismero" extension.
        The code for each plugin must be in a Python script within the same
        folder as the ".golismero" file, or within any subdirectory of it.

        :param orchestrator_config: Orchestrator settings.
        :type orchestrator_config: OrchestratorConfig

        :returns: A list of plugins loaded, and a list of plugins that failed to load.
        :rtype: tuple(list(str), list(str))
        """

        # XXX FIXME: this forces the plugin folder structure, but
        # we should be able to parse the categories from the config
        # file instead if the user wants to store all plugins together.

        # Check the argument type.
        if not isinstance(orchestrator_config, OrchestratorConfig):
            raise TypeError("Expected OrchestratorConfig, got %s instead" % type(orchestrator_config))

        # Get the plugins folder.
        plugins_folder = orchestrator_config.plugins_folder

        # Default plugins folder if not given.
        if not plugins_folder:
            plugins_folder = path.join(path.split(__file__)[0], "..", "..", "plugins")
            plugins_folder = path.abspath(plugins_folder)

        # Make sure the plugins folder is an absolute path.
        plugins_folder = path.abspath(plugins_folder)

        # Raise an exception if the plugins folder doesn't exist or isn't a folder.
        if not path.isdir(plugins_folder):
            raise ValueError("Invalid plugins folder: %s" % plugins_folder)

        # Update the Orchestrator config if needed.
        if orchestrator_config.plugins_folder != plugins_folder:
            orchestrator_config.plugins_folder = plugins_folder

        # List to collect the plugins that loaded successfully.
        success = list()

        # List to collect the plugins that failed to load.
        failure = list()

        # The first directory level is the category.
        for current_category, _ in self.CATEGORIES.iteritems():

            # Get the folder for this category.
            category_folder = path.join(plugins_folder, current_category)

            # Skip missing folders.
            if not path.isdir(category_folder):
                warnings.warn("Missing plugin category folder: %s" % category_folder)
                continue

            # The following levels belong to the plugins.
            for (dirpath, _, filenames) in walk(category_folder):

                # Look for plugin descriptor files.
                for fname in filenames:
                    if not fname.endswith(".golismero"):
                        continue

                    # Convert the plugin descriptor filename to an absolute path.
                    fname = path.abspath(path.join(dirpath, fname))

                    # The plugin name is the relative path + filename without extension,
                    # where the path separator is always "/" regardless of the current OS.
                    plugin_name = path.splitext(fname)[0][len(plugins_folder):]
                    if plugin_name[0] == path.sep:
                        plugin_name = plugin_name[1:]
                    if path.sep != "/":
                        plugin_name = plugin_name.replace(path.sep, "/")

                    # If the plugin name already exists, skip it.
                    if plugin_name in self.__plugins:
                        failure.append(plugin_name)
                        continue

                    # Parse the plugin descriptor file.
                    try:
                        plugin_info = PluginInfo(plugin_name, fname, orchestrator_config)

                        # Collect the plugin info.
                        self.__plugins[plugin_name] = plugin_info

                        # Add the plugin name to the success list.
                        success.append(plugin_name)

                    # On error add the plugin name to the list of failures.
                    except Exception, e:
                        warnings.warn("Failure while loading plugins: %s" % e)
                        failure.append(plugin_name)

        # Return the successes and failures.
        return success, failure


    #----------------------------------------------------------------------
    def get_plugins(self, category = "all"):
        """
        Get info on the available plugins, optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Mapping of plugin names to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)

        :raises KeyError: The requested category or stage doesn't exist.
        """

        # Make sure the category is lowercase.
        category = category.lower()

        # If not filtering for category, just return the whole dictionary.
        if category == "all":
            return self.__plugins.copy()

        # If it's a category, get only the plugins that match the category.
        if category in self.CATEGORIES:
            return { plugin_name: plugin_info
                     for plugin_name, plugin_info in self.__plugins.iteritems()
                     if plugin_info.category == category }

        # If it's a stage, get only the plugins that match the stage.
        if category in self.STAGES:
            stage_num = self.STAGES[category]
            return { plugin_name: plugin_info
                     for plugin_name, plugin_info in self.__plugins.iteritems()
                     if plugin_info.stage_number == stage_num }

        # If it's neither, it's an error.
        raise KeyError("Unknown plugin category or stage: %r" % category)


    #----------------------------------------------------------------------
    def get_plugin_names(self, category = "all"):
        """
        Get the names of the available plugins, optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Plugin names.
        :rtype: set(str)

        :raises KeyError: The requested category or stage doesn't exist.
        """
        return set(self.get_plugins(category).iterkeys())


    #----------------------------------------------------------------------
    def get_plugin_by_name(self, plugin_name):
        """
        Get info on the requested plugin.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :returns: Plugin information.
        :rtype: PluginInfo

        :raises KeyError: The requested plugin doesn't exist.
        """
        try:
            return self.__plugins[plugin_name]
        except KeyError:
            raise KeyError("Plugin not found: %r" % plugin_name)

    # Alias.
    __getitem__ = get_plugin_by_name


    #----------------------------------------------------------------------
    def guess_plugin_by_name(self, plugin_name):
        """
        Get info on the requested plugin.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :returns: Plugin information.
        :rtype: PluginInfo

        :raises KeyError: The requested plugin doesn't exist,
            or more than one plugin matches the request.
        """
        if any(c in plugin_name for c in "?*["):
            found = self.search_plugins_by_mask(plugin_name)
            if len(found) != 1:
                raise KeyError("Plugin not found: %s" % plugin_name)
            return found.popitem()[1]
        try:
            return self.get_plugin_by_name(plugin_name)
        except KeyError:
            found = self.search_plugins_by_name(plugin_name)
            if len(found) != 1:
                raise
            return found.popitem()[1]


    #----------------------------------------------------------------------
    def search_plugins_by_name(self, search_string):
        """
        Try to match the search string against plugin names.

        :param search_string: Search string.
        :type search_string: str

        :returns: Mapping of plugin names to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        return {
            plugin_name: plugin_info
            for plugin_name, plugin_info in self.__plugins.iteritems()
            if search_string == plugin_name[ plugin_name.rfind("/") + 1 : ]
        }


    #----------------------------------------------------------------------
    def search_plugins_by_mask(self, glob_mask):
        """
        Try to match the glob mask against plugin names.

        If the glob mask has a / then it applies to the whole path,
        if it doesn't then it applies to either the whole path or
        a single component of it.

        :param glob_mask: Glob mask.
        :type glob_mask: str

        :returns: Mapping of plugin names to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        gfilter = fnmatch.filter
        gmatch  = fnmatch.fnmatch
        plugins = self.__plugins
        matches = {
            plugin_name: plugins[plugin_name]
            for plugin_name in gfilter(plugins.iterkeys(), glob_mask)
        }
        if "/" not in glob_mask:
            matches.update({
                plugin_name: plugin_info
                for plugin_name, plugin_info in plugins.iteritems()
                if any(
                    gmatch(token, glob_mask)
                    for token in plugin_name.split("/")
                )
            })
        return matches


    #----------------------------------------------------------------------
    def search_plugins(self, search_string):
        """
        Try to match the search string against plugin names.
        The search string may be any substring or a glob mask.

        :param search_string: Search string.
        :type search_string: str

        :returns: Mapping of plugin names to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        if any(c in search_string for c in "?*["):
            return self.search_plugins_by_mask(search_string)
        return self.search_plugins_by_name(search_string)


    #----------------------------------------------------------------------
    def load_plugins(self, category = "all"):
        """
        Get info on the available plugins, optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Mapping of plugin names to Plugin instances.
        :rtype: dict(str -> Plugin)

        :raises KeyError: The requested category or stage doesn't exist.
        :raises Exception: Plugins may throw exceptions if they fail to load.
        """
        return {
            name : self.load_plugin_by_name(name)
            for name in sorted( self.get_plugin_names(category) )
        }


    #----------------------------------------------------------------------
    def load_plugin_by_name(self, name):
        """
        Load the requested plugin by name.

        :param name: Name of the plugin to load.
        :type name: str

        :returns: Plugin instance.
        :rtype: Plugin

        :raises Exception: Plugins may throw exceptions if they fail to load.
        """

        # If the plugin was already loaded, return the instance from the cache.
        instance = self.__cache.get(name, None)
        if instance is not None:
            return instance

        # Get the plugin info.
        try:
            info = self.__plugins[name]
        except KeyError:
            raise KeyError("Plugin not found: %r" % name)

        # Get the plugin module file.
        source = info.plugin_module

        # Import the plugin module.
        module_fake_name = "plugin_" + re.sub(r"\W|^(?=\d)", "_", name)
        module = imp.load_source(module_fake_name, source)

        # Get the plugin classname.
        classname = info.plugin_class

        # If we know the plugin classname, get the class.
        if classname:
            try:
                clazz = getattr(module, classname)
            except Exception:
                raise ImportError("Plugin class %s not found in file: %s" % (classname, source))

        # If we don't know the plugin classname, we need to find it.
        else:

            # Get the plugin base class for its category.
            base_class = self.CATEGORIES[ name[ : name.find("/") ] ]

            # Get all public symbols from the module.
            public_symbols = [getattr(module, symbol) for symbol in getattr(module, "__all__", [])]
            if not public_symbols:
                public_symbols = [value for (symbol, value) in module.__dict__.iteritems()
                                        if not symbol.startswith("_")]
                if not public_symbols:
                    raise ImportError("Plugin class not found in file: %s" % source)

            # Find all public classes that derive from the base class.
            # NOTE: it'd be faster to stop on the first match,
            #       but then we can't check for ambiguities (see below)
            candidates = []
            bases = self.CATEGORIES.values()
            for value in public_symbols:
                try:
                    if issubclass(value, base_class) and value not in bases:
                        candidates.append(value)
                except TypeError:
                    pass

            # There should be only one candidate, if not raise an exception.
            if not candidates:
                raise ImportError("Plugin class not found in file: %s" % source)
            if len(candidates) > 1:
                msg = "Error loading %r: can't decide which plugin class to load: %s"
                msg = msg % (source, ", ".join(c.__name__ for c in candidates))
                raise ImportError(msg)

            # Get the plugin class.
            clazz = candidates.pop()

            # Add the classname to the plugin info.
            info._fix_classname(clazz.__name__)

        # Instance the plugin class.
        instance = clazz()

        # Add it to the cache.
        self.__cache[name] = instance

        # Return the instance.
        return instance


    #----------------------------------------------------------------------
    def get_plugin_info_from_instance(self, instance):
        """
        Get a plugin's name and information from its already loaded instance.

        :param instance: Plugin instance.
        :type instance: Plugin

        :returns: tuple(str, PluginInfo) -- Plugin name and information.
        :raises KeyError: Plugin instance not found.
        """
        for (name, value) in self.__cache.iteritems():
            if value is instance:
                return (name, self.__plugins[name])
        try:
            r = repr(instance)
        except Exception:
            r = repr(id(instance))
        raise KeyError("Plugin instance not found: " + r)


    #----------------------------------------------------------------------
    def parse_plugin_args(self, plugin_args):
        """
        Parse a list of tuples with plugin arguments as a dictionary of
        dictionaries, with plugin names sanitized.

        Once sanitized, you can all set_plugin_args() to set them.

        :param plugin_args: Arguments as specified in the command line.
        :type plugin_args: list(tuple(str, str, str))

        :returns: Sanitized plugin arguments. Dictionary mapping plugin
            names to dictionaries mapping argument names and values.
        :rtype: dict(str -> dict(str -> str))

        :raises KeyError: Plugin or argument not found.
        """
        parsed = {}
        for plugin_name, key, value in plugin_args:
            plugin_info = self.guess_plugin_by_name(plugin_name)
            key = key.lower()
            if key not in plugin_info.plugin_args:
                raise KeyError(
                    "Argument not found: %s:%s" % (plugin_name, key))
            try:
                target = parsed[plugin_info.plugin_name]
            except KeyError:
                parsed[plugin_info.plugin_name] = target = {}
            target[key] = value
        return parsed


    #----------------------------------------------------------------------
    def set_plugin_args(self, plugin_name, plugin_args):
        """
        Set the user-defined values for the given plugin arguments.

        :param plugin_name: Plugin name.
        :type plugin_name: str

        :param plugin_args: Plugin arguments and their user-defined values.
        :type plugin_args: dict(str -> str)

        :returns: One of the following values:
             - 0: All values set successfully.
             - 1: The plugin was not loaded or does not exist.
             - 2: Some values were not defined for this plugin.
        """
        try:
            plugin_info = self.get_plugin_by_name(plugin_name)
        except KeyError:
            return 1
        target_args = plugin_info.plugin_args
        status = 0
        for key, value in plugin_args.iteritems():
            if key in target_args:
                target_args[key] = value
            else:
                status = 2
        return status


    #----------------------------------------------------------------------
    def get_plugin_manager_for_audit(self, audit):
        """
        Instance an audit-specific plugin manager.

        :param audit: Audit.
        :type audit: Audit

        :returns: Plugin manager for this audit.
        :rtype: AuditPluginManager

        :raises ValueError: Configuration error.
        """
        return AuditPluginManager(
            self, audit.orchestrator.config, audit.config
        )


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this manager.
        """
        self.__plugins = None
        self.__cache   = None


#----------------------------------------------------------------------
class AuditPluginManager (PluginManager):
    """
    Plugin manager for audits.
    """


    #----------------------------------------------------------------------
    def __init__(self, pluginManager, orchestratorConfig, auditConfig):

        # Superclass constructor.
        super(AuditPluginManager, self).__init__()

        # Keep a reference to the plugin manager of the orchestrator.
        self.__pluginManager = pluginManager

        # Batches and stages of plugins (see calculate_dependencies)
        self.__batches = None   # list
        self.__stages  = None   # dict

        # Apply the plugin black and white lists, and all the overrides.
        self._PluginManager__plugins = self.__apply_config(auditConfig)
        if auditConfig.plugin_args:
            for plugin_name, plugin_args in auditConfig.plugin_args.iteritems():
                self.set_plugin_args(plugin_name, plugin_args)

        # Calculate the dependencies.
        self.__calculate_dependencies()


    #----------------------------------------------------------------------

    @property
    def pluginManager(self):
        """
        :returns: Plugin manager.
        :rtype: PluginManager
        """
        return self.__pluginManager


    @property
    def batches(self):
        """
        :returns: Plugin execution batches.
        :rtype: list(set(str))
        """
        return self.__batches


    @property
    def stages(self):
        """
        :returns: Mapping of stage names to plugin names for each stage.
        :rtype: dict(str -> set(str))
        """
        return self.__stages


    #----------------------------------------------------------------------
    def __apply_config(self, auditConfig):
        """
        Apply the black and white lists.
        This controls which plugins are loaded and which aren't.

        :param auditConfig: Audit configuration.
        :type auditConfig: AuditConfig

        :returns: Mapping of the approved plugin names to
                  reconfigured instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)

        :raises ValueError: Configuration error.
        :raises KeyError: Configuration error.
        """

        # Check the argument type.
        if not isinstance(auditConfig, AuditConfig):
            raise TypeError("Expected AuditConfig, got %s instead" % type(auditConfig))

        # Get the black and white lists and the plugin load overrides.
        enable_plugins        = auditConfig.enable_plugins
        disable_plugins       = auditConfig.disable_plugins
        plugin_load_overrides = auditConfig.plugin_load_overrides

        # Dumb check.
        if not enable_plugins and not disable_plugins and not plugin_load_overrides:
            raise ValueError("No plugins selected for audit!")

        # Get all the plugin names.
        all_plugins = self.pluginManager.get_plugin_names()
        if not all_plugins:
            raise SyntaxError("Internal error!")

        # Remove duplicates in black and white lists.
        blacklist_approach = False
        if "all" in enable_plugins:
            enable_plugins     = {"all"}
        if "all" in disable_plugins:
            disable_plugins    = {"all"}
            blacklist_approach = True
        enable_plugins  = set(enable_plugins)
        disable_plugins = set(disable_plugins)

        # Check for consistency in black and white lists.
        conflicting_entries = enable_plugins.intersection(disable_plugins)
        if conflicting_entries:
            if len(conflicting_entries) > 1:
                msg = "The same entries are present in both black and white lists: %s"
                msg %= ", ".join(conflicting_entries)
            else:
                msg = "The same entry (%s) is present in both black and white lists"
                msg %= conflicting_entries.pop()
            raise ValueError(msg)

        # Expand the black and white lists.
        disable_plugins = self.__expand_plugin_list(disable_plugins, "blacklist")
        enable_plugins  = self.__expand_plugin_list(enable_plugins,  "whitelist")

        # Apply the black and white lists.
        if blacklist_approach:
            plugins = all_plugins.intersection(enable_plugins) # use only enabled plugins
        else:
            plugins = all_plugins.difference(disable_plugins)  # use all but disabled plugins

        # Process the plugin load overrides. They only apply to testing plugins.
        # First, find out if there are only enables but no disables.
        # If so, insert a disable command for all testing plugins before the first enable.
        # For all commands, symbolic plugin names are replaced with sets of full IDs.
        if plugin_load_overrides:
            only_enables = all(x[0] for x in plugin_load_overrides)
            overrides = []
            if only_enables:
                plugin_load_overrides.insert( 0, (False, "all") )
            for flag, token in plugin_load_overrides:
                token = token.strip().lower()
                if token in ("all", "testing"):
                    names = self.pluginManager.get_plugin_names("testing")
                    overrides.append( (flag, names) )
                elif token in self.STAGES:
                    names = self.pluginManager.get_plugin_names(token)
                    overrides.append( (flag, names) )
                elif token in all_plugins:
                    info = self.pluginManager.get_plugin_by_name(token)
                    if info.category != "testing":
                        raise ValueError("Not a testing plugin: %s" % token)
                    overrides.append( (flag, (token,)) )
                else:
                    if any(c in token for c in "?*["):
                        matching_plugins = self.pluginManager.search_plugins_by_mask(token)
                        for name, info in matching_plugins.iteritems():
                            if info.category != "testing":
                                raise ValueError("Not a testing plugin: %s" % token)
                            overrides.append( (flag, (name,)) )
                    else:
                        matching_plugins = self.pluginManager.search_plugins_by_name(token)
                        if not matching_plugins:
                            raise ValueError("Unknown plugin: %s" % token)
                        if len(matching_plugins) > 1:
                            msg = ("Ambiguous plugin name %r"
                                   " may refer to any of the following plugins: %s")
                            msg %= (token, ", ".join(sorted(matching_plugins.iterkeys())))
                            raise ValueError(msg)
                        name, info = matching_plugins.items()[0]
                        if info.category != "testing":
                            raise ValueError("Not a testing plugin: %s" % token)
                        overrides.append( (flag, (name,)) )

            # Apply the processed plugin load overrides.
            for enable, names in overrides:
                if enable:
                    plugins.update(names)
                else:
                    plugins.difference_update(names)

        # The UI plugins cannot be disabled.
        plugins.update( self.pluginManager.get_plugin_names("ui") )

        # Return a customized copy of the approved plugins info.
        return {
            name: self.pluginManager[name].customize_for_audit(auditConfig)
            for name in plugins
        }


    #----------------------------------------------------------------------
    def __expand_plugin_list(self, plugin_list, list_name):
        """
        Expand aliases in a plugin black/white list.

        :param plugin_list: Plugin black/white list.
        :type plugin_list: set

        :param list_name: Name of the list ("blacklist" or "whitelist").
        :type list_name: str

        :returns: Black/white list with expanded aliases.
        :rtype: set

        :raises ValueError: Configuration error.
        :raises KeyError: Configuration error.
        """

        # Convert "all" to the entire list of plugins.
        if "all" in plugin_list:
            plugin_list = self.pluginManager.get_plugin_names()
        else:

            # Convert categories to plugin names.
            for category in self.CATEGORIES:
                if category in plugin_list:
                    plugin_list.remove(category)
                    plugin_list.update(self.pluginManager.get_plugin_names(category))

            # Convert stages to plugin names.
            for stage in self.STAGES:
                if stage in plugin_list:
                    plugin_list.remove(stage)
                    plugin_list.update(self.pluginManager.get_plugin_names(stage))

        # Guess partial plugin names in the list.
        # Also make sure all the plugins in the list exist.
        missing_plugins = set()
        all_plugins = self.pluginManager.get_plugin_names()
        for name in sorted(plugin_list):
            if name not in all_plugins:
                matching_plugins = set(self.pluginManager.search_plugins(name).keys())
                if not matching_plugins:
                    missing_plugins.add(name)
                    continue
                if len(matching_plugins) > 1:
                    msg = ("Ambiguous entry in %s (%r)"
                           " may refer to any of the following plugins: %s")
                    msg %= (list_name, name, ", ".join(sorted(matching_plugins)))
                    raise ValueError(msg)
                plugin_list.remove(name)
                plugin_list.update(matching_plugins)
        if missing_plugins:
            if len(missing_plugins) > 1:
                msg = "Unknown plugins in %s: %s"
                msg %= (list_name, ", ".join(sorted(missing_plugins)))
            else:
                msg = "Unknown plugin in %s: %s"
                msg %= (list_name, missing_plugins.pop())
            raise KeyError(msg)

        # Return the expanded list.
        return plugin_list


    #----------------------------------------------------------------------
    def __calculate_dependencies(self):
        """
        Generate a dependency graph for all plugins found, and calculate
        the batches of plugins that can be run concurrently.

        :raises ValueError: The dependencies are broken.
        """

        # Get all the plugins that support dependencies.
        plugins = self.get_plugins("testing")
        all_names = set(plugins.iterkeys())

        # Build the dependency graph, and group plugins by stage.
        # Raise an exception for missing dependencies.
        graph = defaultdict(set)
        stages = defaultdict(set)
        for name, info in plugins.iteritems():
            stage = info.stage_number
            if not stage or stage < 0:
                stage = 0
            stages[stage].add(name)
            deps = set(info.dependencies)
            if not deps.issubset(all_names):
                msg = "Plugin %s depends on missing plugin(s): %s"
                msg %= (name, ", ".join(sorted(deps.difference(all_names))))
                raise ValueError(msg)
            graph[name] = deps

        # Add the implicit dependencies defined by the stages into the graph.
        # (We're creating dummy bridge nodes to reduce the number of edges.)
        stage_numbers = sorted(self.STAGES.itervalues())
        for n in stage_numbers:
            this_stage = "* stage %d" % n
            next_stage = "* stage %d" % (n + 1)
            graph[next_stage].add(this_stage)
        for n in stage_numbers:
            bridge = "* stage %d" % n
            graph[bridge].update(stages[n])
            for node in stages[n + 1]:
                graph[node].add(bridge)

        # Calculate the plugin batches.
        # Raise an exception for circular dependencies.
        batches = []
        while graph:
            ready = {name for name, deps in graph.iteritems() if not deps}
            if not ready:
                # TODO: find each circle in the graph and show it,
                #       instead of dumping the remaining graph
                msg = "Circular dependencies found in plugins: "
                keys = [ k for k in graph.iterkeys() if not k.startswith("*") ]
                keys.sort()
                raise ValueError(msg + ", ".join(keys))
            for name in ready:
                del graph[name]
            for deps in graph.itervalues():
                deps.difference_update(ready)
            ready = {k for k in ready if not k.startswith("*")}
            if ready:
                batches.append(ready)

        # Store the plugin batches and stages.
        self.__batches = batches
        self.__stages  = stages


    #----------------------------------------------------------------------
    def next_concurrent_plugins(self, candidate_plugins):
        """
        Based on the previously executed plugins, get the next plugins
        to execute.

        :param candidate_plugins: Plugins we may want to execute.
        :type candidate_plugins: set(str)

        :returns: Next plugins to execute.
        :rtype: set(str)
        """
        if candidate_plugins:
            for batch in self.__batches:
                batch = batch.intersection(candidate_plugins)
                if batch:
                    return batch
        return set()


    #----------------------------------------------------------------------
    def find_plugins(self, plugins_folder = None):
        """
        .. warning: This method is not available for audits.
        """
        raise NotImplementedError("Not available for audits!")


    #----------------------------------------------------------------------
    def get_plugin_manager_for_audit(self, audit):
        """
        .. warning: This method is not available for audits.
        """
        raise NotImplementedError("Not available for audits!")


    #----------------------------------------------------------------------
    def load_plugin_by_name(self, name):

        # Get the plugin info. Fails if the plugin is disabled.
        info = self.get_plugin_by_name(name)

        # Make the global plugin manager load it, so we can share the cache.
        instance = self.pluginManager.load_plugin_by_name(name)

        # Fix the classname locally.
        info._fix_classname(instance.__class__.__name__)

        # Return the plugin instance.
        return instance


    #----------------------------------------------------------------------
    def get_plugin_info_from_instance(self, instance):

        # Cached by the global plugin manager.
        return self.pluginManager.get_plugin_info_from_instance(instance)


    #--------------------------------------------------------------------------
    def close(self):
        try:
            super(AuditPluginManager, self).close()
        finally:
            self.__pluginManager = None
            self.__batches       = None
            self.__stages        = None
