#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""
This file contains interfaces for OMP implementations
"""

import ssl
import socket

from threading import RLock

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

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


# ------------------------------------------------------------------------------
#
# OMP Methods and utils
#
# ------------------------------------------------------------------------------
def get_connector(host, username, password, port=9390, timeout=None):
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

	:return: OMP subtype.
	:rtype: OMP

	:raises: RemoteVersionError, ServerError, AuthFailedError, TypeError
	"""

    manager = ConnectionManager(host, username, password, port, timeout)

    # Make concrete connector from version
    if manager.protocol_version in ("4.0", "5.0", "6.0"):
        from openvas_lib.ompv4 import OMPv4
        return OMPv4(manager)
    else:
        raise RemoteVersionError("Unknown OpenVAS version for remote host.")


# ------------------------------------------------------------------------------
class ConnectionManager(object):
    """
	Connection manager for OMP objects.

	Added new way to run it: dummy mode, that simulates behavior without connect to any host.

	To enable dummy mode, set 'host' to 'dummy'.
	"""

    TIMEOUT = 10.0

    # ----------------------------------------------------------------------
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

        if not isinstance(host, str):
            raise TypeError("Expected string, got %r instead" % type(host))
        if not isinstance(username, str):
            raise TypeError("Expected string, got %r instead" % type(username))
        if isinstance(port, int):
            if not (0 < port < 65535):
                raise ValueError("Port must be between 0-65535")
        else:
            raise TypeError("Expected int, got %r instead" % type(port))
        if timeout:
            if not isinstance(timeout, int):
                raise TypeError("Expected int, got %r instead" % type(timeout))
            else:
                if timeout < 1:
                    raise ValueError("Timeout must be greater than 0")

        self.__host = host
        self.__username = username
        self.__password = password
        self.__port = port

        # Controls for timeout
        self.__timeout = ConnectionManager.TIMEOUT
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

    # ----------------------------------------------------------------------
    #
    # PROTECTED METHODS
    #
    # ----------------------------------------------------------------------
    def _connect(self):
        """
		Makes the connection and initializes the socket.

		:raises: ServerError, AuthFailedError, TypeError
		"""

        # Get the timeout
        timeout = ConnectionManager.TIMEOUT
        if self.__timeout:
            timeout = self.__timeout

        # For testing purposes
        if self.__host == "dummy":
            return

        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.__host, int(self.__port)))
        except socket.error as e:
            raise ServerError(str(e))
        try:
            self.socket = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1)
        except Exception as e:
            raise ServerError(str(e))

        # Authenticate to the server
        self._authenticate(self.__username, self.__password)

    # ----------------------------------------------------------------------
    def _authenticate(self, username, password):
        """
		Authenticate a user to the manager.

		:param username: user name
		:type username: str

		:param password: user password
		:type password: str

		:raises: AuthFailedError, TypeError
		"""
        if not isinstance(username, str):
            raise TypeError("Expected string, got %r instead" % type(username))
        if not isinstance(password, str):
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

    # ----------------------------------------------------------------------
    def _get_protocol_version(self):
        """
		Get OMP protocol version. If host is 'dummy', return 'dummy' version.

		:return: version of protocol
		:rtype: str

		:raises: ServerError, RemoteVersionError
		"""

        if self.__host == "dummy":
            return "dummy"

        response = self.make_xml_request('<get_version/>', xml_result=True)

        v = response.find("version").text

        if not v:
            raise RemoteVersionError("Unknown remote server version")
        else:
            return v

    # ----------------------------------------------------------------------
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

        if self.__host == "dummy":
            return etree.fromstring(in_data)

        # Make sure the data is a string.
        if etree.iselement(in_data):
            in_data = etree.dump(in_data)

        try:
            in_data = in_data.encode('utf-8')
        except Exception:
            pass

        # Synchronize access to the socket.
        with self.__socket_lock:

            # Send the data to the server.
            try:
                self.socket.sendall(in_data)
            except socket.error:
                raise ServerError("Can't connect to the server.")

            # Get the response from the server.
            tree = None
            data = []
            try:
                while True:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    data.append(chunk)

                    # We use this tip for avoid socket blocking:
                    # If xml is correct, we're finished to receive info. Otherwise,
                    # continue receiving
                    try:
                        tree = etree.fromstring(b"".join(data))
                    except Exception:
                        continue
                    break
            except socket.error as e:
                raise ServerError("Can't receive info from the server: %s" % e)

            # if tree is None:
            if tree is None:
                tree = etree.ElementTree()
                return tree

            # Return the parsed response.
            return tree

    # ----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    # ----------------------------------------------------------------------
    def close(self):
        """Close the connection to the manager."""
        if self.__host == "dummy":
            return

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

    # ----------------------------------------------------------------------
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
        if not isinstance(xmldata, str):
            raise TypeError("Expected str, got '%s' instead" % type(xmldata))
        if not isinstance(xml_result, bool):
            raise TypeError("Expected bool, got '%s' instead" % type(xml_result))

        response = self._send(xmldata)

        # Check the response
        if response is None:
            raise TypeError("Expected ElementTree, got '%s' instead" % type(response))

        try:
            status = response.get('status', None)
        except:
            raise ValueError('Missing status property in response')

        if status is None or status == '':
            raise ValueError('response is missing status: %s' % etree.tostring(response))

        if status.startswith('4'):
            raise ClientError("[%s] %s: %s" % (status,
                                               response.tag,
                                               response.get('status_text')))

        elif status.startswith('5'):
            raise ServerError("[%s] %s: %s" % (status,
                                               response.tag,
                                               response.get('status_text')))
        elif status.startswith('2'):
            if xml_result:
                return response
            else:
                return response.get("status_text")
        else:
            raise ServerError("Invalid status code returned by server: %s" % status)

    # ----------------------------------------------------------------------
    #
    # PROPERTIES
    #
    # ----------------------------------------------------------------------
    @property
    def protocol_version(self):
        """
		:return: Get protocol version.
		:rtype: str
		"""
        return self.__version


#
#
# Some code and ideas of the next code has been taken from the official
# OpenVAS library:
#
# https://pypi.python.org/pypi/OpenVAS.omplib
#
#
#

# ------------------------------------------------------------------------------
#
# OMP low level exceptions
#
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
#
# OMP low level interface
#
# ------------------------------------------------------------------------------
class OMP(object):
    """
	OMP abstract class for OMP implementations
	"""

    # ----------------------------------------------------------------------
    def __init__(self, omp_manager):
        """
		Constructor.

		:param omp_manager: _OMPManager object.
		:type omp_manager: ConnectionManager
		"""
        if not isinstance(omp_manager, ConnectionManager):
            raise TypeError("Expected ConnectionManager, got '%s' instead" % type(omp_manager))

        self._manager = omp_manager

    # ----------------------------------------------------------------------
    #
    # PUBLIC METHODS
    #
    # ----------------------------------------------------------------------
    def delete_task(self, task_id):
        """
		Delete a task in OpenVAS server.

		:param task_id: task id
		:type task_id: str

		:raises: ClientError, ServerError
		"""
        raise NotImplementedError()

    # ----------------------------------------------------------------------
    def stop_task(self, task_id):
        """
		Stops a task in OpenVAS server.

		:param task_id: task id
		:type task_id: str

		:raises: ClientError, ServerError
		"""
        raise NotImplementedError()

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    def delete_target(self, target_id):
        """
		Delete a target in OpenVAS server.

		:param target_id: target id
		:type target_id: str

		:raises: ClientError, ServerError
		"""
        raise NotImplementedError()

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    def start_task(self, task_id):
        """
		Start a task.

		:param task_id: ID of task to start.
		:type task_id: str

		:raises: ClientError, ServerError
		"""
        raise NotImplementedError()

    # ----------------------------------------------------------------------
    @property
    def remote_server_version(self):
        """
		Get OMP protocol version

		:return: version of protocol
		:rtype: str
		"""
        return self._manager.protocol_version

# __all__ = [m for m in globals() if m.endswith("Error")]
