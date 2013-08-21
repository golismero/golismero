#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from golismero.api.audit import get_audit_count
from golismero.api.config import Config
from golismero.api.data import Data
from golismero.api.plugin import UIPlugin, get_plugin_info
from golismero.main.console import Console, colorize
from golismero.messaging.codes import MessageType, MessageCode, MessagePriority

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
        self.already_seen_info = set()   # set(str)


    #--------------------------------------------------------------------------
    def check_params(self, options, *audits):
        if not audits:
            raise ValueError("No targets selected!")


    #--------------------------------------------------------------------------
    def recv_info(self, info):

        # Don't print anything if console output is disabled.
        if Console.level < Console.STANDARD:
            return

        # Filter out info we've already seen.
        if info.identity in self.already_seen_info:
            return
        self.already_seen_info.add(info.identity)

        # Print newly discovered vulnerabilities.
        if info.data_type == Data.TYPE_VULNERABILITY:
            text = "%s Vulnerability '%s' dicovered by plugin '%s'. Risk level: %s" % (
                colorize("<!>", info.risk),
                colorize(info.vulnerability_type, info.risk),
                colorize(self.get_plugin_name(info.plugin_id), info.risk),
                colorize(str(info.risk), info.risk)
            )
            Console.display(text)


    #--------------------------------------------------------------------------
    def recv_msg(self, message):

        # Process status messages
        if message.message_type == MessageType.MSG_TYPE_STATUS:

            if message.message_code == MessageCode.MSG_STATUS_PLUGIN_BEGIN:
                m_plugin_name = self.get_plugin_name(message.plugin_name)
                m_plugin_name = colorize(m_plugin_name, "info")
                m_text        = "[*] %s: Started." % m_plugin_name

                Console.display(m_text)

            elif message.message_code == MessageCode.MSG_STATUS_PLUGIN_END:
                m_plugin_name = self.get_plugin_name(message.plugin_name)
                m_plugin_name = colorize(m_plugin_name, "info")
                m_text        = "[*] %s: Finished." % m_plugin_name

                Console.display(m_text)

            elif message.message_code == MessageCode.MSG_STATUS_PLUGIN_STEP:

                if Console.level >= Console.VERBOSE:
                    m_id, m_progress = message.message_info

                    m_plugin_name = self.get_plugin_name(message.plugin_name)
                    m_plugin_name = colorize(m_plugin_name, "info")

                    if m_progress is not None:
                        m_progress_h   = int(m_progress)
                        m_progress_l   = int((m_progress - float(m_progress_h)) * 100)
                        m_progress_txt = colorize("%i.%.2i%%" % (m_progress_h, m_progress_l), "middle")
                        m_progress_txt = m_progress_txt + " percent done..."
                    else:
                        m_progress_txt = "Working..."

                    m_text = "[*] %s: %s" % (m_plugin_name, m_progress_txt)

                    Console.display(m_text)

        # Process control messages
        elif message.message_type == MessageType.MSG_TYPE_CONTROL:

            # When an audit is finished, check if there are more running audits.
            # If there aren't any, stop the Orchestrator.
            if message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT:
                if get_audit_count() == 1:  # this is the last one
                    Config._context.send_msg(  # XXX FIXME hide this from plugins!
                        message_type = MessageType.MSG_TYPE_CONTROL,
                        message_code = MessageCode.MSG_CONTROL_STOP,
                        message_info = True,  # True for finished, False for user cancel
                            priority = MessagePriority.MSG_PRIORITY_LOW
                    )

            # Show log messages
            # (The verbosity is sent by Logger)
            elif message.message_code == MessageCode.MSG_CONTROL_LOG:
                (text, level, is_error) = message.message_info
                if Console.level >= level:
                    try:
                        m_plugin_name = self.get_plugin_name(message.plugin_name)
                    except Exception:
                        m_plugin_name = "GoLismero"
                    m_plugin_name = colorize(m_plugin_name, 'info')
                    text = colorize(text, 'middle')
                    if is_error:
                        text = "[!] %s: %s" % (m_plugin_name, text)
                        Console.display_error(text)
                    else:
                        text = "[*] %s: %s" % (m_plugin_name, text)
                        Console.display(text)

            # Show plugin errors
            # (Only the description in standard level,
            # full traceback in more verbose level)
            if message.message_code == MessageCode.MSG_CONTROL_ERROR:
                (description, traceback) = message.message_info
                try:
                    m_plugin_name = self.get_plugin_name(message.plugin_name)
                except Exception:
                    m_plugin_name = "GoLismero"
                text        = "[!] Plugin '%s' error: %s " % (m_plugin_name, str(description))
                text        = colorize(text, 'critical')
                traceback   = colorize(traceback, 'critical')
                Console.display_error(text)
                Console.display_error_more_verbose(traceback)

            # Show plugin warnings
            # (Only the description in verbose level,
            # full traceback in more verbose level)
            elif message.message_code == MessageCode.MSG_CONTROL_WARNING:
                for w in message.message_info:
                    if Console.level >= Console.MORE_VERBOSE:
                        formatted = warnings.formatwarning(w.message, w.category, w.filename, w.lineno, w.line)
                    elif Console.level >= Console.VERBOSE:
                        formatted = w.message
                    else:
                        formatted = None
                    if formatted:
                        m_plugin_name = self.get_plugin_name(message.plugin_name)
                        text = "[!] Plugin '%s' warning: %s " % (m_plugin_name, str(formatted))
                        text = colorize(text, 'low')
                        Console.display_error(text)


    #--------------------------------------------------------------------------
    @staticmethod
    def get_plugin_name(plugin_name):
        if plugin_name:
            return get_plugin_info(plugin_name).display_name
        return "GoLismero"
