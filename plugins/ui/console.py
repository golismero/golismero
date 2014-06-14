#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from golismero.api.audit import get_audit_count
from golismero.api.config import Config
from golismero.api.data import Data
from golismero.api.plugin import UIPlugin, get_plugin_info, \
    get_stage_display_name
from golismero.main.console import Console, colorize, colorize_traceback
from golismero.messaging.codes import MessageType, MessageCode, MessagePriority

from collections import defaultdict
from functools import partial

import warnings

#
# Verbosity levels:
#
# Disabled: No output
# Standard: Disabled + errors without traceback
# Verbose: Standard + urls, important actions of plugins
# More verbose: Verbose + errors with tracebacks, unimportant actions of plugins
#


#------------------------------------------------------------------------------
class ConsoleUIPlugin(UIPlugin):
    """
    This is the console UI plugin. It provides a simple interface
    to work with GoLismero from the command line.

    This plugin has no options.
    """


    #--------------------------------------------------------------------------
    def __init__(self):

        # audit_name -> set(identity)
        self.already_seen_info = defaultdict(set)

        # audit_name -> plugin_name -> ack_identity -> simple_id
        self.current_plugins = defaultdict( partial(defaultdict, dict) )


    #--------------------------------------------------------------------------
    def check_params(self, options, *audits):
        if not audits:
            raise ValueError("Daemon mode not supported.")
        for audit in audits:
            if (
                audit.is_new_audit() and
                not audit.targets and
                not audit.imports
            ):
                raise ValueError("No targets selected for audit.")


    #--------------------------------------------------------------------------
    def run(self, info):

        # Don't print anything if console output is disabled.
        if Console.level < Console.MINIMAL:
            return

        # Ignore everything but vulnerabilities.
        if info.data_type != Data.TYPE_VULNERABILITY:
            return

        # Filter out info we've already seen.
        if info.identity in self.already_seen_info[Config.audit_name]:
            return
        self.already_seen_info[Config.audit_name].add(info.identity)

        # Print newly discovered vulnerabilities.
        text = "<!> %s vulnerability dicovered by %s. Level: %s"
        text %= (
            colorize(info.display_name, info.level),
            colorize(self.get_plugin_name(info.plugin_id, None), "blue"),
            colorize(info.level, info.level)
        )
        Console.display(text)


    #--------------------------------------------------------------------------
    def recv_msg(self, message):

        # Process status messages.
        if message.message_type == MessageType.MSG_TYPE_STATUS:

            # A plugin has started.
            if message.message_code == MessageCode.MSG_STATUS_PLUGIN_BEGIN:

                # Create a simple ID for the plugin execution.
                id_dict = self.current_plugins[Config.audit_name][message.plugin_id]
                simple_id = len(id_dict)
                id_dict[message.ack_identity] = simple_id

                # Show this event in extra verbose mode.
                if Console.level >= Console.MORE_VERBOSE:

                    # Show a message to the user.
                    m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                    m_plugin_name = colorize("[*] " + m_plugin_name, "informational")
                    m_text        = "%s: Started." % m_plugin_name
                    Console.display(m_text)

            # A plugin has ended.
            elif message.message_code == MessageCode.MSG_STATUS_PLUGIN_END:

                # Show this event in extra verbose mode.
                if Console.level >= Console.MORE_VERBOSE:

                    # Show a message to the user.
                    m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                    m_plugin_name = colorize("[*] " + m_plugin_name, "informational")
                    m_text        = "%s: Finished." % m_plugin_name
                    Console.display(m_text)

                # Free the simple ID for the plugin execution.
                try:
                    del self.current_plugins[Config.audit_name][message.plugin_id][message.ack_identity]
                except KeyError:
                    pass

            # A plugin has advanced.
            elif message.message_code == MessageCode.MSG_STATUS_PLUGIN_STEP:

                # Show this event in verbose mode.
                if Console.level >= Console.VERBOSE:

                    # Get the plugin name.
                    m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                    m_plugin_name = colorize("[*] " + m_plugin_name, "informational")

                    # Get the progress percentage.
                    m_progress = message.message_info
                    if m_progress is not None:
                        m_progress_h   = int(m_progress)
                        m_progress_l   = int((m_progress - float(m_progress_h)) * 100)
                        m_progress_txt = colorize("%i.%.2i%%" % (m_progress_h, m_progress_l), "middle")
                        m_progress_txt = m_progress_txt + " percent done..."
                    else:
                        m_progress_txt = "Working..."

                    # Show it to the user.
                    m_text = "%s: %s" % (m_plugin_name, m_progress_txt)
                    Console.display(m_text)

            # The audit has moved to another execution stage.
            elif message.message_code == MessageCode.MSG_STATUS_STAGE_UPDATE:

                # Show this event in verbose mode.
                if Console.level >= Console.VERBOSE:

                    # Show the new stage name.
                    m_stage = get_stage_display_name(message.message_info)
                    m_stage = colorize(m_stage, "high")
                    m_plugin_name = colorize("[*] GoLismero", "informational")
                    m_text = "%s: Current stage: %s"
                    m_text %= (m_plugin_name, m_stage)
                    Console.display(m_text)

                    # If on maximum verbosity level and entering report stage,
                    # log the current report mode.
                    if (
                        Console.level >= Console.MORE_VERBOSE and
                        message.message_info == "report"
                    ):
                        if Config.audit_config.only_vulns:
                            m_report_type = "Brief"
                        else:
                            m_report_type = "Full"
                        m_report_type = colorize(m_report_type, "yellow")
                        m_text = "%s: Report type: %s"
                        m_text %= (m_plugin_name, m_report_type)
                        Console.display(m_text)

            # When an audit is aborted, check if there are more running audits.
            # If there aren't any, stop the Orchestrator.
            elif message.message_code == MessageCode.MSG_STATUS_AUDIT_ABORTED:
                (audit_name, description, traceback) = message.message_info
                try:
                    m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                    m_plugin_name = colorize("[!] " + m_plugin_name, 'critical')
                    text      = "%s: Error: %s " % (m_plugin_name, str(description))
                    traceback = colorize(traceback, 'critical')
                    Console.display_error(text)
                    Console.display_error_more_verbose(traceback)
                finally:
                    self.audit_is_dead(audit_name)

        # Process control messages.
        elif message.message_type == MessageType.MSG_TYPE_CONTROL:

            # When an audit is finished, check if there are more running audits.
            # If there aren't any, stop the Orchestrator.
            if message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT:
                self.audit_is_dead(message.audit_name)

            # Show log messages. The verbosity is sent by Logger.
            elif message.message_code == MessageCode.MSG_CONTROL_LOG:
                (text, level, is_error) = message.message_info
                if Console.level >= level:
                    m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                    if is_error:
                        text = colorize_traceback(text)
                        m_plugin_name = colorize("[!] " + m_plugin_name, 'critical')
                        text = "%s: %s" % (m_plugin_name, text)
                        Console.display_error(text)
                    else:
                        m_plugin_name = colorize("[*] " + m_plugin_name, 'informational')
                        text = "%s: %s" % (m_plugin_name, text)
                        Console.display(text)

            # Show plugin errors.
            # Only the description in standard level,
            # full traceback in more verbose level.
            if message.message_code == MessageCode.MSG_CONTROL_ERROR:
                (description, traceback) = message.message_info
                m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                m_plugin_name = colorize("[!] " + m_plugin_name, 'critical')
                text = "%s: Error: %s " % (m_plugin_name, str(description))
                traceback = colorize_traceback(traceback)
                Console.display_error(text)
                Console.display_error_more_verbose(traceback)

            # Show plugin warnings.
            # Only in more verbose level.
            elif message.message_code == MessageCode.MSG_CONTROL_WARNING:
                for w in message.message_info:
                    if Console.level >= Console.MORE_VERBOSE:
                        formatted = warnings.formatwarning(w.message, w.category, w.filename, w.lineno, w.line)
                        m_plugin_name = self.get_plugin_name(message.plugin_id, message.ack_identity)
                        m_plugin_name = colorize("[!] " + m_plugin_name, 'low')
                        text = "%s: Error: %s " % (m_plugin_name, str(formatted))
                        Console.display_error(text)


    #--------------------------------------------------------------------------
    def audit_is_dead(self, audit_name):
        try:
            del self.already_seen_info[audit_name]
        except KeyError:
            pass # may happen when only generating reports
        try:
            del self.current_plugins[audit_name]
        except KeyError:
            pass
        if get_audit_count() <= 1:  # this is the last one
            Config._context.send_msg(  # XXX FIXME hide this from plugins!
                message_type = MessageType.MSG_TYPE_CONTROL,
                message_code = MessageCode.MSG_CONTROL_STOP,
                message_info = True,  # True for finished, False for user cancel
                    priority = MessagePriority.MSG_PRIORITY_LOW,
            )


    #--------------------------------------------------------------------------
    def get_plugin_name(self, plugin_id, ack_identity):

        # If the message comes from the Orchestrator.
        if not plugin_id:
            return "GoLismero"

        # If the message is for us, just return our name.
        if plugin_id == Config.plugin_id:
            return Config.plugin_info.display_name

        # Get the plugin display name.
        plugin_name = get_plugin_info(plugin_id).display_name

        # Append the simple ID if it's greater than zero.
        if ack_identity:
            simple_id = self.current_plugins[Config.audit_name][plugin_id].get(ack_identity)
            if simple_id:
                plugin_name = "%s (%d)" % (plugin_name, simple_id + 1)

        # Return the display name.
        return plugin_name
