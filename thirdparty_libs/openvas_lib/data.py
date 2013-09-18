#!/usr/bin/python
# -*- coding: utf-8 -*-

"OpenVas Data Structures."

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


#------------------------------------------------------------------------------
class OpenVASPort(object):
    """
    Port definition.
    """


    #----------------------------------------------------------------------
    def __init__(self, port_name, number, proto):
        """
        :param port_name: service name asociated (/etc/services). i.e: http
        :type port_name: str

        :param number: port number
        :type number: int

        :param proto: network protocol: tcp, udp, icmp..
        :type proto: str
        """
        if not isinstance(port_name, basestring):
            raise TypeError("Expected string, got %r instead" % type(port_name))

        if isinstance(number, int):
            if not (0 < number < 65535):
                raise ValueError("port must be between ranges: [0-65535]")
        else:
            raise TypeError("Expected int, got %r instead" % type(number))

        if not isinstance(proto, basestring):
            raise TypeError("Expected string, got %r instead" % type(proto))

        self.__port_name             = port_name
        self.__number                = number
        self.__proto                 = proto

    #----------------------------------------------------------------------
    @property
    def proto(self):
        """
        :return: network protocol: tcp, udp, icmp...
        :rtype: str
        """
        return self.__proto

    #----------------------------------------------------------------------
    @property
    def number(self):
        """
        :return: port number
        :rtype: int
        """
        return self.__number

    #----------------------------------------------------------------------
    @property
    def port_name(self):
        """
        :return: service name asociated (/etc/services). i.e: http
        :rtype: str
        """
        return self.__port_name


#----------------------------------------------------------------------
class OpenVASNVT(object):
    """
    OpenVas NVT structure.
    """


    #----------------------------------------------------------------------
    def __init__(self):
        self.__oid             = None
        self.__name            = None
        self.__cvss_base       = None
        self.__risk_factor     = None
        self.__category        = None
        self.__summary         = None
        self.__description     = None
        self.__family          = None

        self.__cve             = None
        self.__bid             = None
        self.__bugtraq         = None
        self.__xrefs           = None
        self.__fingerprints    = None
        self.__tags            = None


    #----------------------------------------------------------------------
    @classmethod
    def make_object(cls, oid, name, cvss_base, risk_factor,
                    summary, description, family=None, category=None,
                    cve=None, bid=None, bugtraq=None, xrefs=None, fingerprints=None, tags=None):
        """
        :type oid: str
        :type name: str
        :type cvss_base: int
        :type risk_factor: int
        :type summary: str
        :type description: str
        :type family: str
        :type category: str
        :type cve: str
        :type bid: str
        :type bugtraq: str
        :type xrefs: str
        :type fingerprints: str
        :type tags: str
        """

        if not isinstance(oid, basestring):
            raise TypeError("Expected string, got %r instead" % type(oid))
        if not isinstance(name, basestring):
            raise TypeError("Expected string, got %r instead" % type(name))
        if not isinstance(cvss_base, int):
            raise TypeError("Expected int, got %r instead" % type(cvss_base))
        if not isinstance(risk_factor, int):
            raise TypeError("Expected int, got %r instead" % type(risk_factor))
        if not isinstance(summary, basestring):
            raise TypeError("Expected string, got %r instead" % type(summary))
        if not isinstance(description, basestring):
            raise TypeError("Expected string, got %r instead" % type(description))

        if family:
            if not isinstance(family, basestring):
                raise TypeError("Expected string, got %r instead" % type(family))
        if category:
            if not isinstance(category, basestring):
                raise TypeError("Expected string, got %r instead" % type(category))

        if cve:
            if not isinstance(cve, basestring):
                raise TypeError("Expected string, got %r instead" % type(cve))

        if bid:
            if not isinstance(bid, basestring):
                raise TypeError("Expected string, got %r instead" % type(bid))

        if bugtraq:
            if not isinstance(bugtraq, basestring):
                raise TypeError("Expected string, got %r instead" % type(bugtraq))

        if xrefs:
            if not isinstance(xrefs, basestring):
                raise TypeError("Expected string, got %r instead" % type(xrefs))

        if fingerprints:
            if not isinstance(fingerprints, basestring):
                raise TypeError("Expected string, got %r instead" % type(fingerprints))

        if tags:
            if not isinstance(tags, basestring):
                raise TypeError("Expected string, got %r instead" % type(tags))

        cls                   = OpenVASNVT()
        cls.__oid             = oid
        cls.__name            = name
        cls.__cvss_base       = cvss_base
        cls.__risk_factor     = risk_factor
        cls.__category        = category
        cls.__summary         = summary
        cls.__description     = description
        cls.__family          = family

        cls.__cve             = cve
        cls.__bid             = bid
        cls.__bugtraq         = bugtraq
        cls.__xrefs           = xrefs
        cls.__fingerprints    = fingerprints
        cls.__tags            = tags

        return cls


    #----------------------------------------------------------------------
    @classmethod
    def make_empty_object(cls):
        """
        :return: make and empty object
        :rtype: OpenVASNVT
        """
        return OpenVASNVT()


    #----------------------------------------------------------------------
    @property
    def oid(self):
        """
        :return:
        :rtype: str
        """
        return self.__oid


    #----------------------------------------------------------------------
    @oid.setter
    def oid(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__oid = val


    #----------------------------------------------------------------------
    @property
    def name(self):
        """
        :return: the name of NVT
        :rtype: basestring
        """
        return self.__name


    #----------------------------------------------------------------------
    @name.setter
    def name(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__name = val


    #----------------------------------------------------------------------
    @property
    def cvss_base(self):
        """
        :return: CVSS Base calculated
        :rtype: int
        """
        return self.__cvss_base


    #----------------------------------------------------------------------
    @cvss_base.setter
    def cvss_base(self, val):
        """
        :param val: CVSS Base calculated
        :type val: int
        """
        if not isinstance(val, int):
            raise TypeError("Expected int, got %r instead" % type(val))

        self.__cvss_base = val


    #----------------------------------------------------------------------
    @property
    def risk_factor(self):
        """
        :return: the risk factor
        :rtype: int
        """
        return self.__risk_factor


    #----------------------------------------------------------------------
    @risk_factor.setter
    def risk_factor(self, val):
        """
        :param val: the risk factor
        :type val: int
        """
        if not isinstance(val, int):
            raise TypeError("Expected int, got %r instead" % type(val))

        self.__risk_factor = val


    #----------------------------------------------------------------------
    @property
    def summary(self):
        """
        :return: The summary
        :rtype: basestring
        """
        return self.__summary


    #----------------------------------------------------------------------
    @summary.setter
    def summary(self, val):
        """
        :param val: The summary
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__summary = val


    #----------------------------------------------------------------------
    @property
    def description(self):
        """
        :return: The description of NVT
        :rtype: basestring
        """
        return self.__description


    #----------------------------------------------------------------------
    @description.setter
    def description(self, val):
        """
        :param val: The description of NVT
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__description = val


    #----------------------------------------------------------------------
    @property
    def family(self):
        """
        :return: The family of NVT
        :rtype: basestring
        """
        return self.__family


    #----------------------------------------------------------------------
    @family.setter
    def family(self, val):
        """
        :param val: The family of NVT
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__family = val


    #----------------------------------------------------------------------
    @property
    def category(self):
        """
        :return: The category that the NVT belongs
        :rtype: basestring
        """
        return self.__category


    #----------------------------------------------------------------------
    @category.setter
    def category(self, val):
        """
        :param val: The category that the NVT belongs
        :type val: basestring
        """
        if not isinstance(val,  basestring):
            raise TypeError("Expected  basestring, got %r instead" % type(val))

        self.__category = val


    #----------------------------------------------------------------------
    @property
    def cve(self):
        """
        :return: the CVE associated
        :rtype: basestring
        """
        return self.__cve


    #----------------------------------------------------------------------
    @cve.setter
    def cve(self, val):
        """
        :param val: the CVE associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__cve = val


    #----------------------------------------------------------------------
    @property
    def bid(self):
        """
        :return: The BID number associated
        :rtype: basestring
        """
        return self.__bid


    #----------------------------------------------------------------------
    @bid.setter
    def bid(self, val):
        """
        :param val: The BID number associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__bid = val


    #----------------------------------------------------------------------
    @property
    def bugtraq(self):
        """
        :return: The Bugtraq ID associated
        :rtype: basestring
        """
        return self.__bugtraq


    #----------------------------------------------------------------------
    @bugtraq.setter
    def bugtraq(self, val):
        """
        :param val: The Bugtraq ID associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__bugtraq = val


    #----------------------------------------------------------------------
    @property
    def xrefs(self):
        """
        :return: The xrefs associated
        :rtype: basestring
        """
        return self.__xrefs


    #----------------------------------------------------------------------
    @xrefs.setter
    def xrefs(self, val):
        """
        :param val: The xrefs associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__xrefs = val


    #----------------------------------------------------------------------
    @property
    def fingerprints(self):
        """
        :return: The fingerprints associated
        :rtype: basestring
        """
        return self.__fingerprints


    #----------------------------------------------------------------------
    @fingerprints.setter
    def fingerprints(self, val):
        """
        :param val: The fingerprints associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__fingerprints = val


    #----------------------------------------------------------------------
    @property
    def tags(self):
        """
        :return: The tags associated
        :rtype: basestring
        """
        return self.__tags


    #----------------------------------------------------------------------
    @tags.setter
    def tags(self, val):
        """
        :param val: The tags associated
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__tags = val


#------------------------------------------------------------------------------
class OpenVASOverride(object):
    """
    Override object of OpenVas results.
    """


    #----------------------------------------------------------------------
    @classmethod
    def make_object(cls, oid, name, text, text_is_excerpt, threat, new_threat, orphan):

        if not isinstance(oid, basestring):
            raise TypeError("Expected string, got %r instead" % type(oid))
        if not isinstance(name, basestring):
            raise TypeError("Expected string, got %r instead" % type(name))
        if not isinstance(text, basestring):
            raise TypeError("Expected string, got %r instead" % type(text))
        if not isinstance(text_is_excerpt, bool):
            raise TypeError("Expected bool, got %r instead" % type(text_is_excerpt))
        if not isinstance(threat, basestring):
            raise TypeError("Expected string, got %r instead" % type(threat))
        if not isinstance(new_threat, basestring):
            raise TypeError("Expected string, got %r instead" % type(new_threat))
        if not isinstance(orphan, bool):
            raise TypeError("Expected bool, got %r instead" % type(orphan))

        cls                   = OpenVASOverride()
        cls.__nvt_oid         = oid
        cls.__nvt_name        = name
        cls.__text            = text
        cls.__text_is_excerpt = text_is_excerpt
        cls.__threat          = threat
        cls.__new_threat      = new_threat
        cls.__orphan          = orphan

        return cls


    #----------------------------------------------------------------------
    @classmethod
    def make_empty_object(cls):

        cls                   = OpenVASOverride()
        cls.__nvt_oid         = None
        cls.__nvt_name        = None
        cls.__text            = None
        cls.__text_is_excerpt = None
        cls.__threat          = None
        cls.__new_threat      = None
        cls.__orphan          = None

        return cls


    #----------------------------------------------------------------------
    @property
    def oid(self):
        """
        :return:
        :rtype: str
        """
        return self.__nvt_oid


    #----------------------------------------------------------------------
    @oid.setter
    def oid(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__nvt_oid = val


    #----------------------------------------------------------------------
    @property
    def name(self):
        """
        :return: The name of the NVT
        :rtype: str
        """
        return self.__name


    #----------------------------------------------------------------------
    @name.setter
    def name(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__name = val


    #----------------------------------------------------------------------
    @property
    def text(self):
        """
        :return:
        :rtype: str
        """
        return self.__text


    #----------------------------------------------------------------------
    @text.setter
    def text(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__text = val


    #----------------------------------------------------------------------
    @property
    def text_is_excerpt(self):
        """
        :return: The text is an excerpt?
        :rtype: bool
        """
        return self.__text_is_excerpt


    #----------------------------------------------------------------------
    @text_is_excerpt.setter
    def text_is_excerpt(self, val):
        """
        :type val: bool
        """
        if not isinstance(val,  bool):
            raise TypeError("Expected  bool, got %r instead" % type(val))

        self.__text_is_excerpt = val


    #----------------------------------------------------------------------
    @property
    def threat(self):
        """
        :return: one of these values: High|Medium|Low|Log|Debug
        :rtype: str
        """
        return self.__threat


    #----------------------------------------------------------------------
    @threat.setter
    def threat(self, val):
        """
        :type val: str - (High|Medium|Low|Log|Debug)
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected  str - (), got %r instead" % type(val))

        self.__threat = val


    #----------------------------------------------------------------------
    @property
    def new_threat(self):
        """
        :return: one of these values: High|Medium|Low|Log|Debug
        :rtype: str
        """
        return self.__new_threat


    #----------------------------------------------------------------------
    @new_threat.setter
    def new_threat(self, val):
        """
        :type val: str - (High|Medium|Low|Log|Debug)
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected  str - (), got %r instead" % type(val))

        self.__new_threat = val


    #----------------------------------------------------------------------
    @property
    def orphan(self):
        """
        :return:  indicates if the NVT is orphan
        :rtype: bool
        """
        return self.__orphan


    #----------------------------------------------------------------------
    @orphan.setter
    def orphan(self, val):
        """
        :type val: bool
        """
        if not isinstance(val, bool):
            raise TypeError("Expected bool, got %r instead" % type(val))

        self.__orphan = val


#------------------------------------------------------------------------------
class OpenVASNotes(object):
    """
    Store the notes for a results object.
    """


    #----------------------------------------------------------------------
    def __init__(self, oid, name, text, text_is_excerpt, orphan):

        if not isinstance(oid, basestring):
            raise TypeError("Expected string, got %r instead" % type(oid))
        if not isinstance(name, basestring):
            raise TypeError("Expected string, got %r instead" % type(name))
        if not isinstance(text, basestring):
            raise TypeError("Expected string, got %r instead" % type(text))
        if not isinstance(text_is_excerpt, bool):
            raise TypeError("Expected bool, got %r instead" % type(text_is_excerpt))
        if not isinstance(orphan, bool):
            raise TypeError("Expected bool, got %r instead" % type(orphan))

        self.__nvt_oid             = oid
        self.__nvt_name            = name
        self.__text                = text
        self.__text_is_excerpt     = text_is_excerpt
        self.__orphan              = orphan


    #----------------------------------------------------------------------
    @property
    def oid(self):
        """
        :return:
        :rtype: basestring
        """
        return self.__nvt_oid


    #----------------------------------------------------------------------
    @property
    def name(self):
        """
        :return: The name of the note
        :rtype: basestring
        """
        return self.__nvt_name


    #----------------------------------------------------------------------
    @property
    def text(self):
        """
        :return: text related with the note
        :rtype: basestring
        """
        return self.__text


    #----------------------------------------------------------------------
    @property
    def text_is_excerpt(self):
        """
        :return: indicates if the text is an excerpt
        :rtype: bool
        """
        return self.__text_is_excerpt


    #----------------------------------------------------------------------
    @property
    def orphan(self):
        """
        :return: indicates if the note is orphan
        :rtype: bool
        """
        return self.__orphan


#------------------------------------------------------------------------------
class OpenVASResult(object):
    """
    Main structure to store audit results.
    """


    #----------------------------------------------------------------------
    @classmethod
    def make_object(cls, id, subnet, host, port, nvt, threat, description=None, notes=None, overrides=None):

        if not isinstance(subnet, basestring):
            raise TypeError("Expected string, got %r instead" % type(subnet))
        if not isinstance(host, basestring):
            raise TypeError("Expected string, got %r instead" % type(host))
        if not isinstance(port, basestring):
            raise TypeError("Expected string, got %r instead" % type(port))
        if not isinstance(nvt, OpenVASNVT):
            raise TypeError("Expected OpenVASNVT, got %r instead" % type(nvt))
        if isinstance(threat, basestring):
            if threat not in ("High", "Medium", "Low", "Log", "Debug"):
                raise ValueError("Value incorrect. Allowed values are: High|Medium|Low|Log|Debug")
        else:
            raise TypeError("Expected OpenVASThreat, got %r instead" % type(threat))

        if not isinstance(description, basestring):
            raise TypeError("Expected string, got %r instead" % type(description))
        if not isinstance(notes, OpenVASNotes):
            raise TypeError("Expected OpenVASNotes, got %r instead" % type(notes))
        if not isinstance(overrides, OpenVASOverride):
            raise TypeError("Expected OpenVASOverride, got %r instead" % type(overrides))


        cls                  = OpenVASResult()
        cls.__id             = id
        cls.__subnet         = subnet
        cls.__host           = host
        cls.__port           = port
        cls.__nvt            = nvt
        cls.__threat         = threat
        cls.__description    = description
        cls.__notes          = notes
        cls.__overrides      = overrides

        return cls


    #----------------------------------------------------------------------
    @classmethod
    def make_empty_object(cls):
        """
        :return: Creates a empty object
        :rtype: OpenVASResult
        """
        cls                  = OpenVASResult()
        cls.__id             = None
        cls.__subnet         = None
        cls.__host           = None
        cls.__port           = None
        cls.__nvt            = None
        cls.__threat         = None
        cls.__description    = None
        cls.__notes          = None
        cls.__overrides      = None

        return cls


    #----------------------------------------------------------------------
    @property
    def id(self):
        """
        :return: the id
        :rtype: str
        """
        return self.__id


    #----------------------------------------------------------------------
    @id.setter
    def id(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__id = val


    #----------------------------------------------------------------------
    @property
    def host(self):
        """
        :return: the target
        :rtype: str
        """
        return self.__host


    #----------------------------------------------------------------------
    @host.setter
    def host(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__host = val


    #----------------------------------------------------------------------
    @property
    def port(self):
        """
        :rtype: OpenVASPort
        """
        return self.__port


    #----------------------------------------------------------------------
    @port.setter
    def port(self, val):
        """
        :type val: OpenVASPort
        """
        if not isinstance(val, OpenVASPort):
            raise TypeError("Expected int, got %r instead" % type(val))

        self.__port = val


    #----------------------------------------------------------------------
    @property
    def subnet(self):
        """
        :return: the network
        :rtype: basestring
        """
        return self.__subnet


    #----------------------------------------------------------------------
    @subnet.setter
    def subnet(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__subnet = val


    #----------------------------------------------------------------------
    @property
    def nvt(self):
        """
        :return:
        :rtype: OpenVASNVT
        """
        return self.__nvt


    #----------------------------------------------------------------------
    @nvt.setter
    def nvt(self, val):
        """
        :type val: OpenVASNVT
        """
        if not isinstance(val, OpenVASNVT):
            raise TypeError("Expected OpenVASNVT, got %r instead" % type(val))

        self.__nvt = val


    #----------------------------------------------------------------------
    @property
    def threat(self):
        """
        :return: "High", "Medium", "Low", "Log", "Debug"
        :rtype: str
        """
        return self.__threat


    #----------------------------------------------------------------------
    @threat.setter
    def threat(self, val):
        """
        :param val: valid values: "High", "Medium", "Low", "Log", "Debug"
        :type val: basestring
        """
        if isinstance(val, basestring ):
            if val not in ("High", "Medium", "Low", "Log", "Debug"):
                raise ValueError("Value incorrect. Allowed values are: High|Medium|Low|Log|Debug")
        else:
            raise TypeError("Expected string , got %r instead" % type(val))

        self.__threat = val


    #----------------------------------------------------------------------
    @property
    def description(self):
        """
        :rtype: str
        """
        return self.__description


    #----------------------------------------------------------------------
    @description.setter
    def description(self, val):
        """
        :type val: basestring
        """
        if not isinstance(val, basestring):
            raise TypeError("Expected string, got %r instead" % type(val))

        self.__description = val


    #----------------------------------------------------------------------
    @property
    def notes(self):
        """
        :rtype: list(OpenVASNotes)
        """
        return self.__notes


    #----------------------------------------------------------------------
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


    #----------------------------------------------------------------------
    @property
    def overrides(self):
        """
        :return:
        :rtype:
        """
        return self.__overrides


    #----------------------------------------------------------------------
    @overrides.setter
    def overrides(self, val):
        """
        :type val: OpenVASOverride
        """
        if not isinstance(val, OpenVASOverride):
            raise TypeError("Expected OpenVASOverride, got %r instead" % type(val))

        self.__overrides = val
