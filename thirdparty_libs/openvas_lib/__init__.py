#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
OpenVAS manager library for OMP v4.0.

This is a replacement of the official library OpenVAS python library,
because the official library doesn't work with OMP v4.0.
"""

__license__ = """
OpenVAS connector for OMPv4.

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

__all__ = ["VulnscanManager"]

import os, sys
cwd = os.path.abspath(os.path.split(__file__)[0])
cwd = os.path.join(cwd, ".")
sys.path.insert(0, cwd)

from .data import *  # noqa

from traceback import format_exc

import socket
import ssl
import re
import threading

from collections import Iterable

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

try:
    # For use within GoLismero:
    # https://github.com/golismero/golismero

    from golismero.api.parallel import setInterval
    from golismero.api.text.text_utils import generate_random_string

except ImportError:

    # Reimplement the missing functionality.

    from random import choice
    from string import ascii_letters, digits
    from threading import Event, Timer


    #------------------------------------------------------------------------------
    def setInterval(interval, times = -1):
        """
        Decorator to execute a function periodically using a timer.
        The function is executed in a background thread.

        Example:

            >>> from time import gmtime, strftime
            >>> @setInterval(2) # Execute every 2 seconds until stopped.
            ... def my_func():
            ...     print strftime("%Y-%m-%d %H:%M:%S", gmtime())
            ...
            >>> handler = my_func()
            2013-07-25 22:40:55
            2013-07-25 22:40:57
            2013-07-25 22:40:59
            2013-07-25 22:41:01
            >>> handler.set() # Stop the execution.
            >>> @setInterval(2, 3) # Every 2 seconds, 3 times.
            ... def my_func():
            ...     print strftime("%Y-%m-%d %H:%M:%S", gmtime())
            ...
            >>> handler = my_func()
            2013-07-25 22:40:55
            2013-07-25 22:40:57
            2013-07-25 22:40:59

        :param: interval: Interval in seconds of how often the function will be
                          executed.
        :type interval: float | int

        :param times: Maximum number of times the function will be executed.
                      Negative values cause the function to be executed until
                      manually stopped, or until the process dies.
        :type times: int
        """

        # Validate the parameters.
        if isinstance(interval, int):
            interval = float(interval)
        elif not isinstance(interval, float):
            raise TypeError("Expected int or float, got %r instead" % type(interval))
        if not isinstance(times, int):
            raise TypeError("Expected int, got %r instead" % type(times))

        # Code adapted from: http://stackoverflow.com/q/5179467

        # This will be the actual decorator,
        # with fixed interval and times parameter
        def outer_wrap(function):
            if not callable(function):
                raise TypeError("Expected function, got %r instead" % type(function))

            # This will be the function to be
            # called
            def wrap(*args, **kwargs):

                stop = Event()

                # This is another function to be executed
                # in a different thread to simulate setInterval
                def inner_wrap():
                    i = 0
                    while i != times and not stop.isSet():
                        stop.wait(interval)
                        function(*args, **kwargs)
                        i += 1

                t = Timer(0, inner_wrap)
                t.daemon = True
                t.start()

                return stop

            return wrap

        return outer_wrap


    #----------------------------------------------------------------------
    def generate_random_string(length = 30):
        """
        Generates a random string of the specified length.

        The key space used to generate random strings are:

        - ASCII letters (both lowercase and uppercase).
        - Digits (0-9).

        >>> generate_random_string(10)
        Asi91Ujsn5
        >>> generate_random_string(30)
        8KNLs981jc0h1ls8b2ks01bc7slgu2

        :param length: Desired string length.
        :type length: int
        """

        m_available_chars = ascii_letters + digits

        return "".join(choice(m_available_chars) for _ in xrange(length))


from data import *


#------------------------------------------------------------------------------
#
# High level exceptions
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
class VulnscanException(Exception):
    "Base class for OpenVAS exceptions."


#------------------------------------------------------------------------------
class VulnscanAuthFail(VulnscanException):
    "Authentication failure."


#------------------------------------------------------------------------------
class VulnscanServerError(VulnscanException):
    "Error message from the OpenVAS server."


#------------------------------------------------------------------------------
class VulnscanClientError(VulnscanException):
    "Error message from the OpenVAS client."


#------------------------------------------------------------------------------
class VulnscanProfileError(VulnscanException):
    "Profile error."


#------------------------------------------------------------------------------
class VulnscanTargetError(VulnscanException):
    "Target related errors."


#------------------------------------------------------------------------------
class VulnscanScanError(VulnscanException):
    "Task related errors."


#------------------------------------------------------------------------------
#
# High level interface
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
class VulnscanManager(object):
    """
    High level interface to the OpenVAS server.

    ..warning: Only compatible with OMP 4.0.
    """


    #----------------------------------------------------------------------
    #
    # Methods to manage OpenVAS
    #
    #----------------------------------------------------------------------


    #----------------------------------------------------------------------
    def __init__(self, host, user, password, port=9390, timeout=None):
        """
        :param host: The host where the OpenVAS server is running.
        :type host: str

        :param user: Username to connect with.
        :type user: str

        :param password: Password to connect with.
        :type password: str

        :param port: Port number of the OpenVAS server.
        :type port: int
        """

        if not isinstance(host, basestring):
            raise TypeError("Expected string, got %r instead" % type(host))
        if not isinstance(user, basestring):
            raise TypeError("Expected string, got %r instead" % type(user))
        if not isinstance(password, basestring):
            raise TypeError("Expected string, got %r instead" % type(password))
        if isinstance(port, int):
            if not (0 < port <= 65535):
                raise ValueError("Port number must be in range (0, 65535]")
        else:
            raise TypeError("Expected int, got %r instead" % type(port))

        m_time_out = None
        if timeout:
            if isinstance(timeout, int):
                if timeout < 1:
                    raise ValueError("Timeout value must be greater than 0.")
                else:
                    m_time_out = timeout
            else:
                raise TypeError("Expected int, got %r instead" % type(timeout))

        # Create the manager
        try:
            self.__manager = OMPv4(host, user, password, port, timeout=m_time_out)
        except ServerError, e:
            raise VulnscanServerError("Error while connecting to the server: %s" % e.message)
        except AuthFailedError:
            raise VulnscanAuthFail("Error while trying to authenticate into the server.")


    #----------------------------------------------------------------------
    def launch_scan(self, target, **kwargs):
        """
        Launch a new audit in OpenVAS.

        This is an example code to launch an OpenVAS scan and wait for it
        to complete::

            from threading import Semaphore
            from functools import partial

            def my_print_status(i): print str(i)

            def my_launch_scanner():

                Sem = Semaphore(0)

                # Configure
                manager = VulnscanManager.connectOpenVAS("localhost", "admin", "admin)

                # Launch
                manager.launch_scan(
                    target,
                    profile = "empty",
                    callback_end = partial(lambda x: x.release(), sem),
                    callback_progress = my_print_status
                )

                # Wait
                Sem.acquire()

                # Finished scan
                print "finished!"

            # >>> my_launch_scanner() # It can take some time
            # 0
            # 10
            # 39
            # 60
            # 90
            # finished!

        :param target: Target to audit.
        :type target: str

        :param profile: Scan profile in the OpenVAS server.
        :type profile: str

        :param callback_end: If this param is set, the process will run in background
                             and call the function specified in this var when the
                             scan ends.
        :type callback_end: function

        :param callback_progress: If this param is set, it will be called every 10 seconds,
                                  with the progress percentaje as a float.
        :type callback_progress: function(float)

        :return: ID of the audit and ID of the target: (ID_scan, ID_target)
        :rtype: (str, str)
        """

        profile              = kwargs.get("profile", "Full and fast")
        call_back_end        = kwargs.get("callback_end", None)
        call_back_progress   = kwargs.get("callback_progress", None)
        if not (isinstance(target, basestring) or isinstance(target, Iterable)):
            raise TypeError("Expected basestring or iterable, got %r instead" % type(target))
        if not isinstance(profile, basestring):
            raise TypeError("Expected string, got %r instead" % type(profile))

        # Generate the random names used
        m_target_name = "golismero_target_%s" % generate_random_string(20)
        m_job_name    = "golismero_scan_%s" % generate_random_string(20)

        # Create the target
        try:
            m_target_id = self.__manager.create_target(m_target_name, target, "Temporal target from golismero OpenVAS plugin")
        except ServerError, e:
            raise VulnscanTargetError("The target already exits on the server. Error: %s" % e.message)

        # Get the profile ID by their name
        m_profile_id      = None
        try:
            tmp           = self.__manager.get_configs_ids(profile)
            m_profile_id  = tmp[profile]
        except ServerError, e:
            raise VulnscanProfileError("The profile select not exits int the server. Error: %s" % e.message)
        except KeyError:
            raise VulnscanProfileError("The profile select not exits int the server")

        # Create task
        m_task_id     = None
        try:
            m_task_id = self.__manager.create_task(m_job_name, m_target_id, config=m_profile_id, comment="scan from golismero OpenVAS plugin")
        except ServerError, e:
            raise VulnscanScanError("The target selected doesnn't exist in the server. Error: %s" % e.message)

        # Start the scan
        try:
            self.__manager.start_task(m_task_id)
        except ServerError, e:
            raise VulnscanScanError("Unknown error while try to start the task '%s'. Error: %s" % (m_task_id, e.message))

        # Callback is set?
        if call_back_end or call_back_progress:
            # schedule a function to run each 10 seconds to check the estate in the server
            self.__function_handle = self._callback(call_back_end, call_back_progress)
            self.__task_id         = m_task_id
            self.__target_id       = m_target_id

        return (m_task_id, m_target_id)


    #----------------------------------------------------------------------
    @property
    def task_id(self):
        """
        :returns: OpenVAS task ID.
        :rtype: str
        """
        return self.__task_id


    #----------------------------------------------------------------------
    @property
    def target_id(self):
        """
        :returns: OpenVAS target ID.
        :rtype: str
        """
        return self.__target_id


    #----------------------------------------------------------------------
    def delete_scan(self, scan_id):
        """
        Delete specified scan ID in the OpenVAS server.

        :param scan_id: Scan ID.
        :type scan_id: str
        """
        self.__manager.delete_task(scan_id)


    #----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
        Delete specified target ID in the OpenVAS server.

        :param target_id: Target ID.
        :type target_id: str
        """
        self.__manager.delete_target(target_id)


    #----------------------------------------------------------------------
    def get_results(self, scan_id):
        """
        Get the results associated to the scan ID.

        :param scan_id: Scan ID.
        :type scan_id: str

        :return: Scan results.
        :rtype: list(OpenVASResult)
        """

        if not isinstance(scan_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(scan_id))

        m_response = None
        try:
            m_response = self.__manager.make_xml_request('<get_results task_id="%s"/>' % scan_id, xml_result=True)
        except ServerError, e:
            raise VulnscanServerError("Can't get the results for the task %s. Error: %s" % (scan_id, e.message))

        return self.transform(m_response)


    #----------------------------------------------------------------------
    def get_progress(self, scan_id):
        """
        Get the progress of a scan.

        :param scan_id: Scan ID.
        :type scan_id: str

        :return: Progress percentaje (between 0.0 and 100.0).
        :rtype: float
        """
        if not isinstance(scan_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(scan_id))

        return self.__manager.get_tasks_progress(scan_id)


    #----------------------------------------------------------------------
    def stop_audit(self, scan_id):
        raise NotImplemented("Not implemented yet")


    #----------------------------------------------------------------------
    @property
    def get_profiles(self):
        """
        :return: All available profiles.
        :rtype: {profile_name: ID}
        """
        return self.__manager.get_configs_ids()


    #----------------------------------------------------------------------
    @property
    def get_all_scans(self):
        """
        :return: All scans.
        :rtype: {scan_name: ID}
        """
        return self.__manager.get_tasks_ids()


    #----------------------------------------------------------------------
    @property
    def get_running_scans(self):
        """
        :return: All running scans.
        :rtype: {scan_name: ID}
        """
        return self.__manager.get_tasks_ids_by_status("Running")


    #----------------------------------------------------------------------
    @property
    def get_finished_scans(self):
        """
        :return: All finished scans.
        :rtype: {scan_name: ID}
        """
        return self.__manager.get_tasks_ids_by_status("Done")


    #----------------------------------------------------------------------
    #
    # Transform OpenVAS results to GoLismero structures
    #
    #----------------------------------------------------------------------


    #----------------------------------------------------------------------
    @staticmethod
    def transform(xml_results):
        """
        Transform the XML results of OpenVAS into GoLismero structures.

        :param xml_results: Input results from OpenVAS in XML format.
        :type xml_results: list(Element)

        :return: Results in GoLismero format.
        :rtype: list(OpenVASResult)
        """
        PORT = re.compile("([\w\d\s]*)\(([\d]+)/([\w\W\d]+)\)")

        m_return         = []
        m_return_append  = m_return.append

        # All the results
        for l_results in xml_results.findall(".//results"):
            for l_results in l_results.findall("result"):
                l_partial_result = OpenVASResult.make_empty_object()

                # Ignore log messages, only get the results
                if l_results.find("threat").text == "Log":
                    continue

                # For each result
                for l_val in l_results.getchildren():

                    l_tag = l_val.tag

                    if l_tag in ("subnet", "host", "threat", "description"):
                        # All text vars can be processes both.
                        setattr(l_partial_result, l_tag, l_val.text)
                    elif l_tag == "port":
                        # Extract and filter port info
                        l_port = PORT.findall(l_val.text)
                        if l_port and len(l_port) > 0:
                            if len(l_port[0]) == 3:
                                l_s       = l_port[0]
                                l_service = l_s[0]
                                l_port    = int(l_s[1])
                                l_proto   = l_s[2]

                                l_partial_result.port = OpenVASPort(l_service,
                                                                    l_port,
                                                                    l_proto)
                    elif l_tag == "nvt":
                        l_nvt_symbols = [x for x in dir(l_val) if not x.startswith("_")]
                        # The NVT Object
                        l_nvt_object  = OpenVASNVT.make_empty_object()
                        for l_nvt in l_val.getchildren():
                            l_nvt_tag = l_nvt.tag

                            if l_nvt_tag in l_nvt_symbols:
                                setattr(l_nvt_object, l_nvt_tag, l_nvt.text)

                        # Add to the NVT Object
                        l_partial_result.nvt = l_nvt_object
                    else:
                        pass

                # Add to the return values
                m_return_append(l_partial_result)

        return m_return


    #----------------------------------------------------------------------
    @setInterval(10.0)
    def _callback(self, func_end, func_status):
        """
        This callback function is called periodically from a timer.
        """

        # Check if audit was finished
        if self.__task_id in self.__manager.get_tasks_ids_by_status(status="Done").values():

            # Task is finished. Stop the callback interval
            self.__function_handle.set()

            # Then, remove the target
            #try:
                #self.delete_target(self.__target_id)
            #except Exception, e:
                #raise VulnscanException("Error while try to delete the target %s. Error: %s" % (self.__target_id, e.message))

            # Call the callback function
            if func_end:
                func_end()

        if func_status:
            t = self.get_progress(self.__task_id)
            func_status(t)


#
#
# Some code and ideas of the next code has been taken from the official
# OpenVAS library:
#
# https://pypi.python.org/pypi/OpenVAS.omplib
#
#
#

#------------------------------------------------------------------------------
#
# OMPv4 low level exceptions
#
#------------------------------------------------------------------------------
class Error(Exception):
    """Base class for OMP errors."""
    def __str__(self):
        return repr(self)

class _ErrorResponse(Error):
    def __init__(self, msg="", *args):

        self.message = msg

        super(_ErrorResponse, self).__init__(*args)

    def __str__(self):
        return self.message

class ClientError(_ErrorResponse):
    """command issued could not be executed due to error made by the client"""

class ServerError(_ErrorResponse):
    """error occurred in the manager during the processing of this command"""

class ResultError(Error):
    """Get invalid answer from Server"""
    def __str__(self):
        return 'Result Error: answer from command %s is invalid' % self.args

class AuthFailedError(Error):
    """Authentication failed."""

#------------------------------------------------------------------------------
#
# OMPv4 low level interface
#
#------------------------------------------------------------------------------
class OMPv4(object):
    """
    Internal manager for OpenVAS low level operations.

    ..note:
        This class is based in code from the original OpenVAS plugin:

        https://pypi.python.org/pypi/OpenVAS.omplib

    ..warning:
        This code is only compatible with OMP 4.0.
    """

    TIMEOUT = 10.0


    #----------------------------------------------------------------------
    def __init__(self, host, username, password, port=9390, timeout=None):
        """
        Open a connection to the manager and authenticate the user.

        :param host: string with host where OpenVAS manager are running.
        :type host: str

        :param username: user name in the OpenVAS manager.
        :type username: str

        :param password: user password.
        :type password: str

        :param port: port of the OpenVAS Manager
        :type port: int

        :param timeout: timeout for connection, in seconds.
        :type timeout: int
        """

        if not isinstance(host, basestring):
            raise TypeError("Expected string, got %r instead" % type(host))
        if not isinstance(username, basestring):
            raise TypeError("Expected string, got %r instead" % type(username))
        if isinstance(port, int):
            if not (0 < port < 65535):
                raise ValueError("Port must be between 0-65535")
        else:
            raise TypeError("Expected int, got %r instead" % type(port))
        if timeout:
            if not isinstance(timeout, int):
                raise TypeError("Expected int, got %r instead" % type(timeout))

        self.__host             = host
        self.__username         = username
        self.__password         = password
        self.__port             = port

        # Synchronizes access to the socket,
        # which is shared by all threads in this plugin
        self.__socket_lock      = threading.RLock()

        # Controls for timeout
        self.__timeout          = OMPv4.TIMEOUT
        if timeout:
            self.__timeout = timeout

        # Make the connection
        self._connect()


    #----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    #----------------------------------------------------------------------


    #----------------------------------------------------------------------
    def close(self):
        """Close the connection to the manager."""
        if self.socket is not None:
            try:
                self.socket.shutdown(2)
            except Exception:
                pass
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None


    #----------------------------------------------------------------------
    def make_xml_request(self, xmldata, xml_result=False):
        """
        Low-level interface to send OMP XML to the manager.

        `xmldata` may be either a utf-8 encoded string or an etree
        Element. If `xml_result` is true, the result is returned as an
        etree Element, otherwise a utf-8 encoded string is returned.

        :param xmldata: string with the XML data.
        :type: xmldata: str

        :param xml_result: boolean that indicates if the response will be in XML format.
        :type xml_result: bool

        :return: a text/xml data from the server.
        :rtype: `ElementTree`

        :raises: RunTimeError, ClientError, ServerError
        """

        if xml_result:
            return self._xml_command(xmldata)
        else:
            return self._text_command(xmldata)


    #----------------------------------------------------------------------
    def delete_task(self, task_id):
        """
        Delete a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: RunTimeError, ClientError, ServerError
        """

        request =  """<delete_task task_id="%s" />""" % (task_id)

        self.make_xml_request(request, xml_result=True)


    #----------------------------------------------------------------------
    def create_task(self, name, target, config=None, comment=""):
        """
        Creates a task in OpenVAS.

        :param name: name to the task
        :type name: str

        :param target: target to scan
        :type target: str

        :param config: config (profile) name
        :type config: str

        :param comment: comment to add to task
        :type comment: str

        :return: the ID of the task created.
        :rtype: str

        :raises: RunTimeError, ClientError, ServerError
        """

        if not config:
            config = "Full and fast"

        request =  """<create_task>
            <name>%s</name>
            <comment>%s</comment>
            <config id="%s"/>
            <target id="%s"/>
            </create_task>""" % (name, comment, config, target)

        return self.make_xml_request(request, xml_result=True).get("id")


    #----------------------------------------------------------------------
    def create_target(self, name, hosts, comment=""):
        """
        Creates a target in OpenVAS.

        :param name: name to the target
        :type name: str

        :param hosts: target list. Can be only one target or a list of targets
        :type hosts: str | list(str)

        :param comment: comment to add to task
        :type comment: str

        :return: the ID of the created target.
        :rtype: str

        :raises: RunTimeError, ClientError, ServerError
        """

        if isinstance(hosts, str):
            m_targets = hosts
        elif isinstance(hosts, Iterable):
            m_targets = ",".join(hosts)

        request =  """<create_target>
            <name>%s</name>
            <hosts>%s</hosts>
            <comment>%s</comment>
        </create_target>""" % (name, m_targets, comment)

        return self.make_xml_request(request, xml_result=True).get("id")


    #----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
        Delete a target in OpenVAS server.

        :param target_id: target id
        :type target_id: str

        :raises: RunTimeError, ClientError, ServerError
        """

        request =  """<delete_target target_id="%s" />""" % (target_id)

        self.make_xml_request(request, xml_result=True)


    #----------------------------------------------------------------------
    def get_configs(self, config_id=None):
        """
        Get information about the configs in the server.

        If name param is provided, only get the config associated to this name.

        :param config_id: config id to get
        :type config_id: str

        :return: `ElementTree`

        :raises: RunTimeError, ClientError, ServerError
        """
        # Recover all config from OpenVAS
        if config_id:
            return self.make_xml_request('<get_configs config_id="%s"/>' % config_id, xml_result=True)
        else:
            return self.make_xml_request("<get_configs />", xml_result=True)


    #----------------------------------------------------------------------
    def get_configs_ids(self, name=None):
        """
        Get information about the configured profiles (configs)in the server.

        If name param is provided, only get the ID associated to this name.

        :param name: config name to get
        :type name: str

        :return: a dict with the format: {config_name: config_ID}

        :raises: RunTimeError, ClientError, ServerError
        """

        m_return = {}

        for x in self.get_configs().findall("config"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name : m_return[name]}
        else:
            return m_return


    #----------------------------------------------------------------------
    def get_tasks(self, task_id=None):
        """
        Get information about the configured profiles in the server.

        If name param is provided, only get the task associated to this name.

        :param task_id: task id to get
        :type task_id: str

        :return: `ElementTree`

        :raises: RunTimeError, ClientError, ServerError
        """
        # Recover all config from OpenVAS
        if task_id:
            return self.make_xml_request('<get_tasks id="%s"/>' % name, xml_result=True)
        else:
            return self.make_xml_request("<get_tasks />", xml_result=True)


    #----------------------------------------------------------------------
    def get_tasks_ids(self, name=None):
        """
        Get IDs of tasks of the server.

        If name param is provided, only get the ID associated to this name.

        :param name: task name to get
        :type name: str

        :return: a dict with the format: {task_name: task_ID}

        :raises: RunTimeError, ClientError, ServerError
        """

        m_return = {}

        for x in self.get_tasks().findall("task"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name : m_return[name]}
        else:
            return m_return


    #----------------------------------------------------------------------
    def get_tasks_progress(self, task_id):
        """
        Get the progress of the task.

        :param task_id: ID of the task
        :type task_id: str

        :return: a float number between 0-100
        :rtype: float

        :raises: RunTimeError, ClientError, ServerError
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_sum_progress = 0.0 # Partial progress
        m_progress_len = 0.0 # All of tasks

        for x in self.get_tasks().findall("task"):
            if x.get("id") == task_id:
                # Looking for each task for each target
                l_status = x.find("status").text
                if l_status == "Running":

                    for l_p in x.findall("progress"):
                        for l_hp in l_p.findall("host_progress"):
                            for r in  l_hp.findall("host"):
                                q = etree.tostring(r)
                                if q:
                                    v = q[q.rfind(">") + 1:]
                                    m_progress_len += 1.0
                                    m_sum_progress += float(v)

        try:
            return (m_sum_progress/m_progress_len)
        except ZeroDivisionError:
            return 0.0


    #----------------------------------------------------------------------
    def get_tasks_ids_by_status(self, status="Done"):
        """
        Get IDs of tasks of the server depending of their status.

        Allowed status are: "Done", "Paused", "Running", "Stopped".

        If name param is provided, only get the ID associated to this name.

        :param name: get task with this status
        :type name: str - ("Done" |"Paused" | "Running" | "Stopped".)

        :return: a dict with the format: {task_name: task_ID}

        :raises: RunTimeError, ClientError, ServerError
        """
        if status not in ("Done", "Paused", "Running", "Stopped"):
            raise ValueError("Requested status are not allowed")


        m_task_ids        = {}

        for x in self.get_tasks().findall("task"):
            if x.find("status").text == status:
                m_task_ids[x.find("name").text] = x.attrib["id"]

        return m_task_ids


    #----------------------------------------------------------------------
    def get_results(self, task_id=None):
        """
        Get the results associated to the scan ID.

        :param task_id: ID of scan to get. All if not provided
        :type task_id: str

        :return: xml object
        :rtype: `ElementTree`

        :raises: RunTimeError, ClientError, ServerError
        """

        m_query = None
        if task_id:
            m_query = '<get_results task_id="%s"/>' % scan_id
        else:
            m_query = '<get_results/>'

        return self.__manager.xml(m_query, xml_result=True)


    #----------------------------------------------------------------------
    def start_task(self, task_id):
        """
        Start a task.

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: RunTimeError, ClientError, ServerError
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_query = '<start_task task_id="%s"/>' % task_id

        self.make_xml_request(m_query, xml_result=True)


    #----------------------------------------------------------------------
    #
    # PRIVATE METHODS
    #
    #----------------------------------------------------------------------


    #----------------------------------------------------------------------
    def _connect(self):
        """
        Makes the connection and initializes the socket.
        """

        # Get the timeout
        m_timeout = OMPv4.TIMEOUT
        if self.__timeout:
            m_timeout = self.__timeout

        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(m_timeout)
        try:
            sock.connect((self.__host, int(self.__port)))
        except socket.error, e:
            raise ServerError(str(e))
        self.socket = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1)

        # Authenticate to the server
        self._authenticate(self.__username, self.__password)


    #----------------------------------------------------------------------
    def _authenticate(self, username, password):
        """
        Authenticate a user to the manager.

        :param username: user name
        :type username: str

        :param password: user password
        :type password: str

        :raises: AuthFailedError
        """
        if not isinstance(username, basestring):
            raise TypeError("Expected string, got %r instead" % type(username))
        if not isinstance(password, basestring):
            raise TypeError("Expected string, got %r instead" % type(password))

        m_request = """<authenticate>
            <credentials>
              <username>%s</username>
              <password>%s</password>
            </credentials>
        </authenticate>""" % (username, password)

        try:
            self._text_command(m_request)
        except ClientError:
            raise AuthFailedError(username)


    #----------------------------------------------------------------------
    def _send(self, data):
        """Send OMP data to the manager and read the result.

        `data` may be either an unicode string, an utf-8 encoded
        string or an etree Element. The result is as an etree Element.

        :param data: data to send.
        :type data: str | ElementTree

        :return: XML tree element.
        :rtype: `ElementTree`
        """

        # Make sure the data is a string.
        if etree.iselement(data):
            data = etree.dump(data)
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        # Synchronize access to the socket.
        with self.__socket_lock:

            # Send the data to the server.
            self.socket.sendall(data)

            # Get the response from the server.
            data = ""
            tree = None
            while True:
                chunk = self.socket.recv(1024)
                if not chunk:
                    break
                data += chunk
                try:
                    tree = etree.fromstring(data)
                except Exception:
                    continue
                break
            if tree is None:
                tree = etree.fromstring(data)

            # Return the parsed response.
            return tree


    #----------------------------------------------------------------------
    def _check_response(self, response):
        """
        Check the response read from the manager.

        If the response status is 4xx a ClientError is raised, if the
        status is 5xx a ServerError is raised.

        :param response: ElementTree with the response
        :type response: ElementTree

        :return: status text
        :type: str

        :raises: RunTimeError, ClientError, ServerError
        """
        if response is None:
            raise TypeError("Expected ElementTree, got '%s' instead" % type(response))

        status = response.get('status')

        if status is None:
            raise RunTimeError('response is missing status: %s'
                               % etree.tostring(response))
        if status.startswith('4'):
            raise ClientError("[%s] %s: %s" % (status,
                                               response.tag,
                                               response.get('status_text')))

        elif status.startswith('5'):
            raise ServerError("[%s] %s: %s" %(status,
                                              response.tag,
                                              response.get('status_text')))

        return status


    #----------------------------------------------------------------------
    def _text_command(self, request):
        """
        Make a request and get the text of the response in raw format.

        :param request: the query.
        :type request: str

        :return: the response text.
        :rtype: str

        :raises: RunTimeError, ClientError, ServerError
        """
        response = self._send(request)
        self._check_response(response)
        return response.text


    #----------------------------------------------------------------------
    def _xml_command(self, request):
        """
        Make a request and get the response as xml tree format.

        :param request: the query.
        :type request: str

        :return: the response as xml tree.
        :rtype: `ElementTree`

        :raises: RunTimeError, ClientError, ServerError
        """
        response = self._send(request)
        self._check_response(response)
        return response
