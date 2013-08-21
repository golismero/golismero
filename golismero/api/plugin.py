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

__all__ = [
    "UIPlugin", "ImportPlugin", "TestingPlugin", "ReportPlugin",
    "get_plugin_info", "get_plugin_names", "PluginState",
]

from .config import Config
from .shared import check_value
from ..messaging.codes import MessageCode

# Sentinel value.
_sentinel = object()


#------------------------------------------------------------------------------
def get_plugin_names():
    """
    Get the plugin names.

    :returns: Plugin names.
    :rtype: set(str)
    """
    return Config._context.remote_call(MessageCode.MSG_RPC_PLUGIN_GET_NAMES)


#------------------------------------------------------------------------------
def get_plugin_info(plugin_name = None):
    """
    Get the plugin information for the requested plugin.

    :param plugin_name: Full plugin name.
        Example: "testing/recon/spider".
        Defaults to the calling plugin name.
    :type plugin_name: str

    :returns: Plugin information.
    :rtype: PluginInfo

    :raises KeyError: The plugin was not found.
    """
    if not plugin_name or (Config.plugin_info and plugin_name == Config.plugin_name):
        return Config.plugin_info
    return Config._context.remote_call(
        MessageCode.MSG_RPC_PLUGIN_GET_INFO, plugin_name)


#------------------------------------------------------------------------------
class PluginState (object):
    """
    Container of plugin state variables.

    State variables are stored in the audit database.
    That way plugins can maintain state regardless of which process
    (or machine!) is running them at any given point in time.
    """


    #--------------------------------------------------------------------------
    def __init__(self, plugin_name = None):
        """
        :param plugin_name: Plugin name.
            If ommitted, the calling plugin state variables are accessed.
        :type plugin_name: str
        """
        if not plugin_name:
            plugin_name = Config.plugin_name
        self.__plugin_name = plugin_name


    #--------------------------------------------------------------------------
    @property
    def plugin_name(self):
        """
        :returns: Name of the plugin these state variables belong to.
        :rtype: str
        """
        return self.__plugin_name


    #--------------------------------------------------------------------------
    def get(self, name, default = _sentinel):
        """
        Get the value of a state variable.

        :param name: Name of the variable.
        :type name: str

        :param default: Optional default value. If set, when the name
                        is not found the default is returned instead
                        of raising KeyError.
        :type default: \\*

        :returns: Value of the variable.
        :rtype: \\*

        :raises KeyError: The variable was not defined.
        """
        if not type(name) in (str, unicode):
            raise TypeError("Expected str or unicode, got %s instead" % type(name))
        try:
            return Config._context.remote_call(
                MessageCode.MSG_RPC_STATE_GET, self.plugin_name, name)
        except KeyError:
            if default is not _sentinel:
                return default
            raise


    #--------------------------------------------------------------------------
    def check(self, name):
        """
        Check if a state variable has been defined.

        .. warning: Due to the asynchronous nature of GoLismero plugins, it's
            possible that another instance of the plugin may remove or add new
            variables right after you call this method.

            Therefore this pattern is NOT recommended:
                myvar = None
                if "myvar" in self.state:
                    myvar = self.state["myvar"]

            You should do this instead:
                try:
                    myvar = self.state["myvar"]
                except KeyError:
                    myvar = None

        :param name: Name of the variable to test.
        :type name: str

        :returns: True if the variable was defined, False otherwise.
        :rtype: bool
        """
        if not type(name) in (str, unicode):
            raise TypeError("Expected str or unicode, got %s instead" % type(name))
        return Config._context.remote_call(
            MessageCode.MSG_RPC_STATE_CHECK, self.plugin_name, name)


    #--------------------------------------------------------------------------
    def set(self, name, value):
        """
        Set the value of a state variable.

        :param name: Name of the variable.
        :type name: str

        :param value: Value of the variable.
        :type value: \\*
        """
        if not type(name) in (str, unicode):
            raise TypeError("Expected str or unicode, got %s instead" % type(name))
        check_value(value)
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_STATE_ADD, self.plugin_name, name, value)


    #--------------------------------------------------------------------------
    def remove(self, name):
        """
        Remove a state variable.

        :param name: Name of the variable.
        :type name: str

        :raises KeyError: The variable was not defined.
        """
        if not type(name) in (str, unicode):
            raise TypeError("Expected str or unicode, got %s instead" % type(name))
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_STATE_REMOVE, self.plugin_name, name)


    #--------------------------------------------------------------------------
    def get_names(self):
        """
        Get the names of the defined state variables.

        .. warning: Due to the asynchronous nature of GoLismero plugins, it's
            possible the list of variables is not accurate - another instance
            of the plugin may remove or add new variables right after you call
            this method.

            Therefore this pattern is NOT recommended::
                myvar = None
                if "myvar" in self.state.get_names():
                    myvar = self.state["myvar"]      # wrong!

            You should do this instead::
                try:
                    myvar = self.state["myvar"]
                except KeyError:                     # right!
                    myvar = None

            This pattern is also WRONG: it would fail if a key is removed,
            and would miss newly created keys::
                data = {}
                for key in self.state.get_names():
                    data[key] = self.state.get(key)  # wrong!

        :returns: Names of the defined state variables.
        :rtype: set(str)
        """
        Config._context.async_remote_call(
            MessageCode.MSG_RPC_STATE_KEYS, self.plugin_name)


    #--------------------------------------------------------------------------
    # Overloaded operators.

    def __getitem__(self, name):
        'x.__getitem__(y) <==> x[y]'
        return self.get(name)

    def __setitem__(self, name, value):
        'x.__setitem__(i, y) <==> x[i]=y'
        return self.set(name, value)

    def __delitem__(self, name):
        'x.__delitem__(y) <==> del x[y]'
        return self.remove(name)

    def __contains__(self, name):
        'D.__contains__(k) -> True if D has a key k, else False'
        return self.check(name)

    def keys(self):
        "D.keys() -> list of D's keys"
        return list( self.get_names() )


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

    PLUGIN_TYPE_FIRST = PLUGIN_TYPE_TESTING
    PLUGIN_TYPE_LAST  = PLUGIN_TYPE_REPORT

    PLUGIN_TYPE = PLUGIN_TYPE_ABSTRACT


    #--------------------------------------------------------------------------
    @property
    def state(self):
        """
        :returns: Shared plugin state variables.
        :rtype: PluginState
        """
        return PluginState()


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
        Config._context.send_status(progress)


#------------------------------------------------------------------------------
class _InformationPlugin (Plugin):
    """
    Information plugins are the ones that receive information, and may also
    send it back. Thus they can form feedback loops among each other.

    .. warning: This is an abstract class, do not use it!
    """


    #--------------------------------------------------------------------------
    def recv_info(self, info):
        """
        Callback method to receive data to be processed.

        This is the most important method of a plugin.
        Here's where most of the logic resides.

        :param info: Data to be processed.
        :type info: Data
        """
        raise NotImplementedError("Plugins must implement this method!")


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        """
        Return a list of constants describing
        which data types are accepted by the recv_info method.

        :returns: Data type constants.
        :rtype: list
        """
        raise NotImplementedError("Plugins must implement this method!")


#------------------------------------------------------------------------------
class UIPlugin (_InformationPlugin):
    """
    User Interface plugins control the way in which the user interacts with GoLismero.

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
    def get_accepted_info(self):
        return None               # Most UI plugins will want all data objects.


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

        Tipically, here is where Report plugins examine the file extension.

        :param output_file: Output file to generate.
        :type output_file: str

        :returns: True if this plugin supports the format, False otherwise.
        :rtype: bool
        """
        raise NotImplementedError("Plugins must implement this method!")


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
