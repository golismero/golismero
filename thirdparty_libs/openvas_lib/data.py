#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

"""OpenVas Data Structures."""

import re
import sys

from collections import OrderedDict

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

if sys.version_info >= (3,):
	_range = range
else:
	_range = xrange


# ------------------------------------------------------------------------------
class _Common(object):
	risk_levels = ("Critical", "High", "Medium", "Low", "None", "None", "Log", "Debug")


# ------------------------------------------------------------------------------
class OpenVASPort(object):
	"""
    Port definition.
    """

	# ----------------------------------------------------------------------
	def __init__(self, port_name, number, proto):
		"""
        :param port_name: service name asociated (/etc/services). i.e: http
        :type port_name: str

        :param number: port number
        :type number: int

        :param proto: network protocol: tcp, udp, icmp..
        :type proto: str
        """
		if not isinstance(port_name, str):
			raise TypeError("Expected string, got %r instead" % type(port_name))

		if number:
			if isinstance(number, int):
				if not (0 < number < 65535):
					raise ValueError("port must be between ranges: [0-65535], got %s instead" % number)
			else:
				raise TypeError("Expected int, got %r instead" % type(number))

		if not isinstance(proto, str):
			raise TypeError("Expected string, got %r instead" % type(proto))

		self.__port_name = port_name.strip()
		self.__number = number
		self.__proto = proto.strip()

	# ----------------------------------------------------------------------
	@property
	def proto(self):
		"""
        :return: network protocol: tcp, udp, icmp...
        :rtype: str
        """
		return self.__proto

	# ----------------------------------------------------------------------
	@property
	def number(self):
		"""
        :return: port number. None if not available.
        :rtype: float
        """
		return self.__number

	# ----------------------------------------------------------------------
	@property
	def port_name(self):
		"""
        :return: service name asociated (/etc/services). i.e: http
        :rtype: str
        """
		return self.__port_name

	# ----------------------------------------------------------------------
	def __str__(self):
		return "%s (%s/%s)" % (self.port_name, self.number, self.proto)


# ----------------------------------------------------------------------
class OpenVASNVT(_Common):
	"""
    OpenVas NVT structure.
    """

	# ----------------------------------------------------------------------
	def __init__(self):
		self.__oid = None
		self.__name = ""
		self.__cvss_base = 0.0
		self.__cvss_base_vector = None
		self.__risk_factor = "None"
		self.__category = "Unknown"
		self.__summary = ""
		self.__description = ""
		self.__family = "Unknown"

		self.__cves = []
		self.__bids = []
		self.__bugtraqs = []
		self.__xrefs = []
		self.__fingerprints = ""
		self.__tags = []

		super(OpenVASNVT, self).__init__()

	# ----------------------------------------------------------------------
	@property
	def oid(self):
		"""
        :return:
        :rtype: str
        """
		return self.__oid

	# ----------------------------------------------------------------------
	@oid.setter
	def oid(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__oid = val

	# ----------------------------------------------------------------------
	@property
	def name(self):
		"""
        :return: the name of NVT
        :rtype: str
        """
		return self.__name

	# ----------------------------------------------------------------------
	@name.setter
	def name(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__name = val

	# ----------------------------------------------------------------------
	@property
	def cvss_base_vector(self):
		"""
        :return: CVSS Base calculated
        :rtype: float
        """
		return self.__cvss_base_vector

	# ----------------------------------------------------------------------
	@cvss_base_vector.setter
	def cvss_base_vector(self, val):
		"""
        :param val: CVSS Base calculated
        :type val: float
        """
		if not isinstance(val, str):
			raise TypeError("Expected str, got %r instead" % type(val))

		self.__cvss_base_vector = val

	# ----------------------------------------------------------------------
	@property
	def cvss_base(self):
		"""
        :return: CVSS Base calculated
        :rtype: float
        """
		return self.__cvss_base

	# ----------------------------------------------------------------------
	@cvss_base.setter
	def cvss_base(self, val):
		"""
        :param val: CVSS Base calculated
        :type val: float
        """
		m = None
		if isinstance(val, (str, int, float)):
			try:
				m = float(val)

				if not (0.0 <= m <= 10.0):
					raise ValueError("CVSS value must be between 0.0 - 10.0, got %s instead" % m)

			except ValueError:
				if val is None or val == '':
					m = 0.0
				else:
					raise TypeError("Expected number, got %r instead" % type(val))
		else:
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__cvss_base = m

	# ----------------------------------------------------------------------
	@property
	def risk_factor(self):
		"""
        :return: the risk factor
        :rtype: int
        """
		return self.__risk_factor

	# ----------------------------------------------------------------------
	@risk_factor.setter
	def risk_factor(self, val):
		"""
        :param val: the risk factor
        :type val: int
        """
		if not isinstance(val, str):
			raise TypeError("Expected int, got %r instead" % type(val))
		if val not in self.risk_levels:
			raise ValueError(
				"Value incorrect. Allowed values are: Critical|High|Medium|Low|None|Log|Debug, got %s instead" % val)

		self.__risk_factor = val

	# ----------------------------------------------------------------------
	@property
	def summary(self):
		"""
        :return: The summary
        :rtype: str
        """
		return self.__summary

	# ----------------------------------------------------------------------
	@summary.setter
	def summary(self, val):
		"""
        :param val: The summary
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__summary = val

	# ----------------------------------------------------------------------
	@property
	def description(self):
		"""
        :return: The raw_description of NVT
        :rtype: str
        """
		return self.__description

	# ----------------------------------------------------------------------
	@description.setter
	def description(self, val):
		"""
        :param val: The raw_description of NVT
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__description = val

	# ----------------------------------------------------------------------
	@property
	def family(self):
		"""
        :return: The family of NVT
        :rtype: str
        """
		return self.__family

	# ----------------------------------------------------------------------
	@family.setter
	def family(self, val):
		"""
        :param val: The family of NVT
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__family = val

	# ----------------------------------------------------------------------
	@property
	def category(self):
		"""
        :return: The category that the NVT belongs
        :rtype: str
        """
		return self.__category

	# ----------------------------------------------------------------------
	@category.setter
	def category(self, val):
		"""
        :param val: The category that the NVT belongs
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected  str, got %r instead" % type(val))

		self.__category = val

	# ----------------------------------------------------------------------
	@property
	def cve(self):
		"""
        :return: the CVE associated
        :rtype: str
        """
		return self.__cves

	# ----------------------------------------------------------------------
	@cve.setter
	def cve(self, val):
		"""
        :param val: the CVE associated
        :type val: str
        """
		self.__set_list_value(self.__cves, val)

	# ----------------------------------------------------------------------
	@property
	def bid(self):
		"""
        :return: The BID number associated
        :rtype: str
        """
		return self.__bids

	# ----------------------------------------------------------------------
	@bid.setter
	def bid(self, val):
		"""
        :param val: The BID number associated
        :type val: str
        """
		self.__set_list_value(self.__bids, val)

	# ----------------------------------------------------------------------
	@property
	def bugtraq(self):
		"""
        :return: The Bugtraq ID associated
        :rtype: str
        """
		return self.__bugtraqs

	# ----------------------------------------------------------------------
	@bugtraq.setter
	def bugtraq(self, val):
		"""
        :param val: The Bugtraq ID associated
        :type val: str
        """
		self.__set_list_value(self.__bugtraqs, val)

	# ----------------------------------------------------------------------
	@property
	def xrefs(self):
		"""
        :return: The xrefs associated
        :rtype: str
        """
		return self.__xrefs

	# ----------------------------------------------------------------------
	@xrefs.setter
	def xrefs(self, val):
		"""
        :param val: The xrefs associated
        :type val: str
        """
		self.__set_list_value(self.__xrefs, val)

	# ----------------------------------------------------------------------
	@property
	def fingerprints(self):
		"""
        :return: The fingerprints associated
        :rtype: str
        """
		return self.__fingerprints

	# ----------------------------------------------------------------------
	@fingerprints.setter
	def fingerprints(self, val):
		"""
        :param val: The fingerprints associated
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__fingerprints = val

	# ----------------------------------------------------------------------
	@property
	def tags(self):
		"""
        :return: The tags associated
        :rtype: str
        """
		return self.__tags

	# ----------------------------------------------------------------------
	@tags.setter
	def tags(self, val):
		"""
        :param val: The tags associated
        :type val: str
        """
		self.__set_list_value(self.__tags, val)

	# ----------------------------------------------------------------------
	def __set_list_value(self, prop, val):
		"""
        Checks if value is a string of a list and add the new value to it.

        :param prop: object property
        :type prop: property

        :param val: value
        :type val: str|list

        """
		if isinstance(val, str):
			if val != "":
				prop.append(val)
		elif isinstance(val, list):
			if val:
				prop.extend([x.strip() for x in val])
		else:
			raise TypeError("Expected string, got %r instead" % type(val))


# ------------------------------------------------------------------------------
class OpenVASOverride(_Common):
	"""
    Override object of OpenVas results.
    """

	# ----------------------------------------------------------------------
	def __init__(self):
		self.__nvt_oid = None
		self.__nvt_name = ""
		self.__text = ""
		self.__text_is_excerpt = False
		self.__threat = "None"
		self.__new_threat = "None"
		self.__orphan = False

		super(OpenVASOverride, self).__init__()

	# ----------------------------------------------------------------------
	@property
	def oid(self):
		"""
        :return:
        :rtype: str
        """
		return self.__nvt_oid

	# ----------------------------------------------------------------------
	@oid.setter
	def oid(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__nvt_oid = val

	# ----------------------------------------------------------------------
	@property
	def name(self):
		"""
        :return: The name of the NVT
        :rtype: str
        """
		return self.__nvt_name

	# ----------------------------------------------------------------------
	@name.setter
	def name(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__nvt_name = val

	# ----------------------------------------------------------------------
	@property
	def text(self):
		"""
        :return:
        :rtype: str
        """
		return self.__text

	# ----------------------------------------------------------------------
	@text.setter
	def text(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__text = val

	# ----------------------------------------------------------------------
	@property
	def text_is_excerpt(self):
		"""
        :return: The text is an excerpt?
        :rtype: bool
        """
		return self.__text_is_excerpt

	# ----------------------------------------------------------------------
	@text_is_excerpt.setter
	def text_is_excerpt(self, val):
		"""
        :type val: bool
        """
		if not isinstance(val, bool):
			raise TypeError("Expected  bool, got %r instead" % type(val))

		self.__text_is_excerpt = val

	# ----------------------------------------------------------------------
	@property
	def threat(self):
		"""
        :return: one of these values: Critical|High|Medium|Low|None|Log|Debug
        :rtype: str
        """
		return self.__threat

	# ----------------------------------------------------------------------
	@threat.setter
	def threat(self, val):
		"""
        :type val: str - (Critical|High|Medium|Low|None|Log|Debug)
        """
		if not isinstance(val, str):
			raise TypeError("Expected  str - (), got %r instead" % type(val))
		if val not in self.risk_levels:
			raise ValueError(
				"Value incorrect. Allowed values are: Critical|High|Medium|Low|None|Log|Debug, got %s instead" % val)

		self.__threat = val

	# ----------------------------------------------------------------------
	@property
	def new_threat(self):
		"""
        :return: one of these values: Critical|High|Medium|Low|None|Log|Debug
        :rtype: str
        """
		return self.__new_threat

	# ----------------------------------------------------------------------
	@new_threat.setter
	def new_threat(self, val):
		"""
        :type val: str - (Critical|High|Medium|Low|None|Log|Debug)
        """
		if not isinstance(val, str):
			raise TypeError("Expected  str - (), got %r instead" % type(val))
		if val not in self.risk_levels:
			raise ValueError(
				"Value incorrect. Allowed values are: Critical|High|Medium|Low|None|Log|Debug, got %s instead" % val)

		self.__new_threat = val

	# ----------------------------------------------------------------------
	@property
	def orphan(self):
		"""
        :return:  indicates if the NVT is orphan
        :rtype: bool
        """
		return self.__orphan

	# ----------------------------------------------------------------------
	@orphan.setter
	def orphan(self, val):
		"""
        :type val: bool
        """
		if not isinstance(val, bool):
			raise TypeError("Expected bool, got %r instead" % type(val))

		self.__orphan = val


# ------------------------------------------------------------------------------
class OpenVASNotes(object):
	"""
    Store the notes for a results object.
    """

	# ----------------------------------------------------------------------
	def __init__(self, oid, name, text, text_is_excerpt, orphan):

		if not isinstance(oid, str):
			raise TypeError("Expected string, got %r instead" % type(oid))
		if not isinstance(name, str):
			raise TypeError("Expected string, got %r instead" % type(name))
		if not isinstance(text, str):
			raise TypeError("Expected string, got %r instead" % type(text))
		if not isinstance(text_is_excerpt, bool):
			raise TypeError("Expected bool, got %r instead" % type(text_is_excerpt))
		if not isinstance(orphan, bool):
			raise TypeError("Expected bool, got %r instead" % type(orphan))

		self.__nvt_oid = oid
		self.__nvt_name = name
		self.__text = text
		self.__text_is_excerpt = text_is_excerpt
		self.__orphan = orphan

	# ----------------------------------------------------------------------
	@property
	def oid(self):
		"""
        :return:
        :rtype: str
        """
		return self.__nvt_oid

	# ----------------------------------------------------------------------
	@property
	def name(self):
		"""
        :return: The name of the note
        :rtype: str
        """
		return self.__nvt_name

	# ----------------------------------------------------------------------
	@property
	def text(self):
		"""
        :return: text related with the note
        :rtype: str
        """
		return self.__text

	# ----------------------------------------------------------------------
	@property
	def text_is_excerpt(self):
		"""
        :return: indicates if the text is an excerpt
        :rtype: bool
        """
		return self.__text_is_excerpt

	# ----------------------------------------------------------------------
	@property
	def orphan(self):
		"""
        :return: indicates if the note is orphan
        :rtype: bool
        """
		return self.__orphan


# ------------------------------------------------------------------------------
class OpenVASResult(_Common):
	"""
    Main structure to store audit results.
    """

	# ----------------------------------------------------------------------
	def __init__(self):
		self.__id = None
		self.__subnet = None
		self.__host = None
		self.__port = None
		self.__nvt = None
		self.__threat = None
		self.__description = None
		self.__notes = None
		self.__overrides = None

		# auto generated
		self.__impact = ""
		self.__summary = ""
		self.__vulnerability_insight = ""
		self.__affected_software = ""
		self.__solution = ""

		super(OpenVASResult, self).__init__()

	# --------------------------------------------------------------------------
	# Auto generated read only
	# --------------------------------------------------------------------------
	@property
	def impact(self):
		return self.__impact

	@property
	def summary(self):
		return self.__summary

	@property
	def vulnerability_insight(self):
		return self.__vulnerability_insight

	@property
	def affected_software(self):
		return self.__affected_software

	@property
	def solution(self):
		return self.__solution

	# ----------------------------------------------------------------------
	@property
	def id(self):
		"""
        :return: the id
        :rtype: str
        """
		return self.__id

	# ----------------------------------------------------------------------
	@id.setter
	def id(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__id = val

	# ----------------------------------------------------------------------
	@property
	def host(self):
		"""
        :return: the target
        :rtype: str
        """
		return self.__host

	# ----------------------------------------------------------------------
	@host.setter
	def host(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__host = val

	# ----------------------------------------------------------------------
	@property
	def port(self):
		"""
        :rtype: OpenVASPort
        """
		return self.__port

	# ----------------------------------------------------------------------
	@port.setter
	def port(self, val):
		"""
        :type val: OpenVASPort
        """
		if not isinstance(val, OpenVASPort):
			raise TypeError("Expected int, got %r instead" % type(val))

		self.__port = val

	# ----------------------------------------------------------------------
	@property
	def subnet(self):
		"""
        :return: the network
        :rtype: str
        """
		return self.__subnet

	# ----------------------------------------------------------------------
	@subnet.setter
	def subnet(self, val):
		"""
        :type val: str
        """
		if not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		self.__subnet = val

	# ----------------------------------------------------------------------
	@property
	def nvt(self):
		"""
        :return:
        :rtype: OpenVASNVT
        """
		return self.__nvt

	# ----------------------------------------------------------------------
	@nvt.setter
	def nvt(self, val):
		"""
        :type val: OpenVASNVT
        """
		if not isinstance(val, OpenVASNVT):
			raise TypeError("Expected OpenVASNVT, got %r instead" % type(val))

		self.__nvt = val

	# ----------------------------------------------------------------------
	@property
	def threat(self):
		"""
        :return: "Critical", "High", "Medium", "Low", "None", "Log", "Debug"
        :rtype: str
        """
		return self.__threat

	# ----------------------------------------------------------------------
	@threat.setter
	def threat(self, val):
		"""
        :param val: valid values: "Critical", "High", "Medium", "Low", "None", "Log", "Debug"
        :type val: str
        """
		if isinstance(val, str):
			if val not in self.risk_levels:
				raise ValueError(
					"Value incorrect. Allowed values are: Critical|High|Medium|Low|None|Log|Debug, got %s instead" % val)
		else:
			raise TypeError("Expected string , got %r instead" % type(val))

		self.__threat = val

	# ----------------------------------------------------------------------
	@property
	def raw_description(self):
		"""
        :rtype: str
        """
		return self.__description

	# ----------------------------------------------------------------------
	@raw_description.setter
	def raw_description(self, val):
		"""
        :type val: str
        """
		if val is None:
			val = ""
		elif not isinstance(val, str):
			raise TypeError("Expected string, got %r instead" % type(val))

		# --------------------------------------------------------------------------
		# Get "Solution", "Impact", "Summary" and "Affected Software", "Vulnerability Insight"
		# --------------------------------------------------------------------------
		stops_words = (
			"[iI]mpact[\s]*:",
			"[sS]ummary[\s]*:",
			"[aA]ffected[\w\W\s]*[sS]oftware[\s\w\W]*:",
			"[sS]olution[\s]*:",
			"[vV]ulnerability[\w\s\W]*[iI]nsight[\s]*:",
		)

		var_maps = dict(mpact="impact",
		                ummary="summary",
		                ffected="affected_software",
		                olution="solution",
		                ulnerability="vulnerability_insight")

		# Get start positions
		positions = OrderedDict()
		for word in stops_words:
			p = re.search(word, val)

			if p:
				positions[p.span()[0]] = word

		keys = sorted(positions.keys())

		for x in _range(len(positions)):
			start = "(%s)" % positions[keys[x]]
			end = "%s" % "(%s)" % positions[keys[x + 1]] if x < len(keys) - 1 else ""

			# Get first range of text
			regex = "%s([\w\W\n\s\r]+)%s" % (start, end)

			range_text = re.search(regex, val)

			if range_text:
				# Looking for text and their var correspondence
				var_name = None
				for y, v in var_maps.items():
					if y in positions[keys[x]]:
						var_name = v
						break

				# Filter text
				text = range_text.group(2)

				# Replace special chars by space
				text = re.sub("[\r\n\t]", " ", text)

				# Replace 2 or more spaces by only one
				text = re.sub("\s\s+", " ", text)

				# Remove start and end spaces
				text = text.strip()

				setattr(self, "_OpenVASResult__%s" % var_name, text)

		self.__description = val

	# ----------------------------------------------------------------------
	@property
	def notes(self):
		"""
        :rtype: list(OpenVASNotes)
        """
		return self.__notes

	# ----------------------------------------------------------------------
	@notes.setter
	def notes(self, val):
		"""
        :type val: list(OpenVASNotes)
        """
		val = list(val)
		for v in val:
			if not isinstance(v, OpenVASNotes):
				raise TypeError("Expected OpenVASNotes, got %r instead" % type(v))

		self.__notes = val

	# ----------------------------------------------------------------------
	@property
	def overrides(self):
		"""
        :return:
        :rtype:
        """
		return self.__overrides

	# ----------------------------------------------------------------------
	@overrides.setter
	def overrides(self, val):
		"""
        :type val: OpenVASOverride
        """
		if not isinstance(val, OpenVASOverride):
			raise TypeError("Expected OpenVASOverride, got %r instead" % type(val))

		self.__overrides = val


__all__ = [x for x in dir() if x.startswith("OpenVAS")]
