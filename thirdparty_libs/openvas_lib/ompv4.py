#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file contains OMPv4 implementation
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


# ------------------------------------------------------------------------------
#
# OMPv4 implementation
#
# ------------------------------------------------------------------------------
class OMPv4(OMP):
	"""
    Internal manager for OpenVAS low level operations.

    ..note:
        This class is based in code from the original OpenVAS plugin:

        https://pypi.python.org/pypi/OpenVAS.omplib

    ..warning:
        This code is only compatible with OMP 4.0.
    """

	# ----------------------------------------------------------------------
	def __init__(self, omp_manager):
		"""
        Constructor.

        :param omp_manager: _OMPManager object.
        :type omp_manager: ConnectionManager
        """
		# Call to super
		super(OMPv4, self).__init__(omp_manager)

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

        :raises: AuditNotFoundError, ServerError
        """
		request = """<delete_task task_id="%s" />""" % task_id

		try:
			self._manager.make_xml_request(request, xml_result=True)
		except ClientError:
			raise AuditNotFoundError()

	# ----------------------------------------------------------------------
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

		if not config:
			config = "Full and fast"

		request = """<create_task>
            <name>%s</name>
            <comment>%s</comment>
            <config id="%s"/>
            <target id="%s"/>
            </create_task>""" % (name, comment, config, target)

		return self._manager.make_xml_request(request, xml_result=True).get("id")

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
        from collections import Iterable
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

	# ----------------------------------------------------------------------
	def delete_target(self, target_id):
		"""
        Delete a target in OpenVAS server.

        :param target_id: target id
        :type target_id: str

        :raises: ClientError, ServerError
        """

		request = """<delete_target target_id="%s" />""" % target_id

		self._manager.make_xml_request(request, xml_result=True)

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
		# Recover all config from OpenVAS
		if config_id:
			return self._manager.make_xml_request('<get_configs config_id="%s"/>' % config_id, xml_result=True)
		else:
			return self._manager.make_xml_request("<get_configs />", xml_result=True)

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
		m_return = {}

        for x in self.get_configs().findall("config"):
            m_return[x.find("name").text] = x.get("id")

        if name:
            return {name: m_return[name]}
        else:
            return m_return

    #----------------------------------------------------------------------
    def get_targets(self, target_id=None):
        """
        Get information about the targets in the server.

        If name param is provided, only get the target associated to this name.

        :param target_id: target id to get
        :type target_id: str

        :return: `ElementTree` | None

        :raises: ClientError, ServerError
        """
        # Recover all config from OpenVAS
        if target_id:
            return self._manager.make_xml_request('<get_targets id="%s"/>' % target_id,
                xml_result=True).find('.//target[@id="%s"]' % target_id)
        else:
            return self._manager.make_xml_request("<get_targets />", xml_result=True)

    def get_targets_ids(self, name=None):
        """
        Get IDs of targets of the server.

        If name param is provided, only get the ID associated to this name.

        :param name: target name to get
        :type name: str

        :return: a dict with the format: {target_name: target_ID}

        :raises: ClientError, ServerError
        """
        m_return = {}

        for x in self.get_targets().findall("target"):
            m_return[x.find("name").text] = x.get("id")

		if name:
			return {name: m_return[name]}
		else:
			return m_return

	# ----------------------------------------------------------------------
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
		# Get status with xpath
		status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

		if status is None:
			raise ServerError("Task not found")

		return status.text in ("Running", "Requested")

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

		m_return = {}

		for x in self.get_tasks().findall("task"):
			m_return[x.find("name").text] = x.get("id")

		if name:
			return {name: m_return[name]}
		else:
			return m_return

	# ----------------------------------------------------------------------
	def get_task_status(self, task_id):
		"""
        Get task status

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: ClientError, ServerError
        """
		if not isinstance(task_id, str):
			raise TypeError("Expected string, got %r instead" % type(task_id))

		status = self.get_tasks().find('.//task[@id="%s"]/status' % task_id)

		if status is None:
			raise ServerError("Task not found")

		return status.text

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
		if not isinstance(task_id, str):
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
			return m_sum_progress / m_progress_len
		except ZeroDivisionError:
			return 0.0

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
		if status not in ("Done", "Paused", "Running", "Stopped"):
			raise ValueError("Requested status are not allowed")

		m_task_ids = {}

		for x in self.get_tasks().findall("task"):
			if x.find("status").text == status:
				m_task_ids[x.find("name").text] = x.attrib["id"]

		return m_task_ids

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

		if task_id:
			m_query = '<get_results task_id="%s"/>' % task_id
		else:
			m_query = '<get_results/>'

		return self._manager.make_xml_request(m_query, xml_result=True)

	# ----------------------------------------------------------------------
	def get_tasks_detail(self, scan_id):
		if not isinstance(scan_id, str):
			raise TypeError("Expected string, got %r instead" % type(scan_id))

		try:
			m_response = self._manager.make_xml_request('<get_tasks task_id="%s" details="1"/>' % scan_id,
			                                            xml_result=True)
		except ServerError as e:
			raise VulnscanServerError("Can't get the detail for the task %s. Error: %s" % (scan_id, e.message))
		return m_response

	# ----------------------------------------------------------------------
	def get_report_id(self, scan_id):
		m_response = self.get_tasks_detail(scan_id)
		return m_response.find('task').find('last_report')[0].get("id")

	# ----------------------------------------------------------------------
	def get_report_pdf(self, report_id):
		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		try:
			m_response = self._manager.make_xml_request(
				'<get_reports report_id="%s" format_id="c402cc3e-b531-11e1-9163-406186ea4fc5"/>' % report_id,
				xml_result=True)
		except ServerError as e:
			raise VulnscanServerError("Can't get the pdf for the report %s. Error: %s" % (report_id, e.message))
		return m_response

	# ----------------------------------------------------------------------
	def get_report_html(self, report_id):
		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		try:
			m_response = self._manager.make_xml_request(
				'<get_reports report_id="%s" format_id="6c248850-1f62-11e1-b082-406186ea4fc5"/>' % report_id,
				xml_result=True)
		except ServerError as e:
			raise VulnscanServerError("Can't get the pdf for the report %s. Error: %s" % (report_id, e.message))
		return m_response

	# ----------------------------------------------------------------------
	def get_report_xml(self, report_id):
		if not isinstance(report_id, str):
			raise TypeError("Expected string, got %r instead" % type(report_id))

		try:
			m_response = self._manager.make_xml_request('<get_reports report_id="%s" />' % report_id, xml_result=True)
		except ServerError as e:
			raise VulnscanServerError("Can't get the xml for the report%s. Error: %s" % (report_id, e.message))

		return m_response

	# ----------------------------------------------------------------------
	def start_task(self, task_id):
		"""
        Start a task.

        :param task_id: ID of task to start.
        :type task_id: str

        :raises: ClientError, ServerError
        """
		if not isinstance(task_id, str):
			raise TypeError("Expected string, got %r instead" % type(task_id))

		m_query = '<start_task task_id="%s"/>' % task_id

        self._manager.make_xml_request(m_query, xml_result=True)
