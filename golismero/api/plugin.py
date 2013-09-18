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
    "get_plugin_info", "get_plugin_ids", "get_plugin_name",
    "PluginState",
]

from .config import Config
from .progress import Progress
from .shared import SharedMap
from ..messaging.codes import MessageCode


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

    PLUGIN_TYPE_FIRST = PLUGIN_TYPE_TESTING
    PLUGIN_TYPE_LAST  = PLUGIN_TYPE_REPORT

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
        if progress:
            self.progress.set_percent(progress)


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
