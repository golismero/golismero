#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTTP requests and responses.
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

__all__ = ["HTTP_Request", "HTTP_Response"]

from . import Capture
from .. import identity, keep_newer
from ...config import Config
from ...text.text_utils import to_utf8
from ...net.web_utils import ParsedURL, generate_user_agent

import re
import httplib


#------------------------------------------------------------------------------
class HTTP_Headers (object):
    """
    HTTP headers.

    Unlike other methods of storing HTTP headers in Python this class preserves
    the original order of the headers, doesn't remove duplicated headers,
    preserves the original case but still letting your access them in a
    case-insensitive manner, and is read-only.

    Also see: parse_headers
    """

    # Also see: https://en.wikipedia.org/wiki/List_of_HTTP_header_fields


    #--------------------------------------------------------------------------
    def __init__(self, raw_headers):
        """
        :param raw_headers: Raw headers to parse.
        :type raw_headers: str
        """
        self.__raw_headers = to_utf8(raw_headers)
        self.__headers, self.__cache = self.parse_headers(raw_headers)


    #--------------------------------------------------------------------------
    @staticmethod
    def from_items(items):
        """
        Get HTTP headers in pre-parsed form.

        This is useful for integrating with other libraries that have
        already parsed the HTTP headers in their own way.

        :param items: Iterable of key/value pairs.
        :type items: iterable( tuple(str, str) )
        """

        # Reconstruct the raw headers the best we can.
        reconstructed = [
            "%s: %s" % (to_utf8(name),
                        (to_utf8(value)
                         if value.endswith("\r\n")
                         else value + "\r\n")
                        )
            for name, value in items
        ]
        reconstructed.append("\r\n")
        raw_headers = "".join(reconstructed)

        # Return an HTTP_Headers object using the reconstructed raw headers.
        return HTTP_Headers(raw_headers)


    #--------------------------------------------------------------------------
    @staticmethod
    def parse_headers(raw_headers):
        """
        Parse HTTP headers.

        Unlike other common Python solutions (mimetools, etc.) this one
        properly supports multiline HTTP headers and duplicated header
        merging as specified in the RFC.

        The parsed headers are returned in two forms.

        The first is an n-tuple of 2-tuples of strings containing each
        header's name and value. The original case and order is preserved,
        as well as any whitespace and line breaks in the values. Duplicate
        headers are not merged or dealt with in any special way. This aims
        at preserving the headers in original form as much as possible
        without resorting to the raw headers themselves, for example for
        fingerprint analysis of the web server.

        The second is a dictionary mapping header names to their values.
        Duplicate headers are merged as per RFC specs, and multiline headers
        are converted to single line headers to avoid line breaks in the
        values. Header names are converted to lowercase for easier case
        insensitive lookups. This aims at making it easier to get the values
        of the headers themselves rather than analyzing the web server.

        :param raw_headers: Raw headers to parse.
        :type raw_headers: str

        :returns: Parsed headers in original and simplified forms.
        :rtype: tuple( tuple(tuple(str, str)), dict(str -> str) )
        """

        # Split the headers into lines and parse each line.
        original = []
        parsed = {}
        last_name = None
        for line in to_utf8(raw_headers).split("\r\n"):

            # If we find an empty line, stop processing.
            if not line:
                break

            # If the line begins with whitespace, it's a continuation.
            if line[0] in " \t":
                if last_name is None:
                    break                              # broken headers
                line = line.strip()
                parsed[last_name] += " " + line
                item = original[-1]
                item = (item[0], item[1] + " " + line)
                original[-1] = item
                continue                               # next line

            # Split the name and value pairs.
            name, value = line.split(":", 1)

            # Strip the leading and trailing whitespace.
            name  = name.strip()
            value = value.strip()

            # Convert the name to lowercase.
            name_lower = name.lower()

            # Remember the last name we've seen.
            last_name = name_lower

            # Add the headers to the parsed form.
            # If the name already exists, merge the headers.
            # If not, add a new one.
            if name_lower in parsed:
                parsed[name_lower] += ", " + value
            else:
                parsed[name_lower] = value

            # Add the headers to the original form.
            original.append( (name, value) )

        # Convert the original headers list into a tuple to make it
        # read-only, then return the tuple and the dictionary.
        return tuple(original), parsed


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.__raw_headers


    #--------------------------------------------------------------------------
    def __repr__(self):
        return "<%s headers=%r>" % (self.__class__.__name__, self.__headers)


    #--------------------------------------------------------------------------
    def to_tuple(self):
        """
        Convert the headers to Python tuples of strings.

        :returns: Headers.
        :rtype: tuple( tuple(str, str) )
        """

        # Immutable object, we can return it directly.
        return self.__headers


    #--------------------------------------------------------------------------
    def to_dict(self):
        """
        Convert the headers to a Python dictionary.

        :returns: Headers.
        :rtype: dict(str -> str)
        """

        # Mutable object, we need to make a new one.
        return dict(self.to_tuple())


    #--------------------------------------------------------------------------
    def __iter__(self):
        """
        When iterated, whole header lines are returned.
        To iterate header names and values use iterkeys(), itervalues()
        or iteritems().

        :returns: Iterator of header lines.
        :rtype: iter(str)
        """
        return ("%s: %s\r\n" % item for item in self.__headers)


    #--------------------------------------------------------------------------
    def iteritems(self):
        """
        When iterating, the original case and order of the headers
        is preserved. This means some headers may be repeated.

        :returns: Iterator of header names and values.
        :rtype: iter( tuple(str, str) )
        """
        return self.__headers.__iter__()


    #--------------------------------------------------------------------------
    def iterkeys(self):
        """
        When iterating, the original case and order of the headers
        is preserved. This means some headers may be repeated.

        :returns: Iterator of header names.
        :rtype: iter(str)
        """
        return (name for name, _ in self.__headers)


    #--------------------------------------------------------------------------
    def itervalues(self):
        """
        When iterating, the original case and order of the headers
        is preserved. This means some headers may be repeated.

        :returns: Iterator of header values.
        :rtype: iter(str)
        """
        return (value for _, value in self.__headers)


    #--------------------------------------------------------------------------
    def __getitem__(self, key):
        """
        The [] operator works both for index lookups and key lookups.

        When provided with an index, the whole header line is returned.

        When provided with a header name, the value is looked up.
        Only the first header of that name is returned. Comparisons
        are case-insensitive.

        :param key: Index or header name.
        :type key: int | str

        :returns: Header line (for indices) or value (for names).
        :rtype: str
        """
        if type(key) in (int, long):
            return "%s: %s\r\n" % self.__headers[key]
        try:
            key = key.lower()
        except AttributeError:
            raise TypeError("Expected str, got %s" % type(key))
        return self.__cache[key]


    #--------------------------------------------------------------------------
    def get(self, name, default = None):
        """
        Get a header by name.

        Comparisons are case-insensitive. When more than one header has
        the requested name, only the first one is returned.

        :param name: Header name.
        :type name: str

        :returns: Header value.
        :rtype: str
        """
        try:
            name = to_utf8(name)
            if ":" in name:
                name = name.split(":", 1)[0]
            name = name.strip().lower()
        except AttributeError:
            raise TypeError("Expected str, got %s" % type(name))
        try:
            return self.__cache[name]
        except KeyError:
            return default


    #--------------------------------------------------------------------------
    def __getslice__(self, start = None, end = None):
        """
        When sliced, whole header lines are returned in a single string.

        :param start: Start of the slice.
        :type start: int | None

        :param end: End of the slice.
        :type end: int | None

        :returns: The requested header lines merged into a single string.
        :rtype: str
        """
        return "".join(
            "%s: %s\r\n" % item
            for item in self.__headers[start:end]
        )


    #--------------------------------------------------------------------------
    def has_key(self, name):
        """
        Test the presence of a header.
        Comparisons are case-insensitive.

        :param name: Header name.
        :type name: str

        :returns: True if present, False otherwise.
        :rtype: bool
        """
        try:
            name = to_utf8(name)
            if ":" in name:
                name = name.split(":", 1)[0]
            name = name.strip().lower()
        except AttributeError:
            raise TypeError("Expected str, got %s" % type(name))
        return name in self.__cache

    # Alias.
    __contains__ = has_key


    #--------------------------------------------------------------------------
    def items(self):
        """
        The original case and order of the headers is preserved.
        This means some headers may be repeated.

        :returns: Header names and values.
        :rtype: list( tuple(str, str) )
        """
        return list(self.iteritems())


    #--------------------------------------------------------------------------
    def keys(self):
        """
        The original case and order of the headers is preserved.
        This means some headers may be repeated.

        :returns: Header names.
        :rtype: list(str)
        """
        return list(self.iterkeys())


    #--------------------------------------------------------------------------
    def values(self):
        """
        The original case and order of the headers is preserved.
        This means some headers may be repeated.

        :returns: Header values.
        :rtype: list(str)
        """
        return list(self.itervalues())


#------------------------------------------------------------------------------
class HTTP_Request (Capture):
    """
    HTTP request information.
    """

    data_subtype = "http_request"


    #
    # TODO:
    #   + Allow multipart file uploads.
    #   + Parse and reconstruct requests as it's done with responses.
    #     It may be useful one day, for example, for HTTP proxying.
    #


    # Default user agent string.
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible, GoLismero/2.0 The Web Knife; +https://github.com/golismero/golismero)"

    # Default headers to use in HTTP requests.
    DEFAULT_HEADERS = (
        ("Accept-Language", "en-US"),
        ("Accept", "*/*"),
        ("Cache-Control", "no-store"),
        ("Pragma", "no-cache"),
        ("Expires", "0"),
    )


    #--------------------------------------------------------------------------
    def __init__(self, url, headers = None, post_data = None, method = None, protocol = "HTTP", version = "1.1", referer = None, user_agent = None):
        """
        :param url: Absolute URL to connect to.
        :type url: str

        :param headers: HTTP headers, in raw or parsed form.
            Defaults to DEFAULT_HEADERS.
        :type headers: HTTP_Headers | dict(str -> str) | tuple( tuple(str, str) ) | str | None

        :param post_data: Optional POST data.
            If used, the Content-Type and Content-Length headers are populated automatically,
            unless already present in "headers".
        :type post_data: str | None

        :param method: HTTP method.
            Defaults to POST if post_data is used, or to GET if no post_data is used.
        :type method: str

        :param protocol: Protocol name.
        :type protocol: str

        :param version: Protocol version.
        :type version: str

        :param referer: Optional referer. Ignored if already present in "headers".
        :type referer: str

        :param user_agent: Optional user-agent string. Ignored if already present in "headers".
            Defaults to DEFAULT_USER_AGENT.
        :type user_agent: str | None
        """

        # Default method.
        if not method:
            method = "POST" if post_data else "GET"

        # HTTP method, protocol and version.
        self.__method   = to_utf8(method.upper())      # Not sure about upper() here...
        self.__protocol = to_utf8(protocol.upper())    # Not sure about upper() here...
        self.__version  = to_utf8(version)

        # POST data.
        self.__post_data = post_data

        # URL.
        self.__parsed_url = ParsedURL(url)
        self.__url = self.__parsed_url.url

        # Cookie header value.
        try:
            cookie = Config.audit_config.cookie
        except Exception:
            cookie = None

        # User-Agent header value.
        if user_agent:
            if user_agent.lower() == "random":
                user_agent = generate_user_agent()
            else:
                user_agent = to_utf8(user_agent)
        else:
            user_agent = self.DEFAULT_USER_AGENT

        # Referer header value.
        if referer:
            referer = to_utf8(referer)
        else:
            referer = None

        # HTTP headers.
        if headers is None:
            headers = self.DEFAULT_HEADERS
            if version == "1.1":
                headers = (("Host", self.__parsed_url.host),) + headers
            if post_data:
                headers = headers + (("Content-Type", "application/x-www-form-urlencoded"),
                                     ("Content-Length", str(len(post_data))))
            if cookie:
                headers = headers + (("Cookie", cookie),)
            if referer:
                headers = headers + (("Referer", referer),)
            if user_agent:
                headers = headers + (("User-Agent", user_agent),)
            headers = HTTP_Headers.from_items(headers)
        elif not isinstance(headers, HTTP_Headers):
            headers = to_utf8(headers)
            if type(headers) == str:             # raw headers
                headers = HTTP_Headers(headers)
            elif hasattr(headers, "items"):      # dictionary
                headers = HTTP_Headers.from_items(sorted(headers.items()))
            else:                                # dictionary items
                headers = HTTP_Headers.from_items(sorted(headers))
            if cookie or referer or user_agent:
                headers = headers.to_tuple()
                if cookie and not any(x[0].lower() == "cookie" for x in headers):
                    headers = headers + (("Cookie", cookie),)
                if referer and not any(x[0].lower() == "referer" for x in headers):
                    headers = headers + (("Referer", referer),)
                if user_agent and not any(x[0].lower() == "user-agent" for x in headers):
                    headers = headers + (("User-Agent", user_agent),)
                headers = HTTP_Headers.from_items(headers)
        self.__headers = headers

        # Call the parent constructor.
        super(HTTP_Request, self).__init__()


    ##--------------------------------------------------------------------------
    #@staticmethod
    #def from_form(form, data):
        #"""
        #Get the HTTP request needed to send form data.

        #:param form: HTML form.
        #:type form: Form

        #:param data: Mapping of key/value pairs.
        #:type data: dict(str -> str)

        #:returns: HTTP request ready to send the form data.
        #:rtype: HTTP_Request
        #"""
        #if set(form.parameters) != set(data.keys()):
            #raise ValueError("Form data doesn't match form parameters")
        #return HTTP_Request(url       = form.url,
                            #method    = form.method,
                            #post_data = data)


    #--------------------------------------------------------------------------
    def is_in_scope(self, scope = None):
        if scope is None:
            scope = Config.audit_scope
        return self.url in scope


    #--------------------------------------------------------------------------

    @identity
    def method(self):
        """
        :returns: HTTP method.
        :rtype: str
        """
        return self.__method

    @identity
    def url(self):
        """
        :returns: URL.
        :rtype: str
        """
        return self.__url

    @identity
    def protocol(self):
        """
        :returns: Protocol name.
        :rtype: str
        """
        return self.__protocol

    @identity
    def version(self):
        """
        :returns: Protocol version.
        :rtype: str
        """
        return self.__version

    @identity
    def headers(self):
        """
        :return: HTTP headers.
        :rtype: HTTP_Headers
        """
        return self.__headers

    @identity
    def post_data(self):
        """
        :return: POST data.
        :rtype: str | None
        """
        return self.__post_data


    #--------------------------------------------------------------------------

    @property
    def parsed_url(self):
        """
        :returns: URL split to its components.
        :rtype: ParsedURL
        """
        return self.__parsed_url

    @property
    def request_uri(self):
        """
        :return: Request URI.
        :rtype: str
        """
        return self.__parsed_url.request_uri

    @property
    def hostname(self):
        """
        :return: 'Host' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Host')

    @property
    def user_agent(self):
        """
        :return: 'User-Agent' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('User-Agent')

    @user_agent.setter
    def user_agent(self, user_agent):
        """
        Set 'User-Agent' HTTP header.

        :param user_agent: String with the user agent
        :type user_agent: str
        """
        self.__headers['User-Agent'] = user_agent


    @property
    def accept_language(self):
        """
        :return: 'Accept-Language' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Accept-Language')

    @property
    def accept(self):
        """
        :return: 'Accept' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Accept')

    @property
    def referer(self):
        """
        :return: 'Referer' HTTP header.
        :rtype: str
        """
        return self.__headers.get('Referer')

    @property
    def cookie(self):
        """
        :return: 'Cookie' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Cookie')

    @property
    def content_type(self):
        """
        :return: 'Content-Type' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Content-Type')

    @property
    def content_length(self):
        """
        :return: 'Content-Length' HTTP header.
        :rtype: int | None
        """
        try:
            return int(self.__headers.get('Content-Length'))
        except Exception:
            pass


#------------------------------------------------------------------------------
class HTTP_Raw_Request (Capture):
    """
    Raw HTTP request information.
    """

    data_subtype = "http_raw_request"


    #--------------------------------------------------------------------------
    def __init__(self, raw_request):
        """
        :param raw_request: Raw HTTP request.
        :type raw_request: str
        """
        self.__raw_request = to_utf8(raw_request)
        super(HTTP_Raw_Request, self).__init__()


    #--------------------------------------------------------------------------
    @identity
    def raw_request(self):
        """
        :returns: Raw HTTP request.
        :rtype: str
        """
        return self.__raw_request


#------------------------------------------------------------------------------
class HTTP_Response (Capture):
    """
    HTTP response information.

    Typically plugins don't directly instance these objects,
    but receive them from the HTTP API.
    """

    data_subtype = "http_response"
    min_informations = 1


    #--------------------------------------------------------------------------
    def __init__(self, request, **kwargs):
        """
        All optional arguments must be passed as keywords.

        :param request: HTTP request that originated this response.
        :type request: HTTP_Request | HTTP_Raw_Request

        :param raw_response: (Optional) Raw bytes received from the server.
        :type raw_response: str

        :param status: (Optional) HTTP status code. Defaults to "200".
        :type status: str

        :param reason: (Optional) HTTP reason message.
        :type reason: str

        :param protocol: (Optional) Protocol name. Defaults to "HTTP".
        :type protocol: str

        :param version: (Optional) Protocol version. Defaults to "1.1".
        :type version: str

        :param raw_headers: (Optional) Raw HTTP headers.
        :type raw_headers: str

        :param headers: (Optional) Parsed HTTP headers.
        :type headers: HTTP_Headers | dict(str -> str) | tuple( tuple(str, str) )

        :param data: (Optional) Raw data that followed the response headers.
        :type data: str

        :param elapsed: (Optional) Time elapsed in milliseconds since the request
                        was sent until the response was received.
        :type elapsed: int
        """

        # Initialize everything.
        self.__raw_response = None
        self.__raw_headers  = None
        self.__status       = None
        self.__reason       = None
        self.__protocol     = getattr(request, "protocol", "HTTP")
        self.__version      = getattr(request, "version",  "1.1")
        self.__headers      = None
        self.__data         = None
        self.__elapsed      = None

        # Raw response bytes.
        self.__raw_response = kwargs.get("raw_response", None)
        if self.__raw_response:
            self.__parse_raw_response(request)

        # Status line.
        self.__status   = to_utf8( kwargs.get("status",   self.__status)   )
        self.__reason   = to_utf8( kwargs.get("reason",   self.__reason)   )
        self.__protocol = to_utf8( kwargs.get("protocol", self.__protocol) )
        self.__version  = to_utf8( kwargs.get("version",  self.__version)  )
        if self.__status and not self.__reason:
            try:
                self.__reason = httplib.responses[self.__status]
            except Exception:
                pass
        elif not self.__status and self.__reason:
            lower_reason = self.__reason.strip().lower()
            for code, text in httplib.responses.iteritems():
                if text.lower() == lower_reason:
                    self.__status = str(code)
                    break
        elif not self.__status:
            self.__status = "200"
            self.__reason = "OK"

        # HTTP headers.
        self.__raw_headers = to_utf8( kwargs.get("raw_headers", self.__raw_headers) )
        self.__headers = kwargs.get("headers", self.__headers)
        if self.__headers:
            if not isinstance(self.__headers, HTTP_Headers):
                if hasattr(self.__headers, "items"):
                    self.__headers = HTTP_Headers.from_items(sorted(self.__headers.items()))
                else:
                    self.__headers = HTTP_Headers.from_items(sorted(self.__headers))
            if not self.__raw_headers:
                self.__reconstruct_raw_headers()
        elif self.__raw_headers and not self.__headers:
            self.__parse_raw_headers()

        # Data.
        self.__data = to_utf8( kwargs.get("data", self.__data) )

        # Reconstruct the raw response if needed.
        if not self.__raw_response:
            self.__reconstruct_raw_response()

        # Response time.
        self.elapsed = kwargs.get("elapsed", None)

        # Call the parent constructor.
        super(HTTP_Response, self).__init__()

        # Link this response to the request that originated it.
        self.add_link(request)


    #--------------------------------------------------------------------------
    def is_cacheable(self):
        """
        Determines if this response should be cached by default.

        :returns: True if cacheable, False otherwise.
        :rtype: bool
        """

        # TODO: use the headers, Luke!

        return True


    #--------------------------------------------------------------------------

    @keep_newer  # TODO: maybe the times should be collected and/or averaged instead?
    def elapsed(self):
        """
        :returns: Time elapsed in seconds since the request was sent
                  until the response was received. None if not available.
        :rtype: float | None
        """
        return self.__elapsed

    @elapsed.setter
    def elapsed(self, elapsed):
        """
        :param elapsed: Time elapsed in seconds since the request was
            sent until the response was received. None if not available.
        :type elapsed: float | None
        """
        self.__elapsed = float(elapsed) if elapsed is not None else None


    #--------------------------------------------------------------------------

    @identity
    def raw_response(self):
        """
        :returns: Raw HTTP response.
        :rtype: str | None
        """
        return self.__raw_response


    #--------------------------------------------------------------------------

    @property
    def status(self):
        """
        :returns: HTTP status code.
        :rtype: str | None
        """
        return self.__status

    @property
    def reason(self):
        """
        :returns: HTTP reason message.
        :rtype: str | None
        """
        return self.__reason

    @property
    def protocol(self):
        """
        :returns: Protocol name.
        :rtype: str | None
        """
        return self.__protocol

    @property
    def version(self):
        """
        :returns: Protocol version.
        :rtype: str | None
        """
        return self.__version

    @property
    def headers(self):
        """
        :return: HTTP headers.
        :rtype: dict(str -> str) | None
        """
        return self.__headers

    @property
    def raw_headers(self):
        """
        :returns: HTTP method used for this request.
        :rtype: str | None
        """
        return self.__raw_headers

    @property
    def data(self):
        """
        :return: Response data.
        :rtype: str | None
        """
        return self.__data

    @property
    def content_length(self):
        """
        :return: 'Content-Length' HTTP header.
        :rtype: int | None
        """
        try:
            return int(self.__headers.get('Content-Length'))
        except Exception:
            pass

    @property
    def content_type(self):
        """
        :return: 'Content-Type' HTTP header.
        :rtype: str | None
        """
        return self.__headers.get('Content-Type')

    @property
    def content_disposition(self):
        """
        :return: 'Content-Disposition' HTTP header.
        :rtype: str | None
        """
        if self.__headers:
            return self.__headers.get('Content-Disposition')

    @property
    def transport_encoding(self):
        """
        :return: 'Transport-Encoding' HTTP header.
        :rtype: str | None
        """
        if self.__headers:
            return self.__headers.get('Transport-Encoding')

    @property
    def cookie(self):
        """
        :return: 'Set-Cookie' HTTP header.
        :rtype: str | None
        """
        if self.__headers:
            return self.__headers.get('Set-Cookie')

    set_cookie = cookie

    @property
    def server(self):
        """
        :return: 'Server' HTTP header.
        :rtype: str | None
        """
        if self.__headers:
            return self.__headers.get('Server')


    #--------------------------------------------------------------------------
    def __parse_raw_response(self, request):

        # Special case: if parsing HTTP/0.9, everything is data.
        if getattr(request, "version", None) == "0.9":
            self.__protocol = "HTTP"
            self.__version  = "0.9"
            self.__status   = "200"
            self.__reason   = httplib.responses[200]
            self.__data     = self.__raw_response
            return

        # Split the response from the data.
        response, data = self.__raw_response.split("\r\n\r\n", 1)
        response = response + "\r\n\r\n"

        # Split the response line from the headers.
        raw_line, raw_headers = response.split("\r\n", 1)

        # Split the response line into its components.
        try:
            proto_version, status, reason = re.split("[ \t]+", raw_line, 2)
        except Exception:
            proto_version, status = re.split("[ \t]+", raw_line, 1)
            try:
                reason = httplib.responses[int(status)]
            except Exception:
                reason = None
        if "/" in proto_version:
            protocol, version = proto_version.split("/")
        else:
            protocol = proto_version
            version  = None

        # Set missing components to None.
        if not status:
            status = None
        if not reason:
            reason = None
        if not protocol:
            protocol = None
        if not data:
            data = None

        # Store the components.
        self.__protocol    = protocol
        self.__version     = version
        self.__status      = status
        self.__reason      = reason
        self.__raw_headers = raw_headers
        self.__data        = data

        # Parse the raw headers.
        self.__parse_raw_headers()


    #--------------------------------------------------------------------------
    def __reconstruct_raw_response(self):

        # Special case: if parsing HTTP/0.9, everything is data.
        if self.__version == "0.9":
            self.__raw_response = self.__data
            return

        # FIXME: not sure how Requests handles content encoding,
        # it may be possible to generate broken raw responses if
        # the content is decoded automatically behind our backs

        # Reconstruct the response line.
        if self.__protocol and self.__version:
            proto_ver = "%s/%s " % (self.__protocol, self.__version)
        elif self.__protocol:
            proto_ver = self.__protocol + " "
        elif self.__version:
            proto_ver = self.__version + " "
        else:
            proto_ver = ""
        if self.__status and self.__reason:
            status_line = "%s%s %s\r\n" % (proto_ver, self.__status, self.__reason)
        elif self.__status:
            status_line = "%s%s\r\n" % (proto_ver, self.__status)
        elif self.__reason:
            status_line = "%s%s\r\n" % (proto_ver, self.__reason)

        # Reconstruct the headers.
        raw_headers = self.__raw_headers
        if not raw_headers:
            if self.__headers:
                self.__reconstruct_raw_headers()
                raw_headers = self.__raw_headers
            else:
                raw_headers = ""

        # Get the data if available.
        if self.__data:
            data = self.__data
        else:
            data = ""

        # Store the reconstructed raw response.
        self.__raw_response = "%s%s%s" % (status_line, raw_headers, data)


    #--------------------------------------------------------------------------
    def __parse_raw_headers(self):
        self.__headers = HTTP_Headers(self.__raw_headers)


    #--------------------------------------------------------------------------
    def __reconstruct_raw_headers(self):
        self.__raw_headers = str(self.__headers)
