#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A rudimentary testing bootstrap.
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

__all__ = ["PluginTester"]

from .launcher import _sanitize_config
from .orchestrator import Orchestrator
from .scope import AuditScope, DummyScope
from ..api.data import Data, LocalDataCache
from ..api.config import Config
from ..api.file import FileManager
from ..api.net.cache import NetworkCache
from ..api.net.http import HTTP
from ..common import OrchestratorConfig
from ..database.auditdb import AuditDB
from ..managers.auditmanager import Audit
from ..managers.processmanager import PluginContext
from ..messaging.message import Message

from os import getpid, unlink
from thread import get_ident


#------------------------------------------------------------------------------
class PluginTester(object):
    """
    Setup a mock environment to test plugins.

    Example:
        >>> from golismero.api.data.resource.url import BaseUrl
        >>> from golismero.main.testing import PluginTester
        >>> with PluginTester() as t:
        ...    u = BaseUrl("http://www.example.com/")
        ...    print t.run_plugin("testing/recon/robots", u)
        ...
        [<BaseUrl url='http://www.example.com/'>]

    Another example (with a scope):
        >>> from golismero.api.data.resource.url import BaseUrl
        >>> from golismero.main.testing import PluginTester
        >>> with PluginTester(autoinit=False) as t:
        ...    t.audit_config.targets = ["http://www.example.com/"]
        ...    t.init_environment()
        ...    u = BaseUrl("http://www.example.com/")
        ...    print t.run_plugin("testing/recon/robots", u)
        ...
        [<BaseUrl url='http://www.example.com/'>]

    Yet another way of doing it:
        >>> from golismero.api.data.resource.url import BaseUrl
        >>> from golismero.common import AuditConfig
        >>> from golismero.main.testing import PluginTester
        >>> cfg = AuditConfig()
        >>> cfg.targets = ["http://www.example.com/"]
        >>> with PluginTester(audit_config = cfg) as t:
        ...    u = BaseUrl("http://www.example.com/")
        ...    print t.run_plugin("testing/recon/robots", u)
        ...
        [<BaseUrl url='http://www.example.com/'>]
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator_config = None, audit_config = None,
                 autoinit = True):
        """
        :param orchestrator_config: Optional orchestrator configuration.
        :type orchestrator_config: OrchestratorConfig

        :param audit_config: Optional audit configuration.
        :type audit_config: AuditConfig

        :param autoinit: True to initialize the environment automatically,
            False otherwise. If set to False you need to call the
            init_environment() method manually.
        :type autoinit: bool
        """

        # Sanitize the config.
        if orchestrator_config is None:
            orchestrator_config = OrchestratorConfig()
            orchestrator_config.targets = ["http://www.example.com/"]
        orchestrator_config, (audit_config,) = \
            _sanitize_config(orchestrator_config, (audit_config,))

        # Save the config.
        self.__orchestrator_config = orchestrator_config
        self.__audit_config = audit_config

        # Here's where the Orchestrator and Audit instances are stored.
        self.__orchestrator = None
        self.__audit = None

        # Initialize the environment if requested.
        if autoinit:
            self.init_environment()


    #--------------------------------------------------------------------------
    def __enter__(self):
        return self
    def __exit__(self, type, value, tb):
        self.cleanup()


    #--------------------------------------------------------------------------
    @property
    def orchestrator(self):
        return self.__orchestrator

    @property
    def audit(self):
        return self.__audit

    @property
    def orchestrator_config(self):
        return self.__orchestrator_config

    @property
    def audit_config(self):
        return self.__audit_config


    #--------------------------------------------------------------------------
    def init_environment(self):

        # Do nothing if the environment has already been initialized.
        if self.audit is not None:
            return

        # Instance the Orchestrator.
        orchestrator = Orchestrator(self.orchestrator_config)

        # Instance an Audit.
        audit = Audit(self.audit_config, orchestrator)

        # Create the audit database.
        audit._Audit__database = AuditDB(self.audit_config)

        # Calculate the audit scope.
        if self.audit_config.targets:
            audit_scope = AuditScope(self.audit_config)
        else:
            audit_scope = DummyScope()
        audit._Audit__audit_scope = audit_scope

        # Create the audit plugin manager.
        plugin_manager = orchestrator.pluginManager.get_plugin_manager_for_audit(audit)
        audit._Audit__plugin_manager = plugin_manager

        # Load all the plugins.
        plugins = plugin_manager.load_plugins()
        if not plugins:
            raise RuntimeError("Failed to find any plugins!")

        # Get the audit name.
        audit_name = self.audit_config.audit_name

        # Register the Audit with the AuditManager.
        orchestrator.auditManager._AuditManager__audits[audit_name] = audit

        # Setup a local plugin execution context.
        Config._context  = PluginContext(
            orchestrator_pid = getpid(),
            orchestrator_tid = get_ident(),
                   msg_queue = orchestrator._Orchestrator__queue,
                audit_name   = audit_name,
                audit_config = self.audit_config,
                audit_scope  = audit_scope,
        )

        # Initialize the environment.
        HTTP._initialize()
        NetworkCache._clear_local_cache()
        FileManager._update_plugin_path()
        LocalDataCache._enabled = True  # force enable
        LocalDataCache.on_run()
        LocalDataCache._enabled = True  # force enable

        # Save the Orchestrator and Audit instances.
        self.__orchestrator = orchestrator
        self.__audit = audit


    #--------------------------------------------------------------------------
    def get_plugin(self, plugin_name):
        """
        Get an instance of the requested plugin.

        :param plugin_name: Name of the plugin to test.
        :type plugin_name: str

        :returns: Plugin instance and information.
        :rtype: tuple(Plugin, PluginInfo)
        """

        # Make sure the environment is initialized.
        self.init_environment()

        # Load the plugin.
        plugin_info = self.audit.pluginManager.get_plugin_by_name(plugin_name)
        plugin = self.audit.pluginManager.load_plugin_by_name(plugin_name)
        return plugin, plugin_info


    #--------------------------------------------------------------------------
    def run_plugin(self, plugin_name, plugin_input):
        """
        Run the requested plugin. You can test both data and messages.

        It's the caller's resposibility to check the input message queue of
        the Orchestrator instance if the plugin sends any messages.

        :param plugin_name: Name of the plugin to test.
        :type plugin_name: str

        :param plugin_input: Plugin input.
            Testing plugins accept Data objects, Import and Report plugins
            accept filenames, and UI plugins accept both Data and Message.
        :type plugin_input: str | Data | Message

        :returns: Return value from the plugin.
        :rtype: \\*
        """

        # Load the plugin.
        # The name MUST be the full ID. This is intentional.
        plugin, plugin_info = self.get_plugin(plugin_name)
        Config._context._PluginContext__plugin_info = plugin_info

        try:

            # Initialize the environment.
            HTTP._initialize()
            NetworkCache._clear_local_cache()
            FileManager._update_plugin_path()
            LocalDataCache.on_run()

            # If it's a message, send it and return.
            if isinstance(plugin_input, Message):
                return plugin.recv_msg(plugin_input)

            # If it's data....
            if isinstance(plugin_input, Data):
                data = plugin_input

                # If the data is out of scope, don't run the plugin.
                if not data.is_in_scope():
                    return []

                # Make sure the plugin can actually process this type of data.
                # Raise an exception if it doesn't.
                found = False
                for clazz in plugin.get_accepted_info():
                    if isinstance(data, clazz):
                        found = True
                        break
                if not found:
                    msg = "Plugin %s cannot process data of type %s"
                    raise TypeError(msg % (plugin_name, type(data)))

                # Call the plugin.
                result = plugin.recv_info(data)

                # Process the results.
                result = LocalDataCache.on_finish(result)

                # If the input data was not returned, make sure to add it.
                if data not in result:
                    result.insert(0, data)

                # Return the results.
                return result

            # If it's not a string, we have a type error.
            if not type(plugin_input) is str:
                raise TypeError(
                    "Cannot process input of type: %s" % type(plugin_input))

            # It's a filename.
            filename = plugin_input

            # If it's an import plugin...
            if plugin_info.category == "import":

                # Call the import method.
                plugin.import_results(filename)

            # If it's a report plugin...
            elif plugin_info.category == "report":

                # Call the report method.
                plugin.generate_report(filename)

            # If it's another plugin type, it's an error.
            else:
                raise TypeError(
                    "Plugins of category %s cannot process filenames."
                    % plugin_info.category)

        finally:

            # Unload the plugin.
            Config._context._PluginContext__plugin_info = None


    #--------------------------------------------------------------------------
    def cleanup(self):
        """
        Cleanup the mock environment.
        """

        FileManager._update_plugin_path()
        NetworkCache._clear_local_cache()
        LocalDataCache.on_run()
        HTTP._finalize()

        try:
            filename = self.audit.database.filename
        except AttributeError:
            filename = None

        if self.orchestrator is not None:
            self.orchestrator.close()

        self.__audit = None
        self.__orchestrator = None

        if filename:
            try:
                unlink(filename)
            except IOError:
                pass
