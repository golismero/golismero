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
from ..api.audit import get_audit_config, get_audit_scope
from ..api.config import Config
from ..api.logger import Logger
from ..api.plugin import CATEGORIES, STAGES, load_plugin_class_from_info, \
    get_plugin_info
from ..common import Configuration, OrchestratorConfig, AuditConfig, \
    get_default_plugins_folder, EmptyNewStyleClass
from ..managers.processmanager import PluginContext
from ..messaging.codes import MessageCode

from collections import defaultdict
from ConfigParser import RawConfigParser
from keyword import iskeyword
from os import path, walk

import re
import fnmatch
import traceback
import warnings


#------------------------------------------------------------------------------
# RPC implementors for the plugin manager API.

@implementor(MessageCode.MSG_RPC_PLUGIN_GET_IDS)
def rpc_plugin_get_ids(orchestrator, audit_name, *args, **kwargs):
    if audit_name:
        audit = orchestrator.auditManager.get_audit(audit_name)
        try:
            return audit.pluginManager.get_plugin_ids(*args, **kwargs)
        except KeyError:
            pass
    return orchestrator.pluginManager.get_plugin_ids(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_PLUGIN_GET_INFO)
def rpc_plugin_get_info(orchestrator, audit_name, *args, **kwargs):
    if audit_name:
        audit = orchestrator.auditManager.get_audit(audit_name)
        try:
            return audit.pluginManager.get_plugin_by_id(*args, **kwargs)
        except KeyError:
            pass
    return orchestrator.pluginManager.get_plugin_by_id(*args, **kwargs)


#------------------------------------------------------------------------------
class PluginInfo (object):
    """
    Plugin descriptor object.
    """

    @property
    def plugin_id(self):
        """
        :returns: Plugin ID.
        :rtype: str
        """
        return self.__plugin_id

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
        return self.__plugin_id.split("/")[0].lower()

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
        :returns: Web site where you can download
            the latest version of this plugin.
        :rtype: str
        """
        return self.__website


    #--------------------------------------------------------------------------
    def __init__(self, plugin_id, descriptor_file, global_config):
        """
        Load a plugin descriptor file.

        :param plugin_id: Plugin ID.
        :type plugin_id: str

        :param descriptor_file: Descriptor file (with ".golismero" extension).
        :type descriptor_file: str

        :param global_config: Orchestrator settings.
        :type global_config: OrchestratorConfig
        """

        # Store the plugin ID.
        self.__plugin_id = plugin_id

        # Make sure the descriptor filename is an absolute path.
        descriptor_file = path.abspath(descriptor_file)

        # Store the descriptor filename.
        self.__descriptor_file = descriptor_file

        # Parse the descriptor file.
        parser = RawConfigParser()
        parser.read(descriptor_file)

        # Read the "[Core]" section.
        try:
            plugin_module       = parser.get("Core", "Module")
        except Exception:
            plugin_module       = path.splitext(
                                    path.basename(descriptor_file))[0]
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
                category, subcategory = plugin_id.split("/")[:2]
                category = category.strip().lower()
                subcategory = subcategory.strip().lower()
                if category == "testing":
                    self.__stage_number = STAGES[subcategory]
                else:
                    self.__stage_number = 0
            except Exception:
                self.__stage_number = 0
        else:
            try:
                self.__stage_number = STAGES[stage.lower()]
            except KeyError:
                try:
                    self.__stage_number = int(stage)
                    if self.__stage_number not in STAGES.values():
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
            msg = (
                "Error parsing %r:"
                " plugin module (%s) is located"
                " outside the plugins folder (%s)"
            ) % (descriptor_file, plugin_module, plugins_root)
            raise ValueError(msg)

        # Sanitize the plugin classname.
        if plugin_class is not None:
            plugin_class = re.sub(r"\W|^(?=\d)", "_", plugin_class.strip())
            if iskeyword(plugin_class):
                msg = (
                    "Error parsing %r:"
                    " plugin class (%s) is a Python reserved keyword"
                ) % (plugin_class, descriptor_file)
                raise ValueError(msg)

        # Store the plugin module and class.
        self.__plugin_module = plugin_module
        self.__plugin_class  = plugin_class

        # Parse the list of dependencies.
        if not dependencies:
            self.__dependencies = ()
        else:
            self.__dependencies = tuple(sorted(
                {x.strip() for x in dependencies.split(",")}
            ))

        # Parse the recursive flag.
        try:
            self.__recursive = Configuration.boolean(recursive)
        except Exception:
            msg = "Error parsing %r: invalid recursive flag: %r"
            raise ValueError(msg % (descriptor_file, recursive))

        # Read the "[Documentation]" section.
        try:
            self.__display_name = parser.get("Documentation", "Name")
        except Exception:
            self.__display_name = plugin_id
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
            if section not in ("Core", "Documentation",
                               "Configuration", "Arguments"):
                options = dict(
                    (k.lower(), v) for (k, v) in parser.items(section)
                )
                self.__plugin_extra_config[section] = options

        # Override the plugin configuration from the global config file(s).
        self.__read_config_file(global_config.config_file)
        self.__read_config_file(global_config.user_config_file)
        self.__read_config_file(global_config.profile_file)


    #--------------------------------------------------------------------------
    def __copy__(self):
        raise NotImplementedError("Only deep copies, please!")


    #--------------------------------------------------------------------------
    def __deepcopy__(self):

        # Create a new empty object.
        instance = EmptyNewStyleClass()
        instance.__class__ = self.__class__

        # Copy the properties.
        instance.__plugin_id           = self.__plugin_id
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
        instance.__plugin_passwd_args  = self.__plugin_passwd_args.copy()
        instance.__plugin_config       = self.__plugin_config.copy()
        instance.__plugin_extra_config = {
            k: v.copy()
            for (k, v) in self.__plugin_extra_config.iteritems()
        }

        # Return the new instance.
        return instance


    #--------------------------------------------------------------------------
    def __repr__(self):
        return (
            "<PluginInfo instance at %x: "
            "id=%s, "
            "stage=%s, "
            "recursive=%s, "
            "dependencies=%r, "
            "args=%r, "
            "config=%r, "
            "extra=%r"
            ">"
        ) % (
            id(self),
            self.plugin_id,
            self.stage,
            self.recursive,
            self.dependencies,
            self.plugin_args,
            self.plugin_config,
            self.plugin_extra_config,
        )


    #--------------------------------------------------------------------------
    def to_dict(self):
        """
        Convert this PluginInfo object into a dictionary.

        :returns: Converted PluginInfo object.
        :rtype: dict(str -> \\*)
        """
        return {
            "plugin_id"           : self.plugin_id,
            "descriptor_file"     : self.descriptor_file,
            "category"            : self.category,
            "stage"               : self.stage,
            "stage_number"        : self.stage_number,
            "dependencies"        : self.dependencies,
            "recursive"           : self.recursive,
            "plugin_module"       : self.plugin_module,
            "plugin_class"        : self.plugin_class,
            "display_name"        : self.display_name,
            "description"         : self.description,
            "version"             : self.version,
            "author"              : self.author,
            "copyright"           : self.copyright,
            "license"             : self.license,
            "website"             : self.website,
            "plugin_args"         : self.plugin_args.copy(),
            "plugin_passwd_args"  : self.plugin_passwd_args.copy(),
            "plugin_config"       : self.plugin_config.copy(),
            "plugin_extra_config" : {
                k: v.copy()
                for (k, v) in self.plugin_extra_config.iteritems()
            }
        }


    #--------------------------------------------------------------------------
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
            raise TypeError(
                "Expected AuditConfig, got %r instead" % type(audit_config))

        # Make a customized copy and return it.
        new_instance = self.__deepcopy__()
        new_instance.__read_config_file(audit_config.config_file)
        new_instance.__read_config_file(audit_config.user_config_file)
        new_instance.__read_config_file(audit_config.profile_file)
        return new_instance


    #--------------------------------------------------------------------------
    def __read_config_file(self, config_file):
        """
        Private method to override plugin settings from a config file.

        :param config_file: Configuration file.
        :type config_file: str
        """

        # Dumb check.
        if not config_file:
            return

        # Sections beginning with the plugin ID are for this plugin.
        section_prefix = self.__plugin_id
        section_prefix_short = section_prefix[ section_prefix.rfind("/")+1 : ]

        # Parse the config file.
        config_parser = RawConfigParser()
        config_parser.read(config_file)

        # Go through each section.
        for section in config_parser.sections():

            # If the section name is exactly the plugin ID,
            # copy the settings to the plugin arguments.
            if section in (section_prefix, section_prefix_short):
                target = self.__plugin_args

            # The section name can also be the plugin ID and
            # the plugin config file section separated by a colon.
            elif ":" in section:
                a, b = section.split(":", 1)
                a, b = a.strip(), b.strip()
                if a not in (section_prefix, section_prefix_short):
                    continue

                # Override the arguments.
                # Same as just using the plugin ID.
                if b == "Arguments":
                    target = self.__plugin_args

                # Override the configuration.
                elif b == "Configuration":
                    target = self.__plugin_config

                # Special sections Core and Documentation can't
                # be overridden by config files.
                elif b in ("Core", "Documentation"):
                    msg = "Ignored section [%s] of file %s"
                    warnings.warn(msg % (section, config_file))
                    continue

                else:

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


    #--------------------------------------------------------------------------
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


#------------------------------------------------------------------------------
class PluginManager (object):
    """
    Plugin Manager.
    """

    # Minimum and maximum stage numbers.
    min_stage = min(*STAGES.values())
    max_stage = max(*STAGES.values())
    assert sorted(STAGES.itervalues()) == range(min_stage, max_stage + 1)


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator = None):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator
        """

        # Orchestrator instance.
        self.__orchestrator = orchestrator

        # Dictionary to collect the info for each plugin found
        self.__plugins = {}    # plugin ID -> plugin info

        # Dictionary to cache the plugin instances
        self.__cache = {}


    #--------------------------------------------------------------------------
    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__orchestrator


    #--------------------------------------------------------------------------
    @classmethod
    def get_stage_name_from_value(cls, value):
        """
        :param value: Stage value. See STAGES.
        :type value: int

        :returns: Stage name.
        :rtype: str

        :raise KeyError: Stage value not found.
        """
        for name, val in STAGES.iteritems():
            if value == val:
                return name
        raise KeyError("Stage value not found: %r" % value)


    #--------------------------------------------------------------------------
    def find_plugins(self, config):
        """
        Find plugins in the given folder.

        The folder must contain one subfolder for each plugin category,
        inside which are the plugins.

        Each plugin is defined in a file with the ".golismero" extension.
        The code for each plugin must be in a Python script within the same
        folder as the ".golismero" file, or within any subdirectory of it.

        :param config: Orchestrator or Audit settings.
        :type config: OrchestratorConfig | AuditConfig

        :returns: A list of plugins loaded,
            and a list of plugins that failed to load.
        :rtype: tuple(list(str), list(str))
        """

        # XXX FIXME: this forces the plugin folder structure, but
        # we should be able to parse the categories from the config
        # file instead if the user wants to store all plugins together.

        # Check the argument type.
        if not isinstance(config, OrchestratorConfig):
            raise TypeError(
                "Expected OrchestratorConfig, got %r instead" % type(config))

        # Get the plugins folder. Must be an absolute path.
        plugins_folder = config.plugins_folder
        if plugins_folder:
            plugins_folder = path.abspath(plugins_folder)
        else:
            plugins_folder = get_default_plugins_folder()

        # Raise an exception if the plugins folder doesn't exist
        # or isn't a folder.
        if not path.isdir(plugins_folder):
            raise ValueError("Invalid plugins folder: %s" % plugins_folder)

        # Update the Orchestrator config if needed.
        if config.plugins_folder != plugins_folder:
            config.plugins_folder = plugins_folder

        # List to collect the plugins that loaded successfully.
        success = list()

        # List to collect the plugins that failed to load.
        failure = list()

        # The first directory level is the category.
        for current_category, _ in CATEGORIES.iteritems():

            # Get the folder for this category.
            category_folder = path.join(plugins_folder, current_category)

            # Skip missing folders.
            if not path.isdir(category_folder):
                warnings.warn(
                    "Missing plugin category folder: %s" % category_folder)
                continue

            # The following levels belong to the plugins.
            for (dirpath, _, filenames) in walk(category_folder):

                # Look for plugin descriptor files.
                for fname in filenames:
                    if not fname.endswith(".golismero"):
                        continue

                    # Convert the plugin descriptor filename
                    # to an absolute path.
                    fname = path.abspath(path.join(dirpath, fname))

                    # The plugin ID is the relative path + filename without
                    # extension, where the path separator is always "/"
                    # regardless of the current OS.
                    plugin_id = path.splitext(fname)[0][len(plugins_folder):]
                    if plugin_id[0] == path.sep:
                        plugin_id = plugin_id[1:]
                    if path.sep != "/":
                        plugin_id = plugin_id.replace(path.sep, "/")

                    # If the plugin ID already exists, skip it.
                    if plugin_id in self.__plugins:
                        failure.append(plugin_id)
                        continue

                    # Parse the plugin descriptor file.
                    try:
                        plugin_info = PluginInfo(plugin_id, fname, config)

                        # Collect the plugin info.
                        self.__plugins[plugin_id] = plugin_info

                        # Add the plugin ID to the success list.
                        success.append(plugin_id)

                    # On error add the plugin ID to the list of failures.
                    except Exception, e:
                        warnings.warn("Failure while loading plugins: %s" % e)
                        failure.append(plugin_id)

        # Return the successes and failures.
        return success, failure


    #--------------------------------------------------------------------------
    def get_plugins(self, category = "all"):
        """
        Get info on the available plugins, optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Mapping of plugin IDs to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)

        :raises KeyError: The requested category or stage doesn't exist.
        """

        # Make sure the category is lowercase.
        category = category.lower()

        # If not filtering for category, just return the whole dictionary.
        if category == "all":
            return self.__plugins.copy()

        # If it's a category, get only the plugins that match the category.
        if category in CATEGORIES:
            return { plugin_id: plugin_info
                     for plugin_id, plugin_info in self.__plugins.iteritems()
                     if plugin_info.category == category }

        # If it's a stage, get only the plugins that match the stage.
        if category in STAGES:
            stage_num = STAGES[category]
            return { plugin_id: plugin_info
                     for plugin_id, plugin_info in self.__plugins.iteritems()
                     if plugin_info.stage_number == stage_num }

        # If it's neither, it's an error.
        raise KeyError("Unknown plugin category or stage: %r" % category)


    #--------------------------------------------------------------------------
    def get_plugin_ids(self, category = "all"):
        """
        Get the names of the available plugins,
        optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Plugin IDs.
        :rtype: set(str)

        :raises KeyError: The requested category or stage doesn't exist.
        """
        return set(self.get_plugins(category).iterkeys())


    #--------------------------------------------------------------------------
    def get_plugin_by_id(self, plugin_id):
        """
        Get info on the requested plugin.

        :param plugin_id: Plugin ID.
        :type plugin_id: str

        :returns: Plugin information.
        :rtype: PluginInfo

        :raises KeyError: The requested plugin doesn't exist.
        """
        try:
            return self.__plugins[plugin_id]
        except KeyError:
            raise KeyError("Plugin not found: %r" % plugin_id)

    # Alias.
    __getitem__ = get_plugin_by_id


    #--------------------------------------------------------------------------
    def guess_plugin_by_id(self, plugin_id):
        """
        Get info on the requested plugin.

        :param plugin_id: Plugin ID.
        :type plugin_id: str

        :returns: Plugin information.
        :rtype: PluginInfo

        :raises KeyError: The requested plugin doesn't exist,
            or more than one plugin matches the request.
        """
        if any(c in plugin_id for c in "?*["):
            found = self.search_plugins_by_mask(plugin_id)
            if len(found) != 1:
                raise KeyError("Plugin not found: %s" % plugin_id)
            return found.popitem()[1]
        try:
            return self.get_plugin_by_id(plugin_id)
        except KeyError:
            found = self.search_plugins_by_id(plugin_id)
            if len(found) != 1:
                raise
            return found.popitem()[1]


    #--------------------------------------------------------------------------
    def search_plugins_by_id(self, search_string):
        """
        Try to match the search string against plugin IDs.

        :param search_string: Search string.
        :type search_string: str

        :returns: Mapping of plugin IDs to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        return {
            plugin_id: plugin_info
            for plugin_id, plugin_info in self.__plugins.iteritems()
            if search_string == plugin_id[ plugin_id.rfind("/") + 1 : ]
        }


    #--------------------------------------------------------------------------
    def search_plugins_by_mask(self, glob_mask):
        """
        Try to match the glob mask against plugin IDs.

        If the glob mask has a / then it applies to the whole path,
        if it doesn't then it applies to either the whole path or
        a single component of it.

        :param glob_mask: Glob mask.
        :type glob_mask: str

        :returns: Mapping of plugin IDs to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        gfilter = fnmatch.filter
        gmatch  = fnmatch.fnmatch
        plugins = self.__plugins
        matches = {
            plugin_id: plugins[plugin_id]
            for plugin_id in gfilter(plugins.iterkeys(), glob_mask)
        }
        if "/" not in glob_mask:
            matches.update({
                plugin_id: plugin_info
                for plugin_id, plugin_info in plugins.iteritems()
                if any(
                    gmatch(token, glob_mask)
                    for token in plugin_id.split("/")
                )
            })
        return matches


    #--------------------------------------------------------------------------
    def search_plugins(self, search_string):
        """
        Try to match the search string against plugin IDs.
        The search string may be any substring or a glob mask.

        :param search_string: Search string.
        :type search_string: str

        :returns: Mapping of plugin IDs to instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)
        """
        if any(c in search_string for c in "?*["):
            return self.search_plugins_by_mask(search_string)
        return self.search_plugins_by_id(search_string)


    #--------------------------------------------------------------------------
    def load_plugins(self, category = "all"):
        """
        Get info on the available plugins, optionally filtering by category.

        :param category: Category or stage.
            Use "all" to get plugins from all categories.
            Use "testing" to get all testing plugins for all stages.
        :type category: str

        :returns: Mapping of plugin IDs to Plugin instances.
        :rtype: dict(str -> Plugin)

        :raises KeyError: The requested category or stage doesn't exist.
        :raises Exception: Plugins may throw exceptions if they fail to load.
        """
        return {
            name : self.load_plugin_by_id(name)
            for name in sorted( self.get_plugin_ids(category) )
        }


    #--------------------------------------------------------------------------
    def load_plugin_by_id(self, plugin_id):
        """
        Load the requested plugin by ID.

        :param plugin_id: ID of the plugin to load.
        :type plugin_id: str

        :returns: Plugin instance.
        :rtype: Plugin

        :raises Exception: Plugins may throw exceptions if they fail to load.
        """

        # If the plugin was already loaded, return the instance from the cache.
        instance = self.__cache.get(plugin_id, None)
        if instance is not None:
            return instance

        # Get the plugin info.
        try:
            info = self.__plugins[plugin_id]
        except KeyError:
            raise KeyError("Plugin not found: %r" % plugin_id)

        # Load the plugin class.
        clazz = load_plugin_class_from_info(info)

        # If missing, add the classname to the plugin info.
        if not info.plugin_class:
            info._fix_classname(clazz.__name__)

        # Instance the plugin class.
        instance = clazz()

        # Add it to the cache.
        self.__cache[plugin_id] = instance

        # Return the instance.
        return instance


    #--------------------------------------------------------------------------
    def get_plugin_info_from_instance(self, instance):
        """
        Get a plugin's name and information from its already loaded instance.

        :param instance: Plugin instance.
        :type instance: Plugin

        :returns: tuple(str, PluginInfo) -- Plugin ID and information.
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


    #--------------------------------------------------------------------------
    def set_plugin_args(self, plugin_id, plugin_args):
        """
        Set the user-defined values for the given plugin arguments.

        :param plugin_id: Plugin ID.
        :type plugin_id: str

        :param plugin_args: Plugin arguments and their user-defined values.
        :type plugin_args: dict(str -> str)

        :returns: One of the following values:
             - 0: All values set successfully.
             - 1: The plugin was not loaded or does not exist.
             - 2: Some values were not defined for this plugin.
        """
        try:
            plugin_info = self.get_plugin_by_id(plugin_id)
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


    #--------------------------------------------------------------------------
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
        self.__orchestrator = None
        self.__plugins      = None
        self.__cache        = None


#------------------------------------------------------------------------------
class AuditPluginManager (PluginManager):
    """
    Plugin manager for audits.
    """


    #--------------------------------------------------------------------------
    def __init__(self, pluginManager, orchestratorConfig, auditConfig):

        # Superclass constructor.
        super(AuditPluginManager, self).__init__(
            pluginManager.orchestrator)

        # Keep a reference to the plugin manager of the orchestrator.
        self.__pluginManager = pluginManager

        # Batches and stages of plugins (see calculate_dependencies)
        self.__batches = None   # list
        self.__stages  = None   # dict

        # Apply the plugin black and white lists, and all the overrides.
        self._PluginManager__plugins = self.__apply_config(auditConfig)


    #--------------------------------------------------------------------------
    def initialize(self, audit_config):
        """
        Initializes the plugin arguments and disables the plugins that fail the
        parameter checks. Also calculates the dependencies.
        """

        # Set the plugin arguments.
        if audit_config.plugin_args:
            for plugin_id, plugin_args in audit_config.plugin_args.iteritems():
                status = self.set_plugin_args(plugin_id, plugin_args)
                if status == 1:
                    try:
                        self.__pluginManager.get_plugin_by_id(plugin_id)
                    except KeyError:
                        warnings.warn(
                            "Unknown plugin ID: %s" % plugin_id,
                            RuntimeWarning)
                elif status == 2:
                    warnings.warn(
                        "Some arguments undefined for plugin ID: %s" %
                        plugin_id, RuntimeWarning)

        # Check the plugin parameters.
        self.__check_plugin_params(audit_config)

        # Calculate the dependencies.
        self.__calculate_dependencies()


    #--------------------------------------------------------------------------

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
        :returns: Mapping of stage names to plugin IDs for each stage.
        :rtype: dict(str -> set(str))
        """
        return self.__stages


    #--------------------------------------------------------------------------
    def __apply_config(self, auditConfig):
        """
        Apply the black and white lists.
        This controls which plugins are loaded and which aren't.

        :param auditConfig: Audit configuration.
        :type auditConfig: AuditConfig

        :returns: Mapping of the approved plugin IDs to
                  reconfigured instances of PluginInfo.
        :rtype: dict(str -> PluginInfo)

        :raises ValueError: Configuration error.
        :raises KeyError: Configuration error.
        """

        # Check the argument type.
        if not isinstance(auditConfig, AuditConfig):
            raise TypeError(
                "Expected AuditConfig, got %r instead" % type(auditConfig))

        # Get the black and white lists and the plugin load overrides.
        enable_plugins        = auditConfig.enable_plugins
        disable_plugins       = auditConfig.disable_plugins
        plugin_load_overrides = auditConfig.plugin_load_overrides

        # Dumb check.
        if (
            not enable_plugins and
            not disable_plugins and
            not plugin_load_overrides
        ):
            raise ValueError("No plugins selected for audit!")

        # Get all the plugin IDs.
        all_plugins = self.pluginManager.get_plugin_ids()
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
                msg = (
                    "The same entries are present"
                    " in both black and white lists: %s"
                ) % ", ".join(conflicting_entries)
            else:
                msg = (
                    "The same entry (%s) is present"
                    " in both black and white lists"
                ) % conflicting_entries.pop()
            raise ValueError(msg)

        # Expand the black and white lists.
        disable_plugins = self.__expand_plugin_list(
            disable_plugins, "blacklist")
        enable_plugins  = self.__expand_plugin_list(
            enable_plugins,  "whitelist")

        # Apply the black and white lists.
        if blacklist_approach:
            # Use only enabled plugins.
            plugins = all_plugins.intersection(enable_plugins)
        else:
            # Use all but disabled plugins.
            plugins = all_plugins.difference(disable_plugins)

        # Process the plugin load overrides. They only apply to testing
        # plugins. First, find out if there are only enables but no disables.
        # If so, insert a disable command for all testing plugins before the
        # first enable. For all commands, symbolic plugin IDs are replaced
        # with sets of full IDs.
        if plugin_load_overrides:
            only_enables = all(x[0] for x in plugin_load_overrides)
            overrides = []
            if only_enables:
                plugin_load_overrides.insert( 0, (False, "all") )
            for flag, token in plugin_load_overrides:
                token = token.strip().lower()
                if token in ("all", "testing"):
                    names = self.pluginManager.get_plugin_ids("testing")
                    overrides.append( (flag, names) )
                elif token in STAGES:
                    names = self.pluginManager.get_plugin_ids(token)
                    overrides.append( (flag, names) )
                elif token in all_plugins:
                    info = self.pluginManager.get_plugin_by_id(token)
                    if info.category != "testing":
                        raise ValueError("Not a testing plugin: %s" % token)
                    overrides.append( (flag, (token,)) )
                else:
                    if any(c in token for c in "?*["):
                        matching_plugins = self.pluginManager.\
                                                search_plugins_by_mask(token)
                        for name, info in matching_plugins.iteritems():
                            if info.category != "testing":
                                raise ValueError(
                                    "Not a testing plugin: %s" % token)
                            overrides.append( (flag, (name,)) )
                    else:
                        matching_plugins = self.pluginManager.\
                                                search_plugins_by_id(token)
                        if not matching_plugins:
                            raise ValueError("Unknown plugin: %s" % token)
                        if len(matching_plugins) > 1:
                            msg = (
                                "Ambiguous plugin ID %r may refer to any"
                                " of the following plugins: %s"
                            ) % (token,
                              ", ".join(sorted(matching_plugins.iterkeys())))
                            raise ValueError(msg)
                        name, info = matching_plugins.items()[0]
                        if info.category != "testing":
                            raise ValueError(
                                "Not a testing plugin: %s" % token)
                        overrides.append( (flag, (name,)) )

            # Apply the processed plugin load overrides.
            for enable, names in overrides:
                if enable:
                    plugins.update(names)
                else:
                    plugins.difference_update(names)

        # The UI plugins cannot be disabled.
        plugins.update( self.pluginManager.get_plugin_ids("ui") )

        # Return a customized copy of the approved plugins info.
        return {
            name: self.pluginManager[name].customize_for_audit(auditConfig)
            for name in plugins
        }


    #--------------------------------------------------------------------------
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
            plugin_list = self.pluginManager.get_plugin_ids()
        else:

            # Convert categories to plugin IDs.
            for category in CATEGORIES:
                if category in plugin_list:
                    plugin_list.remove(category)
                    plugin_list.update(
                        self.pluginManager.get_plugin_ids(category))

            # Convert stages to plugin IDs.
            for stage in STAGES:
                if stage in plugin_list:
                    plugin_list.remove(stage)
                    plugin_list.update(
                        self.pluginManager.get_plugin_ids(stage))

        # Guess partial plugin IDs in the list.
        # Also make sure all the plugins in the list exist.
        missing_plugins = set()
        all_plugins = self.pluginManager.get_plugin_ids()
        for plugin_id in sorted(plugin_list):
            if plugin_id not in all_plugins:
                matching_plugins = set(
                    self.pluginManager.search_plugins(plugin_id).keys())
                if not matching_plugins:
                    missing_plugins.add(plugin_id)
                    continue
                if len(matching_plugins) > 1 and not "*" in plugin_id:
                    msg = ("Ambiguous entry in %s (%r)"
                           " may refer to any of the following plugins: %s")
                    msg %= (list_name,
                            plugin_id, ", ".join(sorted(matching_plugins)))
                    raise ValueError(msg)
                plugin_list.remove(plugin_id)
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


    #--------------------------------------------------------------------------
    def __calculate_dependencies(self):
        """
        Generate a dependency graph for all plugins found, and calculate
        the batches of plugins that can be run concurrently.

        :raises ValueError: The dependencies are broken.
        """

        # Get all the plugins that support dependencies.
        plugins = self.get_plugins("testing")
        all_plugins = set(plugins.iterkeys())

        # Build the dependency graph, and group plugins by stage.
        # Raise an exception for missing dependencies.
        graph = defaultdict(set)
        stages = defaultdict(set)
        for plugin_id, info in plugins.iteritems():
            stage = info.stage_number
            if not stage or stage < 0:
                stage = 0
            stages[stage].add(plugin_id)
            deps = set(info.dependencies)
            if not deps.issubset(all_plugins):
                msg = "Plugin %s depends on missing plugin(s): %s"
                msg %= (plugin_id,
                        ", ".join(sorted(deps.difference(all_plugins))))
                raise ValueError(msg)
            graph[plugin_id] = deps

        # Add the implicit dependencies defined by the stages into the graph.
        # (We're creating dummy bridge nodes to reduce the number of edges.)
        stage_numbers = sorted(STAGES.itervalues())
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
            ready = {
                plugin_id
                for plugin_id, deps in graph.iteritems()
                if not deps
            }
            if not ready:
                # TODO: find each circle in the graph and show it,
                #       instead of dumping the remaining graph
                msg = "Circular dependencies found in plugins: "
                keys = [
                    k
                    for k in graph.iterkeys()
                    if not k.startswith("*")
                ]
                keys.sort()
                raise ValueError(msg + ", ".join(keys))
            for plugin_id in ready:
                del graph[plugin_id]
            for deps in graph.itervalues():
                deps.difference_update(ready)
            ready = {k for k in ready if not k.startswith("*")}
            if ready:
                batches.append(ready)

        # Store the plugin batches and stages.
        self.__batches = batches
        self.__stages  = stages


    #--------------------------------------------------------------------------
    def __check_plugin_params(self, audit_config):
        """
        Check the plugin parameters.
        Plugins that fail this check are automatically disabled.
        """
        orchestrator = self.orchestrator
        plugins = self.get_plugins("testing")
        for plugin_id in plugins:
            plugin  = self.load_plugin_by_id(plugin_id)
            new_ctx = orchestrator.build_plugin_context(None, plugin, None)
            new_ctx = PluginContext(
                orchestrator_pid = new_ctx._orchestrator_pid,
                orchestrator_tid = new_ctx._orchestrator_tid,
                       msg_queue = new_ctx.msg_queue,
                         address = new_ctx.address,
                    ack_identity = None,
                     plugin_info = self.get_plugin_by_id(plugin_id),
                      audit_name = audit_config.audit_name,
                    audit_config = audit_config,
                     audit_scope = new_ctx.audit_scope,
            )
            old_ctx = Config._context
            try:
                Config._context = new_ctx
                try:
                    plugin.check_params()
                except Exception, e:
                    del self._PluginManager__plugins[plugin_id]
                    err_tb  = traceback.format_exc()
                    err_msg = "Plugin disabled, reason: %s" % str(e)
                    Logger.log_error_verbose(err_msg)
                    Logger.log_error_more_verbose(err_tb)
            finally:
                Config._context = old_ctx


    #--------------------------------------------------------------------------
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


    #--------------------------------------------------------------------------
    def find_plugins(self, plugins_folder = None):
        """
        .. warning: This method is not available for audits.
        """
        raise NotImplementedError("Not available for audits!")


    #--------------------------------------------------------------------------
    def get_plugin_manager_for_audit(self, audit):
        """
        .. warning: This method is not available for audits.
        """
        raise NotImplementedError("Not available for audits!")


    #--------------------------------------------------------------------------
    def load_plugin_by_id(self, plugin_id):

        # Get the plugin info. Fails if the plugin is disabled.
        info = self.get_plugin_by_id(plugin_id)

        # Make the global plugin manager load it, so we can share the cache.
        instance = self.pluginManager.load_plugin_by_id(plugin_id)

        # Fix the classname locally.
        info._fix_classname(instance.__class__.__name__)

        # Return the plugin instance.
        return instance


    #--------------------------------------------------------------------------
    def get_plugin_info_from_instance(self, instance):

        # Get the original PluginInfo from the global plugin manager.
        plugin_id, info = self.pluginManager.get_plugin_info_from_instance(
                                                                  instance)

        # Try getting the customized PluginInfo object.
        # If not found, return the original PluginInfo object.
        try:
            return plugin_id, self.get_plugin_by_id(plugin_id)
        except KeyError:
            return plugin_id, info


    #--------------------------------------------------------------------------
    def close(self):
        try:
            super(AuditPluginManager, self).close()
        finally:
            self.__pluginManager = None
            self.__batches       = None
            self.__stages        = None


#------------------------------------------------------------------------------
class SwitchToAudit(object):
    """
    Context manager that allows UI plugins to run API calls as if they came
    from within an audit. This is useful, for example, to have access to the
    audit database APIs from a UI plugin.

    Example::
        >>> from golismero.api.data.db import Database
        >>> with SwitchToAudit("my_audit"):
        ...     data_ids = Database.keys()
        ...     print "Ok!"
        ...
        Ok!
        >>> try:
        ...     Database.keys()
        ... except Exception:
        ...     print "Error!"
        ...
        Error!
    """

    def __init__(self, audit_name):
        if type(audit_name) is not str:
            raise TypeError("Expected str, got %r instead" % type(audit_name))
        if not audit_name:
            raise ValueError("No audit name provided!")
        self.audit_name = audit_name

    def __enter__(self):

        # Keep the original execution context.
        self.old_context = old_context = Config._context

        # Get the audit name.
        audit_name = self.audit_name

        # Update the execution context for this audit.
        Config._context = PluginContext(
                   msg_queue = old_context.msg_queue,
                     address = old_context.address,
                ack_identity = old_context.ack_identity,
                 plugin_info = old_context.plugin_info,
                  audit_name = audit_name,
                audit_config = get_audit_config(audit_name),
                 audit_scope = get_audit_scope(audit_name),
            orchestrator_pid = old_context._orchestrator_pid,
            orchestrator_tid = old_context._orchestrator_tid)

    def __exit__(self, *args, **kwargs):

        # Restore the original execution context.
        Config._context = self.old_context


#------------------------------------------------------------------------------
class SwitchToPlugin(object):
    """
    Context manager that allows UI plugins to run API calls as if they came
    from within another plugin.

    Example::
        >>> from golismero.api.plugin import get_plugin_name
        >>> with SwitchToPlugin("testing/recon/spider"):
        ...     print get_plugin_name()
        ...
        Web Spider
        >>> print get_plugin_name()
        GoLismero
    """

    def __init__(self, plugin_id, audit_name = None):
        self.plugin_id  = plugin_id
        self.audit_name = audit_name

    def __enter__(self):

        # Keep the original execution context.
        self.old_context = old_context = Config._context

        # Get the plugin information object.
        plugin_info = get_plugin_info(self.plugin_id)

        # If an audit name was given, get the config and scope.
        # Otherwise just copy the existing values.
        audit_name = self.audit_name
        if audit_name:
            audit_config = get_audit_config(audit_name)
            audit_scope  = get_audit_scope(audit_name)
        else:
            audit_config = old_context.audit_config
            audit_scope  = old_context.audit_scope

        # Update the execution context.
        Config._context = PluginContext(
                   msg_queue = old_context.msg_queue,
                     address = old_context.address,
                ack_identity = old_context.ack_identity,
                 plugin_info = plugin_info,
                  audit_name = audit_name,
                audit_config = audit_config,
                 audit_scope = audit_scope,
            orchestrator_pid = old_context._orchestrator_pid,
            orchestrator_tid = old_context._orchestrator_tid)

    def __exit__(self, *args, **kwargs):

        # Restore the original execution context.
        Config._context = self.old_context
