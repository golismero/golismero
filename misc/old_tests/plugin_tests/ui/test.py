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
from golismero.api.data.db import Database
from golismero.api.plugin import UIPlugin
from golismero.main.console import colorize
from golismero.messaging.codes import MessageType, MessageCode, MessagePriority
from golismero.messaging.message import Message

import time
import warnings


#------------------------------------------------------------------------------
class TestUIPlugin(UIPlugin):
    """
    Test UI plugin.
    """


    #--------------------------------------------------------------------------
    def run(self, info):
        if not isinstance(info, Data):
            raise TypeError("Expected Data, got %r instead" % type(info))
        print "-" * 79
        print "ID:   %s" % info.identity
        print "Data: %r" % info
        history = Database.get_plugin_history(info.identity)
        if history:
            print "History:"
            for plugin_id in history:
                print "  " + plugin_id
        print


    #--------------------------------------------------------------------------
    def recv_msg(self, message):
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %r instead" % type(message))

        print "-" * 79
        print "Message:"
        print "  Timestamp: %s" % time.ctime(message.timestamp)
        print "  Audit:     %s" % message.audit_name
        print "  Plugin:    %s" % message.plugin_id
        print "  Type:      %s" % MessageType.get_name_from_value(message.message_type)
        print "  Code:      %s" % MessageCode.get_name_from_value_and_type(message.message_code, message.message_type)
        print "  Priority:  %s" % MessagePriority.get_name_from_value(message.priority)
        print "  Payload:   %r" % (message.message_info,)
        print

        if message.message_type == MessageType.MSG_TYPE_CONTROL:

            if message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT:
                if get_audit_count() == 1:
                    Config._context.send_msg(
                        message_type = MessageType.MSG_TYPE_CONTROL,
                        message_code = MessageCode.MSG_CONTROL_STOP,
                        message_info = True,
                            priority = MessagePriority.MSG_PRIORITY_LOW
                    )

            elif message.message_code == MessageCode.MSG_CONTROL_LOG:
                (text, level, is_error) = message.message_info
                if is_error:
                    print colorize(text, "magenta")
                else:
                    print colorize(text, "cyan")

            elif message.message_code == MessageCode.MSG_CONTROL_ERROR:
                (description, traceback) = message.message_info
                print colorize(description, "magenta")
                print colorize(traceback, "magenta")

            elif message.message_code == MessageCode.MSG_CONTROL_WARNING:
                for w in message.message_info:
                    formatted = warnings.formatwarning(w.message, w.category, w.filename, w.lineno, w.line)
                    print colorize(formatted, "yellow")


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        pass
