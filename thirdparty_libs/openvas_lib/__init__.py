#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""
OpenVAS connector for OMP protocol.

This is a replacement of the official library OpenVAS python library,
because the official library doesn't work with OMP v4.0.
"""

import os
import logging

try:
	from xml.etree import cElementTree as etree
except ImportError:
	from xml.etree import ElementTree as etree

from collections import Iterable

from openvas_lib.data import *
from openvas_lib.utils import *
from openvas_lib.common import *

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
# Stand alone parser
#
# ------------------------------------------------------------------------------
def report_parser_from_text(text, ignore_log_info=True):
	"""
    This functions transform XML OpenVas file report to OpenVASResult object structure.

    To pass string as parameter:
    >>> xml='<report extension="xml" type="scan" id="aaaa" content_type="text/xml" format_id="a994b278-1f62-11e1-96ac-406186ea4fc5"></report>'
    >>> report_parser_from_text(f)
    [OpenVASResult]

    Language specification: http://www.openvas.org/omp-4-0.html

    :param text: xml text to parse.
    :type text: str

    :param ignore_log_info: Ignore Threats with Log and Debug info
    :type ignore_log_info: bool

    :raises: etree.ParseError, IOError, TypeError

    :return: list of OpenVASResult structures.
    :rtype: list(OpenVASResult)
    """
	if not isinstance(text, str):
		raise TypeError("Expected str, got '%s' instead" % type(text))

	try:
		import cStringIO as S
	except ImportError:
		import StringIO as S

	return report_parser(S.StringIO(text), ignore_log_info)


def report_parser(path_or_file, ignore_log_info=True):
	"""
    This functions transform XML OpenVas file report to OpenVASResult object structure.

    To pass StringIO file as parameter, you must do that:
    >>> import StringIO
    >>> xml='<report extension="xml" type="scan" id="aaaa" content_type="text/xml" format_id="a994b278-1f62-11e1-96ac-406186ea4fc5"></report>'
    >>> f=StringIO.StringIO(xml)
    >>> report_parser(f)
    [OpenVASResult]

    To pass a file path:
    >>> xml_path='/home/my_user/openvas_result.xml'
    >>> report_parser(xml_path)
    [OpenVASResult]

    Language specification: http://www.openvas.org/omp-4-0.html

    :param path_or_file: path or file descriptor to xml file.
    :type path_or_file: str | file | StringIO

    :param ignore_log_info: Ignore Threats with Log and Debug info
    :type ignore_log_info: bool

    :raises: etree.ParseError, IOError, TypeError

    :return: list of OpenVASResult structures.
    :rtype: list(OpenVASResult)
    """
	if isinstance(path_or_file, str):
		if not os.path.exists(path_or_file):
			raise IOError("File %s not exits." % path_or_file)
		if not os.path.isfile(path_or_file):
			raise IOError("%s is not a file." % path_or_file)
	else:
		if not getattr(getattr(path_or_file, "__class__", ""), "__name__", "") in ("file", "StringIO", "StringO"):
			raise TypeError("Expected str or file, got '%s' instead" % type(path_or_file))

	# Parse XML file
	try:
		xml_parsed = etree.parse(path_or_file)
	except etree.ParseError:
		raise etree.ParseError("Invalid XML file. Ensure file is correct and all tags are properly closed.")

	# Use this method, because API not exposes real path and if you write isisntance(xml_results, Element)
	# doesn't works
	if type(xml_parsed).__name__ == "Element":
		xml = xml_parsed
	elif type(xml_parsed).__name__ == "ElementTree":
		xml = xml_parsed.getroot()
	else:
		raise TypeError("Expected ElementTree or Element, got '%s' instead" % type(xml_parsed))

	# Check valid xml format
	if "id" not in xml.keys():
		raise ValueError("XML format is not valid, doesn't contains id attribute.")

	# Regex
	port_regex_specific = re.compile("([\w\d\s]*)\(([\d]+)/([\w\W\d]+)\)")
	port_regex_generic = re.compile("([\w\d\s]*)/([\w\W\d]+)")
	cvss_regex = re.compile("(cvss_base_vector=[\s]*)([\w:/]+)")
	vulnerability_IDs = ("cve", "bid", "bugtraq")

	m_return = []
	m_return_append = m_return.append

	# All the results
	for l_results in xml.findall(".//result"):
		l_partial_result = OpenVASResult()

		# Id
		l_vid = None
		try:
			l_vid = l_results.get("id")
			l_partial_result.id = l_vid
		except TypeError as e:
			logging.warning("%s is not a valid vulnerability ID, skipping vulnerability..." % l_vid)
			logging.debug(e)
			continue

		# --------------------------------------------------------------------------
		# Filter invalid vulnerability
		# --------------------------------------------------------------------------
		threat = l_results.find("threat")
		if threat is None:
			logging.warning("Vulnerability %s can't has 'None' as thread value, skipping vulnerability..." % l_vid)
			continue
		else:
			# Valid threat?
			if threat.text not in OpenVASResult.risk_levels:
				logging.warning("%s is not a valid risk level for %s vulnerability. skipping vulnerability..."
				                % (threat.text,
				                   l_vid))
				continue

		# Ignore log/debug messages, only get the results
		if threat.text in ("Log", "Debug") and ignore_log_info is True:
			continue

		# For each result
		for l_val in l_results.getchildren():

			l_tag = l_val.tag

			# --------------------------------------------------------------------------
			# Common properties: subnet, host, threat, raw_description
			# --------------------------------------------------------------------------
			if l_tag in ("subnet", "host", "threat"):
				# All text vars can be processes both.
				try:
					setattr(l_partial_result, l_tag, l_val.text)
				except (TypeError, ValueError) as e:
					logging.warning(
						"%s is not a valid value for %s property in %s vulnerability. skipping vulnerability..."
						% (l_val.text,
						   l_tag,
						   l_partial_result.id))
					logging.debug(e)
					continue

			elif l_tag == "description":
				try:
					setattr(l_partial_result, "raw_description", l_val.text)
				except TypeError as e:
					logging.warning("%s is not a valid description for %s vulnerability. skipping vulnerability..."
					                % (l_val.text,
					                   l_vid))
					logging.debug(e)
					continue

			# --------------------------------------------------------------------------
			# Port
			# --------------------------------------------------------------------------
			elif l_tag == "port":

				# Looking for port as format: https (443/tcp)
				l_port = port_regex_specific.search(l_val.text)
				if l_port:
					l_service = l_port.group(1)
					l_number = int(l_port.group(2))
					l_proto = l_port.group(3)

					try:
						l_partial_result.port = OpenVASPort(l_service,
						                                    l_number,
						                                    l_proto)
					except (TypeError, ValueError) as e:
						logging.warning("%s is not a valid port for %s vulnerability. skipping vulnerability..."
						                % (l_val.text,
						                   l_vid))
						logging.debug(e)
						continue
				else:
					# Looking for port as format: general/tcp
					l_port = port_regex_generic.search(l_val.text)
					if l_port:
						l_service = l_port.group(1)
						l_proto = l_port.group(2)

						try:
							l_partial_result.port = OpenVASPort(l_service, 0, l_proto)
						except (TypeError, ValueError) as e:
							logging.warning("%s is not a valid port for %s vulnerability. skipping vulnerability..."
							                % (l_val.text,
							                   l_vid))
							logging.debug(e)
							continue

			# --------------------------------------------------------------------------
			# NVT
			# --------------------------------------------------------------------------
			elif l_tag == "nvt":

				# The NVT Object
				l_nvt_object = OpenVASNVT()
				try:
					l_nvt_object.oid = l_val.attrib['oid']
				except TypeError as e:
					logging.warning("%s is not a valid NVT oid for %s vulnerability. skipping vulnerability..."
					                % (l_val.attrib['oid'],
					                   l_vid))
					logging.debug(e)
					continue

				# Sub nodes of NVT tag
				l_nvt_symbols = [x for x in dir(l_nvt_object) if not x.startswith("_")]

				for l_nvt in l_val.getchildren():
					l_nvt_tag = l_nvt.tag

					# For each xml tag...
					if l_nvt_tag in l_nvt_symbols:

						# For tags with content, like: <cert>blah</cert>
						if l_nvt.text:

							# For filter tags like <cve>NOCVE</cve>
							if l_nvt.text.startswith("NO"):
								try:
									setattr(l_nvt_object, l_nvt_tag, "")
								except (TypeError, ValueError) as e:
									logging.warning(
										"Empty value is not a valid NVT value for %s property in %s vulnerability. skipping vulnerability..."
										% (l_nvt_tag,
										   l_vid))
									logging.debug(e)
									continue

							# Tags with valid content
							else:
								# --------------------------------------------------------------------------
								# Vulnerability IDs: CVE-..., BID..., BugTraq...
								# --------------------------------------------------------------------------
								if l_nvt_tag.lower() in vulnerability_IDs:
									l_nvt_text = getattr(l_nvt, "text", "")
									try:
										setattr(l_nvt_object, l_nvt_tag, l_nvt_text.split(","))
									except (TypeError, ValueError) as e:
										logging.warning(
											"%s value is not a valid NVT value for %s property in %s vulnerability. skipping vulnerability..."
											% (l_nvt_text,
											   l_nvt_tag,
											   l_vid))
										logging.debug(e)
									continue

								else:
									l_nvt_text = getattr(l_nvt, "text", "")
									try:
										setattr(l_nvt_object, l_nvt_tag, l_nvt_text)
									except (TypeError, ValueError) as e:
										logging.warning(
											"%s value is not a valid NVT value for %s property in %s vulnerability. skipping vulnerability..."
											% (l_nvt_text,
											   l_nvt_tag,
											   l_vid))
										logging.debug(e)
									continue

						# For filter tags without content, like: <cert/>
						else:
							try:
								setattr(l_nvt_object, l_nvt_tag, "")
							except (TypeError, ValueError) as e:
								logging.warning(
									"Empty value is not a valid NVT value for %s property in %s vulnerability. skipping vulnerability..."
									% (l_nvt_tag,
									   l_vid))
								logging.debug(e)
								continue

				# Get CVSS
				cvss_candidate = l_val.find("tags")
				if cvss_candidate is not None and getattr(cvss_candidate, "text", None):
					# Extract data
					cvss_tmp = cvss_regex.search(cvss_candidate.text)
					if cvss_tmp:
						l_nvt_object.cvss_base_vector = cvss_tmp.group(2) if len(cvss_tmp.groups()) >= 2 else ""

				# Add to the NVT Object
				try:
					l_partial_result.nvt = l_nvt_object
				except (TypeError, ValueError) as e:
					logging.warning(
						"NVT oid %s is not a valid NVT value for %s vulnerability. skipping vulnerability..."
						% (l_nvt_object.oid,
						   l_vid))
					logging.debug(e)
					continue

			# --------------------------------------------------------------------------
			# Unknown tags
			# --------------------------------------------------------------------------
			else:
				# Unrecognised tag
				logging.warning("%s tag unrecognised" % l_tag)

		# Add to the return values
		m_return_append(l_partial_result)

	return m_return


# ------------------------------------------------------------------------------
#
# High level exceptions
#
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class VulnscanException(Exception):
	"""Base class for OpenVAS exceptions."""


# ------------------------------------------------------------------------------
class VulnscanAuthFail(VulnscanException):
	"""Authentication failure."""


# ------------------------------------------------------------------------------
class VulnscanServerError(VulnscanException):
	"""Error message from the OpenVAS server."""


# ------------------------------------------------------------------------------
class VulnscanClientError(VulnscanException):
	"""Error message from the OpenVAS client."""


# ------------------------------------------------------------------------------
class VulnscanProfileError(VulnscanException):
	"""Profile error."""


# ------------------------------------------------------------------------------
class VulnscanTargetError(VulnscanException):
	"""Target related errors."""


# ------------------------------------------------------------------------------
class VulnscanScanError(VulnscanException):
	"""Task related errors."""


# ------------------------------------------------------------------------------
class VulnscanVersionError(VulnscanException):
	"""Wrong version of OpenVAS server."""


# ------------------------------------------------------------------------------
class VulnscanTaskNotFinishedError(VulnscanException):
	"""Wrong version of OpenVAS server."""


# ------------------------------------------------------------------------------
class VulnscanAuditNotRunningError(VulnscanException):
	"""Wrong version of OpenVAS server."""


# ------------------------------------------------------------------------------
class VulnscanAuditNotFoundError(VulnscanException):
	"""Wrong version of OpenVAS server."""


# ------------------------------------------------------------------------------
#
# High level interface
#
# ------------------------------------------------------------------------------
class AuditNotRunning(object):
    pass


class VulnscanManager(object):
	"""
    High level interface to the OpenVAS server.

    ..warning: Only compatible with OMP 4.0.
    """

	# ----------------------------------------------------------------------
	#
	# Methods to manage OpenVAS
	#
	# ----------------------------------------------------------------------
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

		if not isinstance(host, str):
			raise TypeError("Expected string, got %r instead" % type(host))
		if not isinstance(user, str):
			raise TypeError("Expected string, got %r instead" % type(user))
		if not isinstance(password, str):
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
			self.__manager = get_connector(host, user, password, port, m_time_out)
		except ServerError as e:
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

		# Init various vars
		self.__function_handle = None
		self.__task_id = None
		self.__target_id = None

	# ----------------------------------------------------------------------
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
                manager = VulnscanManager("localhost", "admin", "admin)

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
		if not (isinstance(target, str) or isinstance(target, Iterable)):
			raise TypeError("Expected str or iterable, got %r instead" % type(target))
		if not isinstance(profile, str):
			raise TypeError("Expected string, got %r instead" % type(profile))

		# Generate the random names used
		m_target_name = "openvas_lib_target_%s_%s" % (target, generate_random_string(20))
		m_job_name = "openvas_lib_scan_%s_%s" % (target, generate_random_string(20))

		# Create the target
		try:
			m_target_id = self.__manager.create_target(m_target_name, target,
			                                           "Temporal target from OpenVAS Lib")
		except ServerError as e:
			raise VulnscanTargetError("The target already exits on the server. Error: %s" % e.message)

		# Get the profile ID by their name
		try:
			tmp = self.__manager.get_configs_ids(profile)
			m_profile_id = tmp[profile]
		except ServerError as e:
			raise VulnscanProfileError("The profile select not exits int the server. Error: %s" % e.message)
		except KeyError:
			raise VulnscanProfileError("The profile select not exits int the server")

		# Create task
		try:
			m_task_id = self.__manager.create_task(m_job_name, m_target_id, config=m_profile_id,
			                                       comment="scan from OpenVAS lib")
		except ServerError as e:
			raise VulnscanScanError("The target selected doesnn't exist in the server. Error: %s" % e.message)

		# Start the scan
		try:
			self.__manager.start_task(m_task_id)
		except ServerError as e:
			raise VulnscanScanError(
				"Unknown error while try to start the task '%s'. Error: %s" % (m_task_id, e.message))

		# Callback is set?
		if call_back_end or call_back_progress:
			# schedule a function to run each 10 seconds to check the estate in the server
			self.__task_id = m_task_id
			self.__target_id = m_target_id
			self.__function_handle = self._callback(call_back_end, call_back_progress)

		return m_task_id, m_target_id

	# ----------------------------------------------------------------------
	@property
	def task_id(self):
		"""
        :returns: OpenVAS task ID.
        :rtype: str
        """
		return self.__task_id

	# ----------------------------------------------------------------------
	@property
	def target_id(self):
		"""
        :returns: OpenVAS target ID.
        :rtype: str
        """
		return self.__target_id

	# ----------------------------------------------------------------------
	def delete_scan(self, task_id):
		"""
        Delete specified scan ID in the OpenVAS server.

        :param task_id: Scan ID.
        :type task_id: str

        :raises: VulnscanAuditNotFoundError
        """
		try:
			self.__manager.delete_task(task_id)
		except AuditNotRunningError as e:
			raise VulnscanAuditNotFoundError(e)

	# ----------------------------------------------------------------------
	def delete_target(self, target_id):
		"""
        Delete specified target ID in the OpenVAS server.

        :param target_id: Target ID.
        :type target_id: str
        """
		self.__manager.delete_target(target_id)

	# ----------------------------------------------------------------------
	def get_results(self, task_id):
		"""
        Get the results associated to the scan ID.

        :param task_id: Scan ID.
        :type task_id: str

        :return: Scan results.
        :rtype: list(OpenVASResult)

        :raises: ServerError, TypeError
        """

		if not isinstance(task_id, str):
			raise TypeError("Expected string, got %r instead" % type(task_id))

		if self.__manager.is_task_running(task_id):
			raise VulnscanTaskNotFinishedError(
				"Task is currently running. Until it not finished, you can't obtain the results.")

		try:
			m_response = self.__manager.get_results(task_id)
		except ServerError as e:
			raise VulnscanServerError("Can't get the results for the task %s. Error: %s" % (task_id, e.message))

		return report_parser(m_response)

	# ----------------------------------------------------------------------
	def get_report_id(self, scan_id):

		if not isinstance(scan_id, str):
			raise TypeError("Expected string, got %r instead" % type(scan_id))

		return self.__manager.get_report_id(scan_id)

	# ----------------------------------------------------------------------
	def get_report_html(self, report_id):

		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		return self.__manager.get_report_html(report_id)
		# ----------------------------------------------------------------------

	# ----------------------------------------------------------------------
	def get_report_xml(self, report_id):

		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		return self.__manager.get_report_xml(report_id)
		# ----------------------------------------------------------------------

	# ----------------------------------------------------------------------
	def get_report_pdf(self, report_id):

		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		return self.__manager.get_report_pdf(report_id)

	# ----------------------------------------------------------------------
	def get_progress(self, task_id):
		"""
        Get the progress of a scan.

        :param task_id: Scan ID.
        :type task_id: str

        :return: Progress percentage (between 0.0 and 100.0).
        :rtype: float
        """
		if not isinstance(task_id, str):
			raise TypeError("Expected string, got %r instead" % type(task_id))

		return self.__manager.get_tasks_progress(task_id)

	# ----------------------------------------------------------------------
	def stop_audit(self, task_id):
		"""
        Stops specified scan ID in the OpenVAS server.

        :param task_id: Scan ID.
        :type task_id: str

        :raises: VulnscanAuditNotFoundError
        """
		try:
			self.__manager.stop_task(self.task_id)
		except AuditNotRunningError as e:
			raise VulnscanAuditNotFoundError(e)

	# ----------------------------------------------------------------------
	@property
	def get_profiles(self):
		"""
        :return: All available profiles.
        :rtype: {profile_name: ID}
        """
		return self.__manager.get_configs_ids()

	# ----------------------------------------------------------------------
	@property
	def get_all_scans(self):
		"""
        :return: All scans.
        :rtype: {scan_name: ID}
        """
		return self.__manager.get_tasks_ids()

	# ----------------------------------------------------------------------
	@property
	def get_running_scans(self):
		"""
        :return: All running scans.
        :rtype: {scan_name: ID}
        """
		return self.__manager.get_tasks_ids_by_status("Running")

	# ----------------------------------------------------------------------
	@property
	def get_finished_scans(self):
		"""
        :return: All finished scans.
        :rtype: {scan_name: ID}
        """
		return self.__manager.get_tasks_ids_by_status("Done")

	# ----------------------------------------------------------------------
	@set_interval(10.0)
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

		except (ClientError, ServerError, Exception) as e:
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

			except (ClientError, ServerError, Exception) as e:

				func_status(self.__old_progress)


__all__ = [x for x in dir() if x.startswith("Vulnscan") or x.startswith("report_parser")]
