#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager of external results import plugins.
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

__all__ = ["ImportManager"]

from ..api.config import Config
from ..api.logger import Logger

from traceback import format_exc


#------------------------------------------------------------------------------
class ImportManager (object):
    """
    Manager of external results importer plugins.
    """


    #----------------------------------------------------------------------
    def __init__(self, orchestrator, audit):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator

        :param audit: Audit instance.
        :type audit: Audit
        """

        # Keep a reference to the audit configuration.
        self.__config = audit.config

        # Keep a reference to the Orchestrator.
        self.__orchestrator = orchestrator

        # Load the import plugins.
        self.__plugins = audit.pluginManager.load_plugins("import")

        # Map import plugins to input files.
        self.__importers = {}
        for input_file in self.__config.imports:
            if input_file in self.__importers:
                continue
            found = [name for name, plugin in self.__plugins.iteritems()
                          if plugin.is_supported(input_file)]
            if not found:
                raise ValueError(
                    "Input file format not supported: %r" % input_file)
            if len(found) > 1:
                msg = "Input file format supported by multiple plugins!\nFile: %r\nPlugins:\n\t"
                msg %= input_file
                msg += "\n\t".join(found)
                raise ValueError(msg)
            self.__importers[input_file] = found[0]


    #----------------------------------------------------------------------

    @property
    def config(self):
        """
        :returns: Audit configuration.
        :rtype: AuditConfig.
        """
        return self.__config

    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__orchestrator

    @property
    def plugin_count(self):
        """
        :returns: Number of import plugins loaded.
        :rtype: int
        """
        return len(self.__importers)


    #----------------------------------------------------------------------
    def import_results(self):
        """
        Import all the requested results before running an audit.

        :returns: Number of plugins executed.
        :rtype: int
        """

        # Abort if importing is disabled.
        if not self.__importers:
            return 0

        # Show a log message.
        Logger.log_verbose("Importing results from external tools...")

        # For each input file, run its corresponding import plugin.
        # Import plugins are run in the same process as the Orchestrator.
        count = 0
        for input_file, plugin_id in self.__importers.iteritems():
            try:
                plugin_instance = self.__plugins[plugin_id]
                context = self.orchestrator.build_plugin_context(
                    self.config.audit_name, plugin_instance, None
                )
                old_context = Config._context
                try:
                    Config._context = context
                    plugin_instance.import_results(input_file)
                finally:
                    Config._context = old_context
            except Exception, e:
                Logger.log_error("Failed to import results from file %r: %s" % (input_file, str(e)))
                Logger.log_error_more_verbose(format_exc())
            count += 1
        return count


    #----------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this manager.
        """
        self.__config       = None
        self.__orchestrator = None
        self.__plugins      = None
        self.__importers    = None
