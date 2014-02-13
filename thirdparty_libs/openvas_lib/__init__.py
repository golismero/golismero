#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
OpenVAS connector for OMP protocol.

This is a replacement of the official library OpenVAS python library,
because the official library doesn't work with OMP v4.0.
"""

__license__ = """
OpenVAS connector for OMP protocol.

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

import socket
import ssl
import re
from threading import RLock

from .data import *
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
    def setInterval(interval, times=-1):
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
    def generate_random_string(length=30):
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


#------------------------------------------------------------------------------
#
# High level exceptions
#
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
class VulnscanException(Exception):
    """Base class for OpenVAS exceptions."""


#------------------------------------------------------------------------------
class VulnscanAuthFail(VulnscanException):
    """Authentication failure."""


#------------------------------------------------------------------------------
class VulnscanServerError(VulnscanException):
    """Error message from the OpenVAS server."""


#------------------------------------------------------------------------------
class VulnscanClientError(VulnscanException):
    """Error message from the OpenVAS client."""


#------------------------------------------------------------------------------
class VulnscanProfileError(VulnscanException):
    """Profile error."""


#------------------------------------------------------------------------------
class VulnscanTargetError(VulnscanException):
    """Target related errors."""


#------------------------------------------------------------------------------
class VulnscanScanError(VulnscanException):
    """Task related errors."""


#------------------------------------------------------------------------------
class VulnscanVersionError(VulnscanException):
    """Wrong version of OpenVAS server."""


#------------------------------------------------------------------------------
class VulnscanTaskNotFinishedError(VulnscanException):
    """Wrong version of OpenVAS server."""


#------------------------------------------------------------------------------
class VulnscanAuditNotRunningError(VulnscanException):
    """Wrong version of OpenVAS server."""


#------------------------------------------------------------------------------
class VulnscanAuditNotFoundError(VulnscanException):
    """Wrong version of OpenVAS server."""



#------------------------------------------------------------------------------
#
# High level interface
#
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

        :raises: VulnscanServerError, VulnscanAuthFail, VulnscanVersionError
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
            self.__manager = _get_connector(host, user, password, port, m_time_out)
        except ServerError, e:
            raise VulnscanServerError("Error while connecting to the server: %s" % e.message)
        except AuthFailedError:
            raise VulnscanAuthFail("Error while trying to authenticate into the server.")
        except RemoteVersionError:
            raise VulnscanVersionError("Invalid OpenVAS version in remote server.")

        #
        # Flow control

        # Error counter
        self.__error_counter = 0

        # Old progress
        self.__old_progress = 0.0

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

        profile = kwargs.get("profile", "Full and fast")
        call_back_end = kwargs.get("callback_end", None)
        call_back_progress = kwargs.get("callback_progress", None)
        if not (isinstance(target, basestring) or isinstance(target, Iterable)):
            raise TypeError("Expected basestring or iterable, got %r instead" % type(target))
        if not isinstance(profile, basestring):
            raise TypeError("Expected string, got %r instead" % type(profile))

        # Generate the random names used
        m_target_name = "golismero_target_%s_%s" % (target, generate_random_string(20))
        m_job_name = "golismero_scan_%s_%s" % (target, generate_random_string(20))

        # Create the target
        try:
            m_target_id = self.__manager.create_target(m_target_name, target,
                                                       "Temporal target from golismero OpenVAS plugin")
        except ServerError, e:
            raise VulnscanTargetError("The target already exits on the server. Error: %s" % e.message)

        # Get the profile ID by their name
        try:
            tmp = self.__manager.get_configs_ids(profile)
            m_profile_id = tmp[profile]
        except ServerError, e:
            raise VulnscanProfileError("The profile select not exits int the server. Error: %s" % e.message)
        except KeyError:
            raise VulnscanProfileError("The profile select not exits int the server")

        # Create task
        try:
            m_task_id = self.__manager.create_task(m_job_name, m_target_id, config=m_profile_id,
                                                   comment="scan from golismero OpenVAS plugin")
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
            self.__task_id = m_task_id
            self.__target_id = m_target_id
            self.__function_handle = self._callback(call_back_end, call_back_progress)

        return m_task_id, m_target_id

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
    def delete_scan(self, task_id):
        """
        Delete specified scan ID in the OpenVAS server.

        :param task_id: Scan ID.
        :type task_id: str

        :raises: VulnscanAuditNotFoundError
        """
        try:
            self.__manager.delete_task(task_id)
        except AuditNotRunningError, e:
            raise VulnscanAuditNotFoundError(e)

    #----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
        Delete specified target ID in the OpenVAS server.

        :param target_id: Target ID.
        :type target_id: str
        """
        self.__manager.delete_target(target_id)

    #----------------------------------------------------------------------
    def get_results(self, task_id):
        """
        Get the results associated to the scan ID.

        :param task_id: Scan ID.
        :type task_id: str

        :return: Scan results.
        :rtype: list(OpenVASResult)

        :raises: ServerError, TypeError
        """

        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        if self.__manager.is_task_running(task_id):
            raise VulnscanTaskNotFinishedError("Task is currently running. Until it not finished, you can't obtain the results.")

        try:
            m_response = self.__manager.get_results(task_id)
        except ServerError, e:
            raise VulnscanServerError("Can't get the results for the task %s. Error: %s" % (task_id, e.message))

        return VulnscanManager.transform(m_response, self.__manager.remote_server_version)

    #----------------------------------------------------------------------
    def get_progress(self, task_id):
        """
        Get the progress of a scan.

        :param task_id: Scan ID.
        :type task_id: str

        :return: Progress percentaje (between 0.0 and 100.0).
        :rtype: float
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        return self.__manager.get_tasks_progress(task_id)

    #----------------------------------------------------------------------
    def stop_audit(self, task_id):
        """
        Stops specified scan ID in the OpenVAS server.

        :param task_id: Scan ID.
        :type task_id: str

        :raises: VulnscanAuditNotFoundError
        """
        try:
            self.__manager.stop_task(self.task_id)
        except AuditNotRunningError, e:
            raise VulnscanAuditNotFoundError(e)

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
    @staticmethod
    def transform(xml_results, version="4.0"):
        """
        Transform the XML results of OpenVAS into GoLismero structures.

        :param xml_results: Input results from OpenVAS in XML format.
        :type xml_results: Element

        :param version: OpenVAS result version.
        :type version: str

        :return: Results in GoLismero format.
        :rtype: list(OpenVASResult)

        :raises: ValueError, VulnscanVersionError
        """
        if version == "4.0":
            return _OMPv4.transform(xml_results)
        else:
            raise VulnscanVersionError()

    #----------------------------------------------------------------------
    @setInterval(10.0)
    def _callback(self, func_end, func_status):
        """
        This callback function is called periodically from a timer.

        :param func_end: Function called when task end.
        :type func_end: funtion pointer

        :param func_status: Function called for update task status.
        :type func_status: funtion pointer
        """
        # Check if audit was finished
        try:
            if not self.__manager.is_task_running(self.task_id):
                # Task is finished. Stop the callback interval
                self.__function_handle.set()

                # Call the callback function
                if func_end:
                    func_end()

                # Reset error counter
                self.__error_counter = 0

        except (ClientError, ServerError), e:
            self.__error_counter += 1

            # Checks for error number
            if self.__error_counter >= 5:
                # Stop the callback interval
                self.__function_handle.set()

                func_end()

        if func_status:
            try:
                t = self.get_progress(self.task_id)

                # Save old progress
                self.__old_progress = t

                func_status(1.0 if t == 0.0 else t)

            except (ClientError, ServerError), e:

                func_status(self.__old_progress)


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
# OMP low level exceptions
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


class RemoteVersionError(Error):
    """Authentication failed."""


class AuditNotRunningError(Error):
    """Audit is not running."""


class AuditNotFoundError(Error):
    """Audit not found."""


#------------------------------------------------------------------------------
#
# OMP Methods and utils
#
#------------------------------------------------------------------------------
def _get_connector(host, username, password, port=9390, timeout=None):
    """
    Get concrete connector version for server.

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

    :return: _OMP subtype.
    :rtype: _OMP

    :raises: RemoteVersionError, ServerError, AuthFailedError, TypeError
    """

    manager = _ConnectionManager(host, username, password, port, timeout)

    # Make concrete connector from version
    if manager.protocol_version == "4.0":
        return _OMPv4(manager)
    else:
        raise RemoteVersionError("Unknown OpenVAS version for remote host.")


#------------------------------------------------------------------------------
class _ConnectionManager(object):
    """
    Connection manager for OMP objects.
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

        self.__host = host
        self.__username = username
        self.__password = password
        self.__port = port

        # Controls for timeout
        self.__timeout = _ConnectionManager.TIMEOUT
        if timeout:
            self.__timeout = timeout

        # Synchronizes access to the socket,
        # which is shared by all threads in this plugin
        self.__socket_lock = RLock()
        self.socket = None

        # Make the connection
        self._connect()

        # Get version
        self.__version = self._get_protocol_version()

    #----------------------------------------------------------------------
    #
    # PROTECTED METHODS
    #
    #----------------------------------------------------------------------
    def _connect(self):
        """
        Makes the connection and initializes the socket.

        :raises: ServerError, AuthFailedError, TypeError
        """

        # Get the timeout
        timeout = _ConnectionManager.TIMEOUT
        if self.__timeout:
            timeout = self.__timeout

        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.__host, int(self.__port)))
        except socket.error, e:
            raise ServerError(str(e))
        try:
            self.socket = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1)
        except Exception, e:
            raise ServerError(str(e))

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

        :raises: AuthFailedError, TypeError
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
            self.make_xml_request(m_request)
        except ClientError:
            raise AuthFailedError(username)

    #----------------------------------------------------------------------
    def _get_protocol_version(self):
        """
        Get OMP protocol version

        :return: version of protocol
        :rtype: str

        :raises: ServerError, RemoteVersionError
        """
        response = self.make_xml_request('<get_version/>', xml_result=True)

        v = response.find("version").text

        if not v:
            raise RemoteVersionError("Unknown remote server version")
        else:
            return v

    #----------------------------------------------------------------------
    def _send(self, in_data):
        """Send OMP data to the manager and read the result.

        `in_data` may be either an unicode string, an utf-8 encoded
        string or an etree Element. The result is as an etree Element.

        :param in_data: data to send.
        :type in_data: str | ElementTree

        :return: XML tree element.
        :rtype: `ElementTree`

        :raises: ServerError
        """
        # Make sure the data is a string.
        if etree.iselement(in_data):
            in_data = etree.dump(in_data)
        if isinstance(in_data, unicode):
            in_data = in_data.encode('utf-8')

        # Synchronize access to the socket.
        with self.__socket_lock:

            # Send the data to the server.
            try:
                self.socket.sendall(in_data)
            except socket.error:
                raise ServerError("Can't connect to the server.")

            # Get the response from the server.
            tree = None
            data = ""
            try:
                while True:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                    # We use this tip for avoid socket blocking:
                    # If xml is correct, we're finished to receive info. Otherwise,
                    # continue receiving
                    try:
                        tree = etree.fromstring(data)
                    except Exception:
                        continue
                    break
            except socket.error, e:
                raise ServerError("Can't receive info from the server: %s" % e)

            # if tree is None:
            if tree is None:
                tree = etree.fromstring(data)

            # Return the parsed response.
            return tree

    #----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
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
        :rtype: `ElementTree`|str

        :raises: ClientError, ServerError, TypeError, ValueError
        """
        response = self._send(xmldata)

        # Check the response
        if response is None:
            raise TypeError("Expected ElementTree, got '%s' instead" % type(response))

        status = response.get('status', None)

        if status is None:
            raise ValueError('response is missing status: %s' % etree.tostring(response))

        if status.startswith('4'):
            raise ClientError("[%s] %s: %s" % (status,
                                               response.tag,
                                               response.get('status_text')))

        elif status.startswith('5'):
            raise ServerError("[%s] %s: %s" % (status,
                                               response.tag,
                                               response.get('status_text')))
        if xml_result:
            return response
        else:
            return response.text


    #----------------------------------------------------------------------
    #
    # PROPERTIES
    #
    #----------------------------------------------------------------------
    @property
    def protocol_version(self):
        """
        :return: Get protocol version.
        :rtype: str
        """
        return self.__version


#------------------------------------------------------------------------------
#
# OMP low level interface
#
#------------------------------------------------------------------------------
class _OMP(object):
    """
    OMP interface
    """

    #----------------------------------------------------------------------
    def __init__(self, omp_manager):
        """
        Constructor.

        :param omp_manager: _OMPManager object.
        :type omp_manager: _ConnectionManager
        """
        if not isinstance(omp_manager, _ConnectionManager):
            raise TypeError("Expected _ConnectionManager, got '%s' instead" % type(omp_manager))

        self._manager = omp_manager

    #----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    #----------------------------------------------------------------------
    def delete_task(self, task_id):
        """
        Delete a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def stop_task(self, task_id):
        """
        Stops a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

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

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

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

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
        Delete a target in OpenVAS server.

        :param target_id: target id
        :type target_id: str

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_configs(self, config_id=None):
        """
        Get information about the configs in the server.

        If name param is provided, only get the config associated to this name.

        :param config_id: config id to get
        :type config_id: str

        :return: `ElementTree`

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_configs_ids(self, name=None):
        """
        Get information about the configured profiles (configs)in the server.

        If name param is provided, only get the ID associated to this name.

        :param name: config name to get
        :type name: str

        :return: a dict with the format: {config_name: config_ID}

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_tasks(self, task_id=None):
        """
        Get information about the configured profiles in the server.

        If name param is provided, only get the task associated to this name.

        :param task_id: task id to get
        :type task_id: str

        :return: `ElementTree`

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_tasks_ids(self, name=None):
        """
        Get IDs of tasks of the server.

        If name param is provided, only get the ID associated to this name.

        :param name: task name to get
        :type name: str

        :return: a dict with the format: {task_name: task_ID}

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_tasks_progress(self, task_id):
        """
        Get the progress of the task.

        :param task_id: ID of the task
        :type task_id: str

        :return: a float number between 0-100
        :rtype: float

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_tasks_ids_by_status(self, status="Done"):
        """
        Get IDs of tasks of the server depending of their status.

        Allowed status are: "Done", "Paused", "Running", "Stopped".

        If name param is provided, only get the ID associated to this name.

        :param status: get task with this status
        :type status: str - ("Done" |"Paused" | "Running" | "Stopped".)

        :return: a dict with the format: {task_name: task_ID}

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_task_status(self, task_id):
        """
        Get task status

        :param task_id: ID of task to start.
        :type task_id: str

        :return: string with status text.
        :rtype: str

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def is_task_running(self, task_id):
        """
        Return true if task is running

        :param task_id: ID of task to start.
        :type task_id: str

        :return: bool
        :rtype: bool

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def get_results(self, task_id=None):
        """
        Get the results associated to the scan ID.

        :param task_id: ID of scan to get. All if not provided
        :type task_id: str

        :return: xml object
        :rtype: `ElementTree`

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    def start_task(self, task_id):
        """
        Start a task.

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: ClientError, ServerError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    @staticmethod
    def transform(xml_results):
        """
        Transform the XML results of OpenVAS into GoLismero structures.

        :param xml_results: Input results from OpenVAS in XML format.
        :type xml_results: Element

        :return: Results in GoLismero format.
        :rtype: list(OpenVASResult)

        :raises: ValueError
        """
        raise NotImplementedError()

    #----------------------------------------------------------------------
    @property
    def remote_server_version(self):
        """
        Get OMP protocol version

        :return: version of protocol
        :rtype: str
        """
        return self._manager.protocol_version


#------------------------------------------------------------------------------
#
# OMPv4 implementation
#
#------------------------------------------------------------------------------
class _OMPv4(_OMP):
    """
    Internal manager for OpenVAS low level operations.

    ..note:
        This class is based in code from the original OpenVAS plugin:

        https://pypi.python.org/pypi/OpenVAS.omplib

    ..warning:
        This code is only compatible with OMP 4.0.
    """

    #----------------------------------------------------------------------
    def __init__(self, omp_manager):
        """
        Constructor.

        :param omp_manager: _OMPManager object.
        :type omp_manager: _ConnectionManager
        """
        # Call to super
        super(_OMPv4, self).__init__(omp_manager)

    #----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    #----------------------------------------------------------------------
    def delete_task(self, task_id):
        """
        Delete a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: AuditNotFoundError, ServerError
        """
        request = """<delete_task task_id="%s" />""" % task_id

        try:
            self._manager.make_xml_request(request, xml_result=True)
        except ClientError:
            raise AuditNotFoundError()

    #----------------------------------------------------------------------
    def stop_task(self, task_id):
        """
        Stops a task in OpenVAS server.

        :param task_id: task id
        :type task_id: str

        :raises: ServerError, AuditNotFoundError
        """

        request = """<stop_task task_id="%s" />""" % task_id
        try:
            self._manager.make_xml_request(request, xml_result=True)
        except ClientError:
            raise AuditNotFoundError()

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

        :raises: ClientError, ServerError
        """

        if not config:
            config = "Full and fast"

        request = """<create_task>
            <name>%s</name>
            <comment>%s</comment>
            <config id="%s"/>
            <target id="%s"/>
            </create_task>""" % (name, comment, config, target)

        return self._manager.make_xml_request(request, xml_result=True).get("id")

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

        :raises: ClientError, ServerError
        """
        if isinstance(hosts, str):
            m_targets = hosts
        elif isinstance(hosts, Iterable):
            m_targets = ",".join(hosts)

        request = """<create_target>
            <name>%s</name>
            <hosts>%s</hosts>
            <comment>%s</comment>
        </create_target>""" % (name, m_targets, comment)

        return self._manager.make_xml_request(request, xml_result=True).get("id")

    #----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
        Delete a target in OpenVAS server.

        :param target_id: target id
        :type target_id: str

        :raises: ClientError, ServerError
        """

        request = """<delete_target target_id="%s" />""" % target_id

        self._manager.make_xml_request(request, xml_result=True)

    #----------------------------------------------------------------------
    def get_configs(self, config_id=None):
        """
        Get information about the configs in the server.

        If name param is provided, only get the config associated to this name.

        :param config_id: config id to get
        :type config_id: str

        :return: `ElementTree`

        :raises: ClientError, ServerError
        """
        # Recover all config from OpenVAS
        if config_id:
            return self._manager.make_xml_request('<get_configs config_id="%s"/>' % config_id, xml_result=True)
        else:
            return self._manager.make_xml_request("<get_configs />", xml_result=True)

    #----------------------------------------------------------------------
    def get_configs_ids(self, name=None):
        """
        Get information about the configured profiles (configs)in the server.

        If name param is provided, only get the ID associated to this name.

        :param name: config name to get
        :type name: str

        :return: a dict with the format: {config_name: config_ID}

        :raises: ClientError, ServerError
        """
        m_return = {}

        for x in self.get_configs().findall("config"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name: m_return[name]}
        else:
            return m_return

    #----------------------------------------------------------------------
    def get_tasks(self, task_id=None):
        """
        Get information about the configured profiles in the server.

        If name param is provided, only get the task associated to this name.

        :param task_id: task id to get
        :type task_id: str

        :return: `ElementTree` | None

        :raises: ClientError, ServerError
        """
        # Recover all config from OpenVAS
        if task_id:
            return self._manager.make_xml_request('<get_tasks id="%s"/>' % task_id,
                                                  xml_result=True).find('.//task[@id="%s"]' % task_id)
        else:
            return self._manager.make_xml_request("<get_tasks />", xml_result=True)

    #----------------------------------------------------------------------
    def is_task_running(self, task_id):
        """
        Return true if task is running

        :param task_id: ID of task to start.
        :type task_id: str

        :return: bool
        :rtype: bool

        :raises: ClientError, ServerError
        """
        # Get status with xpath
        status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        return status.text in ("Running", "Requested")

    #----------------------------------------------------------------------
    def get_tasks_ids(self, name=None):
        """
        Get IDs of tasks of the server.

        If name param is provided, only get the ID associated to this name.

        :param name: task name to get
        :type name: str

        :return: a dict with the format: {task_name: task_ID}

        :raises: ClientError, ServerError
        """

        m_return = {}

        for x in self.get_tasks().findall("task"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name: m_return[name]}
        else:
            return m_return

    #----------------------------------------------------------------------
    def get_task_status(self, task_id):
        """
        Get task status

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: ClientError, ServerError
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        return status.text

    #----------------------------------------------------------------------
    def get_tasks_progress(self, task_id):
        """
        Get the progress of the task.

        :param task_id: ID of the task
        :type task_id: str

        :return: a float number between 0-100
        :rtype: float

        :raises: ClientError, ServerError
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_sum_progress = 0.0  # Partial progress
        m_progress_len = 0.0  # All of tasks

        # Get status with xpath
        tasks = self.get_tasks()
        status = tasks.find('.//task[@id="%s"]/status' % task_id)

        if status is None:
            raise ServerError("Task not found")

        if status.text in ("Running", "Pause Requested", "Paused"):
            h = tasks.findall('.//task[@id="%s"]/progress/host_progress/host' % task_id)

            if h is not None:
                m_progress_len += float(len(h))
                m_sum_progress += sum([float(x.tail) for x in h])

        elif status.text in ("Delete Requested", "Done", "Stop Requested", "Stopped", "Internal Error"):
            return 100.0  # Task finished

        try:
            return m_sum_progress/m_progress_len
        except ZeroDivisionError:
            return 0.0

    #----------------------------------------------------------------------
    def get_tasks_ids_by_status(self, status="Done"):
        """
        Get IDs of tasks of the server depending of their status.

        Allowed status are: "Done", "Paused", "Running", "Stopped".

        If name param is provided, only get the ID associated to this name.

        :param status: get task with this status
        :type status: str - ("Done" |"Paused" | "Running" | "Stopped".)

        :return: a dict with the format: {task_name: task_ID}

        :raises: ClientError, ServerError
        """
        if status not in ("Done", "Paused", "Running", "Stopped"):
            raise ValueError("Requested status are not allowed")

        m_task_ids = {}

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

        :raises: ClientError, ServerError
        """

        if task_id:
            m_query = '<get_results task_id="%s"/>' % task_id
        else:
            m_query = '<get_results/>'

        return self._manager.make_xml_request(m_query, xml_result=True)

    #----------------------------------------------------------------------
    def start_task(self, task_id):
        """
        Start a task.

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: ClientError, ServerError
        """
        if not isinstance(task_id, basestring):
            raise TypeError("Expected string, got %r instead" % type(task_id))

        m_query = '<start_task task_id="%s"/>' % task_id

        self._manager.make_xml_request(m_query, xml_result=True)

    #----------------------------------------------------------------------
    @staticmethod
    def transform(xml_results):
        """
        Transform the XML results of OpenVAS into GoLismero structures.

        :param xml_results: Input results from OpenVAS in XML format.
        :type xml_results: Element

        :return: Results in GoLismero format.
        :rtype: list(OpenVASResult)

        :raises: ValueError
        """
        port_regex_specific = re.compile("([\w\d\s]*)\(([\d]+)/([\w\W\d]+)\)")
        port_regex_generic = re.compile("([\w\d\s]*)/([\w\W\d]+)")
        cvss_regex = re.compile("(cvss_base_vector=[\s]*)([\w:/]+)")

        m_return = []
        m_return_append = m_return.append

        # All the results
        for l_results in xml_results.findall(".//result"):
            l_partial_result = OpenVASResult.make_empty_object()

            # Ignore log/debug messages, only get the results
            threat = l_results.find("threat")
            if threat is None:
                continue
            if threat.text in ("Log", "Debug"):
                continue

            # For each result
            for l_val in l_results.getchildren():

                l_tag = l_val.tag

                if l_tag in ("subnet", "host", "threat", "description"):
                    # All text vars can be processes both.
                    setattr(l_partial_result, l_tag, l_val.text)

                elif l_tag == "port":

                    # Looking for port as format: https (443/tcp)
                    l_port = port_regex_specific.search(l_val.text)
                    if l_port:
                            l_service = l_port.group(1)
                            l_number = int(l_port.group(2))
                            l_proto = l_port.group(3)

                            l_partial_result.port = OpenVASPort(l_service,
                                                                l_number,
                                                                l_proto)
                    else:
                        # Looking for port as format: general/tcp
                        l_port = port_regex_generic.search(l_val.text)
                        if l_port:
                            l_service = l_port.group(1)
                            l_proto = l_port.group(2)

                            l_partial_result.port = OpenVASPort(l_service,
                                                                None,
                                                                l_proto)

                elif l_tag == "nvt":

                    # The NVT Object
                    l_nvt_object = OpenVASNVT.make_empty_object()
                    l_nvt_object.oid = l_val.attrib['oid']
                    l_nvt_symbols = [x for x in dir(l_nvt_object) if not x.startswith("_")]

                    for l_nvt in l_val.getchildren():
                        l_nvt_tag = l_nvt.tag
                        if l_nvt_tag in l_nvt_symbols:
                            if l_nvt.text:  # For filter tags like <cert/>
                                if l_nvt.text.startswith("NO"):  # For filter tags like <cve>NOCVE</cve>
                                    setattr(l_nvt_object, l_nvt_tag, "")
                                else:
                                    setattr(l_nvt_object, l_nvt_tag, l_nvt.text)
                            else:
                                setattr(l_nvt_object, l_nvt_tag, "")

                    # Get CVSS
                    cvss_candidate = l_val.find("tags")
                    if cvss_candidate is not None and cvss_candidate.text:
                        # Extract data
                        cvss_tmp = cvss_regex.search(cvss_candidate.text)
                        if cvss_tmp:
                            l_nvt_object.cvss_base_vector = cvss_tmp.group(2)

                    # Add to the NVT Object
                    l_partial_result.nvt = l_nvt_object

                else:
                    # "Unrecognised tag
                    pass

            # Add to the return values
            m_return_append(l_partial_result)

        return m_return
