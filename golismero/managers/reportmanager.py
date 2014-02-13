#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manager of reports generation.
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

__all__ = ["ReportManager"]

from ..api.logger import Logger

from traceback import format_exc


#------------------------------------------------------------------------------
class ReportManager (object):
    """
    Manager of reports generation.
    """


    #--------------------------------------------------------------------------
    def __init__(self, orchestrator, audit):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator

        :param audit: Audit instance.
        :type audit: Audit
        """

        # Keep a reference to the audit name.
        self.__audit_name = audit.name

        # Keep a reference to the audit configuration.
        self.__config = audit.config

        # Keep a reference to the Orchestrator.
        self.__orchestrator = orchestrator

        # Load the report plugins.
        self.__plugins = audit.pluginManager.load_plugins("report")

        # Map report plugins to output files.
        self.__reporters = {}
        for output_file in self.__config.reports:
            if output_file in self.__reporters:
                continue
            found = [name for name, plugin in self.__plugins.iteritems()
                          if plugin.is_supported(output_file)]
            if not found:
                raise ValueError(
                    "Output file format not supported: %r" % output_file)
            if len(found) > 1:
                msg = (
                    "Output file format supported by multiple plugins!\n"
                    "File: %r\nPlugins:\n\t"
                ) % output_file
                msg += "\n\t".join(found)
                raise ValueError(msg)
            self.__reporters[output_file] = found[0]


    #--------------------------------------------------------------------------

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
        :returns: Number of report plugins loaded.
        :rtype: int
        """
        return len(self.__reporters)


    #--------------------------------------------------------------------------
    def generate_reports(self, notifier):
        """
        Generate all the requested reports for the audit.

        :param notifier: Plugin notifier.
        :type notifier: AuditNotifier

        :returns: Number of plugins executed.
        :rtype: int
        """

        # Abort if reporting is disabled.
        if not self.__reporters:
            return 0

        # For each output file, run its corresponding report plugin.
        # Skip the magic plugin for screen reports.
        count = 0
        for output_file, plugin_id in self.__reporters.iteritems():
            if (
                plugin_id == "report/text" and
                (not output_file or output_file == "-")
            ):
                continue
            try:
                notifier.start_report(self.__plugins[plugin_id], output_file)
            except Exception, e:
                Logger.log_error(
                    "Failed to generate report for file %r: %s" %
                    (output_file, str(e)))
                Logger.log_error_more_verbose(format_exc())
            count += 1
        return count


    #--------------------------------------------------------------------------
    def generate_screen_report(self, notifier):
        """
        Generate the screen report for the audit, if enabled.

        :param notifier: Plugin notifier.
        :type notifier: AuditNotifier

        :returns: Number of plugins executed.
        :rtype: int
        """

        # Abort if reporting is disabled.
        if not self.__reporters:
            return 0

        # Abort if the text report plugin is not selected.
        if "report/text" not in self.__reporters.values():
            return 0

        # Get the filename for the screen report plugin.
        # Skip if the filename is real, instead of the dummy
        # filename used to indicate we want console output.
        found = False
        for output_file, plugin_id in self.__reporters.iteritems():
            if (
                plugin_id == "report/text" and
                (not output_file or output_file == "-")
            ):
                found = True
                break
        if not found:
            return 0

        # Run the text report plugin.
        try:
            notifier.start_report(
                self.__plugins[plugin_id], self.__audit_name, output_file)
        except Exception, e:
            Logger.log_error("Failed to run screen report: %s" % str(e))
            Logger.log_error_more_verbose(format_exc())
        return 1


    #--------------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this manager.
        """
        self.__config       = None
        self.__orchestrator = None
        self.__plugins      = None
        self.__reporters    = None
