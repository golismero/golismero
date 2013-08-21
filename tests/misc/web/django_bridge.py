#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module knows how to make the GoLismero Web UI
plugin communicate with its Django web application.
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

__all__ = ["launch_django", "GoLismeroStateMachine"]

import multiprocessing
import os.path
import sys
import thread
import threading
import traceback


#------------------------------------------------------------------------------
def launch_django(orchestrator_config, plugin_config, plugin_extra_config):
    """
    Launches the Django web application from the Web UI plugin.

    :param orchestrator_config: Orchestrator configuration.
    :type orchestrator_config: dict(str -> \\*)

    :param plugin_config: Web UI plugin configuration.
    :type plugin_config: dict(str -> \\*)

    :param plugin_extra_config: Web UI plugin extra configuration.
    :type plugin_extra_config: dict(str -> dict(str -> \\*))

    :returns: Bridge that allows the Web UI plugin to talk to Django.
    :rtype: GoLismero2Django
    """

    # Initialize the variables.
    process    = None
    in_parent  = None
    out_parent = None
    in_child   = None
    out_child  = None

    try:

        # Create the pipes to talk to the Django application.
        in_parent, out_child  = multiprocessing.Pipe(duplex=False)
        in_child,  out_parent = multiprocessing.Pipe(duplex=False)

        # Launch the new process where Django will run.
        args = (
            in_child_conn, out_child_conn,
            orchestrator_config, plugin_config, plugin_extra_config
        )
        process = multiprocessing.Process(target=_launch_django, args=args)
        process.daemon = True  # switch to False if Django fails to run
        process.start()

        # Get the initialization status packet.
        # On timeout or error kill the child process.
        if not in_parent.poll(10):
            raise RuntimeError("Django initialization timed out!")
        status = in_parent.recv()
        if status[0] == "fail":
            raise RuntimeError(
                "Django initialization failed, reason: %s" % status[1])

        # Return the bridge from GoLismero to Django.
        return Bridge(in_parent_conn, out_parent_conn)

    # Clean up on error.
    except:
        if process    is not None: process.terminate()
        if in_parent  is not None: in_parent.close()
        if out_parent is not None: out_parent.close()
        if in_child   is not None: in_child.close()
        if out_child  is not None: out_child.close()
        raise

def _launch_django(input_conn, output_conn,
                   orchestrator_config, plugin_config, plugin_extra_config):
    """
    Internally called function that bootstraps the Django application.

    .. warning: Do not call it yourself!

    :param input_conn: Input pipe.
    :type input_conn: Connection

    :param output_conn: Output pipe.
    :type output_conn: Connection

    :param orchestrator_config: Orchestrator configuration.
    :type orchestrator_config: dict(str -> \\*)

    :param plugin_config: Web UI plugin configuration.
    :type plugin_config: dict(str -> \\*)

    :param plugin_extra_config: Web UI plugin extra configuration.
    :type plugin_extra_config: dict(str -> dict(str -> \\*))
    """

    # Make sure all exceptions are caught.
    try:
        try:
            try:

                # Get the Django command to run.
                command = [x.strip() for x in plugin_config["call_command"].split(" ")]

                # Instance the bridge object to talk to GoLismero.
                bridge = Bridge(input_conn, output_conn)

                # Update the module search path to include our web app.
                modpath = os.path.abspath(os.path.split(__file__)[0]))
                sys.path.insert(0, modpath)

                # Load the Django settings.
                # XXX FIXME this code is bogus! @cr0hn: put your stuff here :)
                from django.core.management import call_command
                from django.conf import settings
                settings["GOLISMERO_BRIDGE"]              = bridge
                settings["GOLISMERO_MAIN_CONFIG"]         = orchestrator_config
                settings["GOLISMERO_PLUGIN_CONFIG"]       = plugin_config
                settings["GOLISMERO_PLUGIN_EXTRA_CONFIG"] = plugin_extra_config

                # Load the Django webapp data model.
                # XXX FIXME this code is bogus! @cr0hn: put your stuff here :)
                from golismero_webapp.data.models import *

                # Start the web application in the background.
                # XXX FIXME this code is bogus! @cr0hn: put your stuff here :)
                # XXX this must be blocking, when we return that means
                # the web application has shut down and we're quitting.
                # You MUST instance GoLismeroStateMachine() by passing it
                # the Bridge instance and (optionally) your event callback.
                call_command(*command)

            # On error tell GoLismero we failed to initialize.
            except Exception, e:
                msg = "%s\n%s" % (str(e), traceback.format_exc())
                output_conn.send( ("fail", msg) )

        # Clean up before exit.
        finally:
            try:
                input_conn.close()
            except:
                pass
            try:
                output_conn.close()
            except:
                pass

    # Silently catch all runaway exceptions.
    except:
        pass


#------------------------------------------------------------------------------
class Bridge (object):
    """
    Django <-> GoLismero bridge.
    """


    #--------------------------------------------------------------------------
    def __init__(self, input_conn, output_conn):
        """
        :param input_conn: Input pipe.
        :type input_conn: Connection

        :param output_conn: Output pipe.
        :type output_conn: Connection
        """
        self.__input_conn  = input_conn
        self.__output_conn = output_conn


    #--------------------------------------------------------------------------
    def recv(self, timeout = None):
        """
        Receive the next packet.

        :param timeout: Optional timeout in seconds.
        :type timeout: int | float | None

        :returns: Packet.
        :rtype: \\*
        """
        if timeout is not None:
            self.__input_conn.poll(timeout)
        return self.__input_conn.recv()


    #--------------------------------------------------------------------------
    def send(self, packet, timeout = None):
        """
        Send a packet.

        :param timeout: Optional timeout in seconds.
        :type timeout: int | float | None

        :param packet: Packet.
        :type packet: \\*
        """
        if timeout is not None:
            self.__output_conn.poll(timeout)
        return self.__output_conn.send(packet)


    #--------------------------------------------------------------------------
    def close(self):
        """
        Shut down the bridge.

        .. note: No exceptions are raised on error.
        """
        try:
            self.__input_conn.close()
        except:
            pass
        try:
            self.__output_conn.close()
        except:
            pass


#------------------------------------------------------------------------------
class GoLismeroStateMachine (threading.Thread):
    """
    State machine to parse packets from the GoLismero bridge.
    """


    #--------------------------------------------------------------------------
    def __init__(self, bridge, event_callback = None):
        """
        :param bridge: Django <-> GoLismero bridge.
        :type bridge: Bridge

        :param event_callback: Optional callback to receive GoLismero events.
            The first argument will be the event name, and the remaining
            arguments depend on each event.
        :type event_callback: callable | None
        """

        # Call the superclass constructor.
        super(GoLismeroStateMachine, self).__init__()

        # Initialize the properties.
        self.__enabled  = True
        self.__bridge   = bridge
        self.__callback = event_callback
        self.__mutex    = threading.RLock()
        self.__queries  = []
        self.__reply    = None

        # Tell GoLismero we've initialized properly.
        self.__bridge.send( ("ok",) )


    #--------------------------------------------------------------------------
    def stop(self):
        """
        Stop the thread and close the bridge.
        """
        self.__enabled = False
        self.__bridge.close()
        if thread.get_ident() != self.ident:
            self.join()


    #--------------------------------------------------------------------------
    def call(self, command, *args):
        """
        Call a command.

        :param command: Command to call.
            All subsequent arguments are passed to the command.
        :type command: str

        :returns: Return value from the command.
        :rtype: \\*
        """

        # Abort if we're shutting down.
        if not self.__enabled:
            raise RuntimeError("Cannot make calls while shutting down")

        # Event that will be set when we must consume a reply.
        consume = threading.Event()
        consume.clear()

        # Event that will be set when we're done consuming a reply.
        done = threading.Event()
        done.clear()

        # Build the command packet.
        packet = (command,) + args

        # Use the mutex.
        with self.__mutex:

            # Put the events in the queue.
            self.__queries.append( (consume, done) )

            # Send the command.
            self.__bridge.send(packet)

        # Wait for the reply.
        consume.wait()

        # Get the reply.
        reply = self.__reply

        # Signal we're done.
        done.set()

        # Return the reply.
        return reply


    #--------------------------------------------------------------------------
    def run(self):
        """
        State machine to parse packets from the GoLismero bridge.
        """

        # Loop until requested to shut down.
        while self.__enabled:

            # Get the next packet.
            packet = self.__bridge.recv()

            try:

                # Extract the command and the arguments.
                command = packet[0]
                args = packet[1:]

                # If it's the special command to stop...
                if command == "stop":

                    # Close the bridge.
                    self.__bridge.close()

                    # Shut down.
                    break

                # If it's a reply...
                if command in ("ok", "fail"):

                    # Get the reply value.
                    try:
                        reply = args[0]
                    except IndexError:
                        reply = None

                    # Use the mutex.
                    with self.__mutex:

                        # Get the next reply target.
                        consume, done = self.__queries.pop(0)

                        # Store the reply value.
                        self.__reply = reply

                        # Tell the consumer to read it.
                        consume.set()

                        # Wait for the consumer to finish.
                        done.wait()

                # If it's an event...
                else:

                    # Use the callback.
                    if self.__callback:
                        self.__callback(command, *args)

            # Break the loop if we're killing the current process.
            except SystemExit:
                break

            # Ignore all other exceptions.
            except:
                continue

    # Kill the current process.
    sys.exit(0)
