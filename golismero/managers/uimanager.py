#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dispatcher of messages for the UI plugins.
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

__all__ = ["UIManager"]

from ..messaging.codes import MessageType, MessageCode
from ..messaging.message import Message
from ..messaging.notifier import OrchestratorNotifier


#------------------------------------------------------------------------------
class UIManager (object):
    """
    Dispatcher of messages for the UI plugins.
    """


    #----------------------------------------------------------------------
    def __init__(self, orchestrator):
        """
        :param orchestrator: Orchestrator instance.
        :type orchestrator: Orchestrator
        """

        # Keep a reference to the Orchestrator.
        self.__orchestrator = orchestrator

        # Init and start notifier.
        self.__notifier = OrchestratorNotifier(orchestrator)

        # Load the selected UI plugin.
        mode = orchestrator.config.ui_mode
        name = "ui/%s" % mode
        try:
            orchestrator.pluginManager.get_plugin_by_name(name)
        except KeyError:
            raise ValueError("No plugin found for UI mode: %r" % mode)
        self.__ui_plugin = orchestrator.pluginManager.load_plugin_by_name(name)

        # Add the plugin to the notifier.
        self.__notifier.add_plugin(name, self.__ui_plugin)


    #----------------------------------------------------------------------
    @property
    def orchestrator(self):
        """
        :returns: Orchestrator instance.
        :rtype: Orchestrator
        """
        return self.__orchestrator


    #----------------------------------------------------------------------
    @property
    def notifier(self):
        """
        :returns: UI notifier instance.
        :rtype: OrchestratorNotifier
        """
        return self.__notifier


    #----------------------------------------------------------------------
    @property
    def ui_plugin(self):
        """
        :returns: UI plugin instance.
        :rtype: UIPlugin
        """
        return self.__ui_plugin


    #----------------------------------------------------------------------
    def check_params(self, *audits):
        """
        Call the UI plugin to verify the Orchestrator and initial Audit
        settings before launching GoLismero.

        :param audits: Audit settings.
        :type audits: AuditConfig

        :raises AttributeError: A critical configuration option is missing.
        :raises ValueError: A configuration option has an incorrect value.
        :raises TypeError: A configuration option has a value of a wrong type.
        :raises Exception: An error occurred while validating the settings.
        """
        for audit_config in audits:
            audit_config.check_params()
        self.ui_plugin.check_params(self.orchestrator.config, *audits)


    #----------------------------------------------------------------------
    def start(self):
        """
        Send the UI start message.
        """
        message = Message(message_type = MessageType.MSG_TYPE_CONTROL,
                          message_code = MessageCode.MSG_CONTROL_START_UI)
        self.orchestrator.dispatch_msg(message)


    #----------------------------------------------------------------------
    def stop(self):
        """
        Send the UI stop message.
        """
        message = Message(message_type = MessageType.MSG_TYPE_CONTROL,
                          message_code = MessageCode.MSG_CONTROL_STOP_UI)
        self.orchestrator.dispatch_msg(message)


    #----------------------------------------------------------------------
    def dispatch_msg(self, message):
        """
        Dispatch incoming messages to all UI plugins.

        :param message: The message to send.
        :type message: Message
        """
        if not isinstance(message, Message):
            raise TypeError("Expected Message, got %s instead" % type(message))

        # Filter out ACKs but send all other messages.
        if (message.message_type != MessageType.MSG_TYPE_CONTROL or
            message.message_code != MessageCode.MSG_CONTROL_ACK
        ):
            self.__notifier.notify(message)


    #----------------------------------------------------------------------
    def close(self):
        """
        Release all resources held by this manager.
        """
        try:
            self.__notifier.close()
        finally:
            self.__orchestrator = None
            self.__notifier     = None
