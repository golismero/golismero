#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Audit control API.

.. note: Testing plugins should not need to use this API,
   it's meant primarily for the UI plugins to start and stop audits.
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

    # Query functions.
    "get_audit_count", "get_audit_names",
    "get_audit_config", "get_audit_times",
    "parse_audit_times",

    # Control functions.
    "start_audit", "stop_audit",
    ##pause_audit, resume_audit,
]

from .config import Config
from ..messaging.codes import MessageCode, MessageType, MessagePriority
from ..messaging.message import Message
from ..common import AuditConfig

from datetime import datetime


#------------------------------------------------------------------------------
def get_audit_count():
    """
    :returns: Number of currently running audits.
    :rtype: int
    """
    return Config._context.remote_call(MessageCode.MSG_RPC_AUDIT_COUNT)


#------------------------------------------------------------------------------
def get_audit_names():
    """
    :returns: Names of currently running audits.
    :rtype: set(str)
    """
    return Config._context.remote_call(MessageCode.MSG_RPC_AUDIT_NAMES)


#------------------------------------------------------------------------------
def get_audit_config(audit_name = None):
    """
    :param audit_name: Name of the audit to query.
        Use None for the current audit.
    :type audit_name: str | None

    :returns: Audit configuration.
    :rtype: AuditConfig
    """
    if not audit_name:
        return Config.audit_config
    return Config._context.remote_call(
        MessageCode.MSG_RPC_AUDIT_CONFIG, audit_name)


#------------------------------------------------------------------------------
def get_audit_times():
    """
    Get the audit start and stop times.

    :returns: Audit start time (None if it hasn't started yet)
        and audit stop time (None if it hasn't finished yet).
        Times are returned as POSIX timestamps.
    :rtype: tuple(float|None, float|None)
    """
    return Config._context.remote_call(MessageCode.MSG_RPC_AUDIT_TIMES)


#------------------------------------------------------------------------------
def parse_audit_times(start_time, stop_time):
    """
    Converts the audit start and stop times into human readable strings.

    :param start_time: Audit start time, as returned by get_audit_times().
    :type start_time: float | None

    :param start_time: Audit stop time, as returned by get_audit_times().
    :type start_time: float | None

    :returns: Audit start and stop times, total execution time.
    :rtype: tuple(str, str, str)
    """
    if start_time and stop_time:
        start_time = datetime.fromtimestamp(start_time)
        stop_time  = datetime.fromtimestamp(stop_time)
        if start_time < stop_time:
            td       = stop_time - start_time
            days     = td.days
            hours    = td.seconds // 3600
            minutes  = (td.seconds // 60) % 60
            seconds  = td.seconds
            run_time = "%d days, %d hours, %d minutes and %d seconds" % \
                (days, hours, minutes, seconds)
        else:
            run_time = "Interrupted"
        start_time = str(start_time)
        stop_time  = str(stop_time)
    else:
        if start_time:
            run_time   = "Interrupted"
        else:
            run_time   = "Unknown"
        if start_time:
            start_time = str(start_time)
        else:
            start_time = "Unknown"
        if stop_time:
            stop_time  = str(stop_time)
        else:
            stop_time  = "Interrupted"
    return (start_time, stop_time, run_time)


#------------------------------------------------------------------------------
def start_audit(audit_config):
    """
    Starts a new audit.

    :param audit_config: Audit configuration.
    :type audit_config: AuditConfig
    """
    if not isinstance(audit_config, AuditConfig):
        raise TypeError(
            "Expected AuditConfig, got %r instead" % type(audit_config))
    audit_config.check_params()
    Config._context.send_msg(
        message_type = MessageType.MSG_TYPE_CONTROL,
        message_code = MessageCode.MSG_CONTROL_START_AUDIT,
        message_info = audit_config,
            priority = MessagePriority.MSG_PRIORITY_HIGH,
    )


#------------------------------------------------------------------------------
def stop_audit(audit_name = None):
    """
    Stops an audit.

    :param audit_name: Name of the audit to stop.
        Use None for the current audit.
    :type audit_name: str | None
    """
    if not audit_name:
        audit_name = Config.audit_name
    msg = Message(
        message_type = MessageType.MSG_TYPE_CONTROL,
        message_code = MessageCode.MSG_CONTROL_STOP_AUDIT,
        message_info = False,        # True for finished, False for user cancel
          audit_name = audit_name,
         plugin_id = Config.plugin_id,
            priority = MessagePriority.MSG_PRIORITY_HIGH,
    )
    Config._context.send_raw_msg(msg)


#------------------------------------------------------------------------------
##def pause_audit(audit_name = None):
##    """
##    Pause an audit.
##
##    :param audit_name: Name of the audit to pause.
##        Use None for the current audit.
##    :type audit_name: str | None
##    """
##    if not audit_name:
##        audit_name = Config.audit_name
##    msg = Message(
##        message_type = MessageType.MSG_TYPE_CONTROL,
##        message_code = MessageCode.MSG_CONTROL_PAUSE_AUDIT,
##          audit_name = audit_name,
##           plugin_id = Config.plugin_id,
##            priority = MessagePriority.MSG_PRIORITY_HIGH,
##    )
##    Config._context.send_raw_msg(msg)


#------------------------------------------------------------------------------
##def resume_audit(audit_name = None):
##    """
##    Resume an audit.
##
##    :param audit_name: Name of the audit to resume.
##        Use None for the current audit.
##    :type audit_name: str | None
##    """
##    if not audit_name:
##        audit_name = Config.audit_name
##    msg = Message(
##        message_type = MessageType.MSG_TYPE_CONTROL,
##        message_code = MessageCode.MSG_CONTROL_RESUME_AUDIT,
##          audit_name = audit_name,
##           plugin_id = Config.plugin_id,
##            priority = MessagePriority.MSG_PRIORITY_HIGH,
##    )
##    Config._context.send_raw_msg(msg)
