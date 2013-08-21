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
from golismero.api.plugin import UIPlugin
from golismero.messaging.codes import MessageType, MessageCode, MessagePriority


#------------------------------------------------------------------------------
class DisabledUIPlugin(UIPlugin):
    """
    This plugin acts as a dummy user interface that does nothing.
    """


    #--------------------------------------------------------------------------
    def check_params(self, options, *audits):
        if not audits:
            raise ValueError("No targets selected!")


    #--------------------------------------------------------------------------
    def get_accepted_info(self):
        return []


    #--------------------------------------------------------------------------
    def recv_info(self, info):
        pass


    #--------------------------------------------------------------------------
    def recv_msg(self, message):

        # When an audit is finished, check if there are more running audits.
        # If there aren't any, stop the Orchestrator.
        if (
            message.message_type == MessageType.MSG_TYPE_CONTROL and
            message.message_code == MessageCode.MSG_CONTROL_STOP_AUDIT and
            get_audit_count() == 1
        ):
            Config._context.send_msg(  # XXX FIXME hide this from plugins!
                message_type = MessageType.MSG_TYPE_CONTROL,
                message_code = MessageCode.MSG_CONTROL_STOP,
                message_info = True,  # True for finished, False for user cancel
                    priority = MessagePriority.MSG_PRIORITY_LOW
            )
