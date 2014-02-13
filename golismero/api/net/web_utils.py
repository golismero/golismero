#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web utilities API.
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
    "download", "data_from_http_response", "generate_user_agent",
    "fix_url", "check_auth", "get_auth_obj", "detect_auth_method",
    "split_hostname", "generate_error_page_url", "get_error_page",
    "ParsedURL", "parse_url", "urlparse", "urldefrag", "urljoin",
    "json_decode", "json_encode",
]


from . import NetworkOutOfScope
from ..data import LocalDataCache, discard_data
from ..text.text_utils import generate_random_string, split_first, to_utf8
from ...common import json_decode, json_encode

from BeautifulSoup import BeautifulSoup
from copy import deepcopy
from posixpath import join, splitext, split
from random import randint
from requests import Request, Session, codes
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests_ntlm import HttpNtlmAuth
from tldextract import TLDExtract
from urllib import quote, quote_plus, unquote, unquote_plus
from urlparse import urljoin as original_urljoin
from warnings import warn

import re


#------------------------------------------------------------------------------
# Url class from urllib3 renamed as Urllib3_Url to avoid confusion.

try:
    from requests.packages.urllib3.util import Url as Urllib3_Url
except ImportError:
    from urllib3.util import Url as Urllib3_Url


#------------------------------------------------------------------------------
__user_agents = (
    "Opera/9.80 (Windows NT 6.1; U; zh-tw) Presto/2.5.22 Version/10.50",
    "Mozilla/6.0 (Macintosh; U; PPC Mac OS X Mach-O; en-US; rv:2.0.0.0) Gecko/20061028 Firefox/3.0",
    "Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1",
    "Mozilla/5.0 (Windows NT 5.1; rv:15.0) Gecko/20100101 Firefox/13.0.1",
    "Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:15.0) Gecko/20120724 Debian Iceweasel/15.0",
    "Mozilla/5.0 (X11; Linux) KHTML/4.9.1 (like Gecko) Konqueror/4.9",
    "Lynx/2.8.8dev.3 libwww-FM/2.14 SSL-MM/1.4.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.60 Safari/537.17",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.6 Safari/537.11",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.2; SV1; .NET CLR 3.3.69573; WOW64; en-US)",
    "Mozilla/4.0(compatible; MSIE 7.0b; Windows NT 6.0)",
    "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (BlackBerry; U; BlackBerry 9900; en) AppleWebKit/534.11+ (KHTML, like Gecko) Version/7.1.0.346 Mobile Safari/534.11+",
    "Mozilla/5.0 (PLAYSTATION 3; 3.55)",
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)"
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/534.16+ (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4",
    "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25"
)

# This var contains names of vars uses by most commont web servers. This will be used by
# all of injection tools, that can skip these vars.
WEB_SERVERS_VARS = ["__utma",
                    "__utmb",
                    "__utmc",
                    "__utmz",
                    "JSESSIONID",
                    "PHPSESSID",
                    "ASPSESSIONID"]

def generate_user_agent():
    """
    :returns: A valid user agent string, randomly chosen from a predefined list.
    :rtype: str
    """
    return __user_agents[randint(0, len(__user_agents) - 1)]


#------------------------------------------------------------------------------
def data_from_http_response(response):
    """
    Extracts data from an HTTP response.

    :param response: HTTP response.
    :type response: HTTP_Response

    :returns: Extracted data, or None if no data was found.
    :rtype: Data | None
    """

    # If we have no data, return None.
    if not response.data:
        return None

    # Get the MIME content type.
    content_type = response.content_type

    # Strip the content type modifiers.
    if ";" in content_type:
        content_type = content_type[:content_type.find(";")]

    # Sanitize the content type.
    content_type = content_type.strip().lower()
    if "/" not in content_type:
        return None

    # Parse the data.
    data = None
    try:

        # HTML pages.
        if content_type == "text/html":
            from ..data.information.html import HTML
            data = HTML(response.data)

        # Plain text data.
        elif content_type.startswith("text/"):
            from ..data.information.text import Text
            data = Text(response.data, response.content_type)

        # Image files.
        elif content_type.startswith("image/"):
            from ..data.information.image import Image
            data = Image(response.data, response.content_type)

    # Catch errors and throw warnings instead.
    except Exception, e:
        ##raise # XXX DEBUG
        warn(str(e), RuntimeWarning)

    # Anything we don't know how to parse we treat as binary.
    if data is None:
        from ..data.information.binary import Binary
        data = Binary(response.data, response.content_type)

    # Associate the data to the response.
    data.add_information(response)

    # Return the data.
    return data


#------------------------------------------------------------------------------
def download(url, callback = None, timeout = 10.0, allow_redirects = True,
             allow_out_of_scope = False):
    """
    Download the file pointed to by the given URL.

    An optional callback function may be given. It will be called just
    before downloading the file, and receives the file size. If it
    returns True the download proceeds, if it returns False it's
    cancelled.

    Example:

        >>> from golismero.api.data.resource.url import Url
        >>> from golismero.api.net.web_utils import download
        >>> def decide(url, name, size, type):
        ...     # 'url' is the URL for the download
        ...     if url is not None:
        ...         print "URL: %s" % url
        ...     # 'name' is the suggested filename (None if not available)
        ...     if name is not None:
        ...         print "Name: %s" % name
        ...     # 'size' is the file size (None if not available)
        ...     if size is not None:
        ...         print "Size: %d" % size
        ...     # 'type' is the MIME type (None if not available)
        ...     if type is not None:
        ...         print "Type: %s" % type
        ...     # Cancel download if not a web page
        ...     if type != "text/html":
        ...         return False
        ...     # Cancel download if it's too large
        ...     if size > 1000000:
        ...         return False
        ...     # Continue downloading
        ...     return True
        ...
        >>> download(Url("http://www.example.com/index.html"), callback=decide)
        URL: http://www.example.com/index.html
        Name: index.html
        Size: 1234
        Type: text/html
        <HTML identity=606489619590839a1c0ad662bcdc0189>
        >>> download(Url("http://www.example.com/"), callback=decide)
        URL: http://www.example.com/
        Size: 1234
        Type: text/html
        <HTML identity=606489619590839a1c0ad662bcdc0189>
        >>> print download(Url("http://www.example.com/big_file.iso"), callback=decide)
        URL: http://www.example.com/big_file.iso
        Name: big_file.iso
        Size: 1234567890
        Type: application/octet-stream
        None

    :param url: URL to download.
    :type url: Url

    :param callback: Callback function.
    :type callback: callable

    :param timeout: Timeout in seconds.
            The minimum value is 0.5 and the maximum is 100.0. Any other values
            will be silently converted to either one of them.
    :type timeout: int | float

    :param allow_redirects: True to follow redirections, False otherwise.
    :type allow_redirects: bool

    :param allow_out_of_scope: True to allow download of URLs out of scope,
                               False otherwise.
    :type allow_out_of_scope: bool

    :returns: Downloaded data as an object of the GoLismero data model,
              or None if cancelled.
    :rtype: File | None

    :raises NetworkOutOfScope: The resource is out of the audit scope.
    :raises NetworkException: A network error occurred during download.
    :raises NotImplementedError: The network protocol is not supported.
    """

    # Validate the callback type.
    if callback is not None and not callable(callback):
        raise TypeError(
            "Expected callable (function, class, instance with __call__),"
            " got %r instead" % type(callback)
        )

    # Autogenerate an Url object if a string is given (common mistake).
    from ..data.resource.url import Url
    if not isinstance(url, Url):
        url = Url(url)
        LocalDataCache.on_autogeneration(url)
        parsed = url.parsed_url
        if not parsed.hostname or not parsed.scheme:
            raise ValueError("Only absolute URLs must be used!")

    # Validate the protocol.
    # TODO: add support for FTP
    scheme = url.parsed_url.scheme
    if scheme not in ("http", "https"):
        raise NotImplementedError("Protocol not supported: %s" % scheme)

    # Validate the scope.
    if not url.is_in_scope() and allow_out_of_scope is False:
        raise NetworkOutOfScope("URL out of scope: %s" % url.url)

    # Autogenerate the HTTP request object.
    from ..config import Config
    from ..data.information.http import HTTP_Request
    request = HTTP_Request( url         = url.url,
                            method      = url.method,
                            post_data   = url.post_params,
                            referer     = url.referer,
                            user_agent  = Config.audit_config.user_agent)
    LocalDataCache.on_autogeneration(request)

    # Prepare the callback.
    if callback is None:
        temp_callback = None
    else:
        def temp_callback(
                    request, url, status_code, content_length, content_type):

            # Abort if not successful.
            if status_code != "200":
                return False

            # Get the name.
            # TODO: parse the Content-Disposition header.
            name = ParsedURL(url).filename
            if not name:
                name = request.parsed_url.filename
                if not name:
                    name = None

            # Call the user-defined callback.
            return callback(url, name, content_length, content_type)

    # Send the request and get the response.
    from .http import HTTP
    response = HTTP.make_request(request,
                                 callback = temp_callback,
                                 timeout = timeout,
                                 allow_redirects = allow_redirects,
                                 allow_out_of_scope = allow_out_of_scope)

    # If not aborted...
    if response:

        # The response object is autogenerated.
        LocalDataCache.on_autogeneration(response)

        # Associate the URL to the request and the response.
        request.add_resource(url)
        response.add_resource(url)

        # Extract the data from the response.
        data = data_from_http_response(response)

        # Associate the data to the URL.
        data.add_resource(url)

        # Return the data.
        return data


#------------------------------------------------------------------------------
def fix_url(url, base_url=None):
    """
    Parse a URL input from a user and convert it to a canonical URL.

    Relative URLs are converted to absolute URLs if the base URL is given.

    .. warning:
       This function may be removed in future versions of GoLismero.

    Example:

    >>> from golismero.api.net.web_utils import fix_url
    >>> fix_url("www.site.com")
    http://www.site.com
    >>> fix_url(url="/contact", base_url="www.site.com")
    http://www.site.com/contact

    :param url: URL
    :type url: str

    :param base_url: (Optional) Base URL.
    :type base_url: str

    :return: Canonical URL.
    :rtype: str
    """

    url      = to_utf8(url)
    base_url = to_utf8(base_url)

    parsed = ParsedURL(url)
    if not parsed.scheme:
        parsed.scheme = 'http://'

    if base_url:
        # Remove the fragment from the base URL.
        base_url = urldefrag(base_url)[0]
        # Canonicalize the URL.
        return urljoin(base_url, parsed.url.strip())
    else:
        return parsed.url


#------------------------------------------------------------------------------
def check_auth(url, user, password):
    """
    Check the auth for and specified url.

    .. warning:
       This function may be removed in future versions of GoLismero.

    :param url: String with url.
    :type url: str

    :param user: string with user text
    :type user: str

    :param password: string with password text
    :type password: str

    :return: True if authentication is successful, False otherwise.
    :rtype: bool
    """

    # Check trivial case.
    if not url:
        return False

    # Sanitize URL string.
    url = to_utf8(url)

    # Get authentication method.
    auth, _ = detect_auth_method(url)

    # Is authentication required?
    if auth:

        # Get authentication object.
        m_auth_obj = get_auth_obj(auth, user, password)

        # Try the request.
        req = Request(url = url, auth = m_auth_obj)
        p = req.prepare()
        s = Session()
        r = s.send(p)

        # Check if authentication was successful.
        return r.status_code == codes.ok

    # No authentication is required.
    return True


#------------------------------------------------------------------------------
def get_auth_obj(method, user, password):
    """
    Generates an authentication code object depending of method as parameter:

    * "basic"
    * "digest"
    * "ntlm"

    .. warning:
       This function may be removed in future versions of GoLismero.

    :param method: Auth method: basic, digest, ntlm.
    :type method: str

    :param user: string with user text
    :type user: str

    :param password: string with password text
    :type password: str

    :return: an object with authentication or None if error/problem.
    """
    m_auth_obj = None

    if method:

        m_method = method.lower()
        if m_method == "basic":
            m_auth_obj = HTTPBasicAuth(user, password)
        elif m_method == "digest":
            m_auth_obj = HTTPDigestAuth(user, password)
        elif m_method == "ntlm":
            m_auth_obj = HttpNtlmAuth(user, password)

    return m_auth_obj


#------------------------------------------------------------------------------
def detect_auth_method(url):
    """
    Detects authentication method/type for an URL.

    .. warning:
       This function may be removed in future versions of GoLismero.

    :param url: url to test authentication.
    :type url: str.

    :return: (scheme, realm) if auth required. None otherwise.
    """

    url = to_utf8(url)
    req = Request(url=url)

    p = req.prepare()
    s = Session()
    r = s.send(p)

    if 'www-authenticate' in r.headers:
        authline = r.headers['www-authenticate']
        authobj  = re.compile(
            r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
            re.IGNORECASE)
        matchobj = authobj.match(authline)

        if matchobj:
            scheme = matchobj.group(1)
            realm  = matchobj.group(2)
            return scheme, realm

    return None, None


#------------------------------------------------------------------------------
def split_hostname(hostname):
    """
    Splits a hostname into its subdomain, domain and TLD parts.

    For example:

    >>> from golismero.api.net.web_utils import ParsedURL
    >>> d = ParsedURL("http://www.example.com/")
    >>> d.split_hostname()
    ('www', 'example', 'com')
    >>> d = ParsedURL("http://some.subdomain.of.example.co.uk/")
    >>> d.split_hostname()
    ('some.subdomain.of', 'example', 'co.uk')
    >>> '.'.join(d.split_hostname())
    'some.subdomain.of.example.co.uk'

    :param hostname: Hostname to split.
    :type hostname: str

    :returns: Subdomain, domain and TLD.
    :rtype: tuple(str, str, str)
    """
    extract = TLDExtract(fetch = False)
    result  = extract( to_utf8(hostname) )
    return result.subdomain, result.domain, result.suffix


#------------------------------------------------------------------------------
def generate_error_page_url(url):
    """
    Takes an URL to an existing document and generates a random URL
    to a nonexisting document, to trigger a server error.

    Example:

    >>> from golismero.api.net.web_utils import generate_error_page_url
    >>> generate_error_page_url("http://www.site.com/index.php")
    'http://www.site.com/index.php.19ds_8vjX'

    :param url: Original URL. It must point to an existing document.
    :type  url: str

    :return: Generated URL.
    :rtype: str
    """
    m_parsed_url = ParsedURL(url)
    m_parsed_url.path = m_parsed_url.path + generate_random_string()
    return m_parsed_url.url


#------------------------------------------------------------------------------
def get_error_page(url):
    """
    Takes an URL to an existing document and generates a random URL
    to a nonexisting document, then uses it to trigger a server error.
    Returns the error page as a File object (typically this would be
    an HTML object, but it may be something else).

    :param url: Original URL. It must point to an existing document.
    :type  url: str

    :returns: Downloaded data as an object of the GoLismero data model,
              or None on error.
    :rtype: File | None

    :raises: ValueError
    """

    # Make the URL.
    m_error_url = generate_error_page_url(url)

    # Get the error page.
    try:
        m_error_response = download(m_error_url)
    except Exception:
        raise ValueError("Can't get error page.")

    # Mark the error page as discarded. Most likely the plugin won't need to
    # send this back as a result.
    discard_data(m_error_response)

    # Return the error page.
    return m_error_response


#------------------------------------------------------------------------------
def parse_url(url, base_url = None):
    """
    Parse an URL and return a mutable object with all its parts.

    For more details see: ParsedURL

    :param url: URL to parse.
    :type url: str

    :param base_url: Optional base URL.
    :type base_url: str

    :returns: Mutable object with access to the URL parts.
    :rtype: ParsedURL
    """
    return ParsedURL(url, base_url)


#------------------------------------------------------------------------------
# Emulate the standard URL parser with our own.

def urlparse(url):
    return parse_url(url)

def urldefrag(url):
    p = parse_url(url)
    f = p.fragment
    p.fragment = ""
    return p.url, f

def urljoin(base_url, url, allow_fragments = True):
    if not allow_fragments:
        url = urldefrag(url)
        base_url = urldefrag(base_url)
    return parse_url(url, base_url).url


#------------------------------------------------------------------------------
class ParsedURL (object):
    """
    Parse an URL and return a mutable object with all its parts.

    For example, the following URL:

    http://user:pass@www.site.com/folder/index.php?param1=val1&b#anchor

    Is broken down to the following properties:

    + url          = 'http://user:pass@www.site.com/folder/index.php?param1=val1&b#anchor'
    + base_url     = 'http://user:pass@www.site.com'
    + request_uri  = '/folder/index.php?b=&param1=val1
    + scheme       = 'http'
    + host         = 'www.site.com'
    + port         = 80
    + username     = 'user'
    + password     = 'pass'
    + auth         = 'user:pass'
    + netloc       = 'user:pass@www.site.com'
    + path         = '/folder/index.php'
    + directory    = '/folder'
    + filename     = 'index.php'
    + filebase     = 'index'
    + extension    = '.php'
    + query        = 'b=&param1=val1'
    + query_params = { 'param1' : 'val1', 'b' : '' }
    + fragment     = 'anchor'

    The url property contains the normalized form of the URL, mostly
    preserving semantics (the query parameters may be sorted, and empty
    URL components are removed).
    For more details see: https://en.wikipedia.org/wiki/URL_normalization

    Changes to the values of these properties will be reflected in all
    other relevant properties. The url and request_uri properties are
    read-only, however.

    **Missing properties are returned as empty strings**, except for the port
    and query_params properties: port is an integer from 1 to 65535 when
    found, or None when it's missing and can't be guessed; query_params is
    a dictionary that may be empty when missing, or None when the query
    string could not be parsed as standard key/value pairs.

    Rebuilding the URL may result in a slightly different, but
    equivalent URL, if the URL that was parsed originally had
    unnecessary delimiters (for example, a ? with an empty query;
    the RFC states that these are equivalent).

    Example:

    >>> from golismero.api.net.web_utils import ParsedURL
    >>> url="http://user:pass@www.site.com/folder/index.php?param1=val1&b#anchor"
    >>> r = ParsedURL(url)
    >>> r.scheme
    'http'
    >>> r.filename
    'index.php'
    >>> r.hostname
    'www.site.com'

    .. warning::
       The url, request_uri, query, netloc and auth properties are URL-encoded.
       All other properties are URL-decoded.

    .. warning::
       Unicode is currently *NOT* supported.
    """


    #--------------------------------------------------------------------------
    # TODO: for the time being we're using the buggy quote and unquote
    # implementations from urllib, but we'll have to roll our own to
    # properly support Unicode (urllib does a mess of it!).
    #--------------------------------------------------------------------------


    #--------------------------------------------------------------------------
    # Dictionary of default port numbers per each supported scheme.
    # The keys of this dictionary are also used to check if a given
    # scheme is supported by this class.

    default_ports = {
        'http'      : 80,        # http://www.example.com/
        'https'     : 443,       # https://secure.example.com/
        'ftp'       : 21,        # ftp://ftp.example.com/file.txt
        'mailto'    : 25,        # mailto://user@example.com?subject=Hi!
        ##'callto'    : None,      # callto:+34666131313
        ##'file'      : None,      # file://C:\Windows\System32\calc.exe
        ##'data'      : None,      # data:data:image/png;base64,iVBORw0KGgoA...
        ##'javascript': None,      # javascript:alert('XSS')
        ##'vbscript'  : None,      # vbscript:alert('XSS')
        ##'magnet'    : None,      # magnet:?xt=urn:sha1:YNCKHTQCWBTRNJIV4WN...
    }

    # See also:
    # https://code.google.com/p/fuzzdb/source/browse/trunk/attack-payloads/http-protocol/known-uri-types.fuzz


    #--------------------------------------------------------------------------
    # List of schemes that require :// instead of just :

    __two_dashes_required = (
        'http', 'https', 'ftp', #'file',
    )


    #--------------------------------------------------------------------------
    # The constructor has code borrowed from the urllib3 project, then
    # adapted and expanded to fit the needs of GoLismero.
    #
    # Urllib3 is copyright 2008-2012 Andrey Petrov and contributors (see
    # CONTRIBUTORS.txt) and is released under the MIT License:
    # http://www.opensource.org/licenses/mit-license.php
    # http://raw.github.com/shazow/urllib3/master/CONTRIBUTORS.txt
    #
    def __init__(self, url, base_url = None):
        """
        :param url: URL to parse.
        :type url: str

        :param base_url: Optional base URL.
        :type base_url: str
        """

        url      = to_utf8(url)
        base_url = to_utf8(base_url)

        if not isinstance(url, str):
            raise TypeError("Expected string, got %r instead" % type(url))
        if base_url is not None and not isinstance(base_url, str):
            raise TypeError("Expected string, got %r instead" % type(base_url))

        original_url = url

        self.__query_char = '?'

        scheme   = ''
        auth     = ''
        host     = ''
        port     = None
        path     = ''
        query    = ''
        fragment = ''

        if base_url:
            url = original_urljoin(base_url, url, allow_fragments=True)

        # Scheme
        if ':' in url:
            if '://' in url:
                scheme, url = url.split('://', 1)
            else:
                scheme, url = url.split(':', 1)
                if scheme in self.__two_dashes_required:
                    raise ValueError("Failed to parse: %s" % original_url)

            # we sanitize it here to prevent errors down below
            scheme = scheme.strip().lower()
            if '%' in scheme or '+' in scheme:
                scheme = unquote_plus(scheme)
            if scheme not in self.default_ports:
                raise ValueError("Failed to parse: %s" % original_url)

        # Find the earliest Authority Terminator
        # (http://tools.ietf.org/html/rfc3986#section-3.2)
        url, path_, delim = split_first(url, ['/', '?', '#'])

        if delim:
            # Reassemble the path
            path = delim + path_

        # Auth
        if '@' in url:
            auth, url = url.split('@', 1)

        # IPv6
        if url and url[0] == '[':
            host, url = url[1:].split(']', 1)
            host = "[%s]" % host  # we need to remember it's IPv6

        # Port
        if ':' in url:
            _host, port = url.split(':', 1)

            if not host:
                host = _host

            if '%' in port:
                port = unquote(port)

            if not port.isdigit():
                raise ValueError("Failed to parse: %s" % original_url)

            port = int(port)

        elif not host and url:
            host = url

        if path:

            # Fragment
            if '#' in path:
                path, fragment = path.split('#', 1)

            # Query
            if '?' in path:
                path, query = path.split('?', 1)
            else:
                # Fix path for values like:
                # http://www.site.com/folder/value_id=0
                p = path.rfind('/') + 1
                if p > 0:
                    _path = path[:p]
                    _query = path[p:]
                else:
                    _path = '/'
                    _query = path
                if '=' in _query:
                    path, query = _path, _query
                    self.__query_char = '/'

        if auth:
            auth = unquote_plus(auth)
        if host:
            host = unquote_plus(host)
        if path:
            path = unquote_plus(path)
        if fragment:
            fragment = unquote_plus(fragment)

        self.__scheme = scheme  # already sanitized
        self.auth = auth
        self.host = host
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.url


    #--------------------------------------------------------------------------
    def copy(self):
        """
        :returns: A copy of this object.
        :rtype: ParsedURL
        """
        return deepcopy(self)


    #--------------------------------------------------------------------------
    def to_urlsplit(self):
        "Convert to a tuple that can be passed to urlparse.urlunstrip()."
        # Do not document the return type!
        return (
            self.__scheme,
            self.netloc,
            self.__path,
            self.query,
            self.__fragment
        )


    #--------------------------------------------------------------------------
    def to_urlparse(self):
        "Convert to a tuple that can be passed to urlparse.urlunparse()."
        # Do not document the return type!
        return (
            self.__scheme,
            self.netloc,
            self.__path,
            None,
            self.query,
            self.__fragment
        )


    #--------------------------------------------------------------------------
    def to_urllib3(self):
        "Convert to a named tuple as returned by urllib3.parse_url()."
        # Do not document the return type!
        return Urllib3_Url(self.__scheme, self.auth, self.__host, self.port,
                           self.__path, self.query, self.__fragment)


    #--------------------------------------------------------------------------
    def match_extension(self, extension,
                        directory_allowed = True,
                        double_allowed    = True,
                        case_insensitive  = True):
        """
        Tries to match the given extension against the URL path.

        By default every component of the path is tested:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/download.php/filename/file.pdf")
        >>> d.match_extension(".php")
        True
        >>> d.match_extension(".pdf")
        True
        >>> d.match_extension(".exe")
        False

        However you can set the 'directory_allowed' to False to check only the last component:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/download.php/filename/file.pdf")
        >>> d.match_extension(".php", directory_allowed = True)
        True
        >>> d.match_extension(".php", directory_allowed = False)
        False

        Double extension is supported, as it can come in handy when analyzing malware URLs:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/malicious.pdf.exe")
        >>> d.filebase
        'malicious.pdf'
        >>> d.extension
        '.exe'
        >>> d.match_extension(".pdf")
        True
        >>> d.match_extension(".exe")
        True

        The double extension support can be disabled by setting the 'double_allowed' argument to False:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/malicious.pdf.exe")
        >>> d.match_extension(".pdf", double_allowed = True)
        True
        >>> d.match_extension(".pdf", double_allowed = False)
        False

        String comparisons are case insensitive by default:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/index.html")
        >>> d.match_extension(".html")
        True
        >>> d.match_extension(".HTML")
        True

        This too can be configured, just set 'case_insensitive' to False:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/index.html")
        >>> d.match_extension(".HTML", case_insensitive = True)
        True
        >>> d.match_extension(".HTML", case_insensitive = False)
        False

        :param extension: Extension to match.
        :type extension: str

        :param directory_allowed: True to match extensions in all path components, False to match only the last one.
        :type directory_allowed: bool

        :param double_allowed: True to support double extensions, False to handle only standard extensions.
        :type double_allowed: bool

        :param case_insensitive: True for case insensitive string comparisons, False for case sensitive comparisons.
        :type case_insensitive: bool

        :returns: True if the extension was found, False otherwise.
        :rtype: bool
        """
        # TODO: maybe use **kwargs so we can support 'case_sensitive' (common mistake),
        # but do not document it so people don't get used to it :P
        if not extension.startswith("."):
            extension = "." + extension
        if case_insensitive:
            extension = extension.lower()
        if directory_allowed:
            components = self.path.split("/")
        else:
            components = [self.filename]
        for token in components:
            base, ext = splitext(token)
            if case_insensitive:
                ext = ext.lower()
            if ext == extension:
                return True
            if double_allowed:
                while True:
                    base, ext = splitext(base)
                    if not ext: break
                    if case_insensitive:
                        ext = ext.lower()
                    if ext == extension:
                        return True
        return False


    #--------------------------------------------------------------------------
    def get_all_extensions(self, directory_allowed = True, double_allowed = True):
        """
        Tries to find any possible file extensions from the URL path.

        By default every component of the path is parsed:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/download.php/filename/file.pdf")
        >>> d.get_all_extensions()
        ['.php', '.pdf']

        However you can set the 'directory_allowed' to False to parse only the last component:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/download.php/filename/file.pdf")
        >>> d.get_all_extensions(directory_allowed = False)
        ['.pdf']
        >>> d.get_all_extensions(directory_allowed = True)
        ['.php', '.pdf']

        Double extension is supported, as it can come in handy when analyzing malware URLs:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/malicious.pdf.exe")
        >>> d.filebase
        'malicious.pdf'
        >>> d.extension
        '.exe'
        >>> d.get_all_extensions()
        ['.pdf', '.exe']

        The double extension support can be disabled by setting the 'double_allowed' argument to False:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/malicious.pdf.exe")
        >>> d.get_all_extensions(double_allowed = False)
        ['.exe']
        >>> d.get_all_extensions(double_allowed = True)
        ['.pdf', '.exe']

        :param directory_allowed: True to match extensions in all path components, False to match only the last one.
        :type directory_allowed: bool

        :param double_allowed: True to support double extensions, False to handle only standard extensions.
        :type double_allowed: bool

        :returns: List of extensions in the order in which they were found.
        :rtype: list(str)
        """
        found = []
        if directory_allowed:
            components = self.path.split("/")
        else:
            components = [self.filename]
        for token in components:
            base, ext = splitext(token)
            pos = len(found)
            if ext:
                found.append(ext)
            if double_allowed:
                while True:
                    base, ext = splitext(base)
                    if not ext: break
                    found.insert(pos, ext)
        return found


    #--------------------------------------------------------------------------
    def split_hostname(self):
        """
        Splits the hostname into the subdomain, domain and TLD parts.

        For example:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/")
        >>> d.split_hostname()
        ('www', 'example', 'com')
        >>> d = ParsedURL("http://some.subdomain.of.example.co.uk/")
        >>> d.split_hostname()
        ('some.subdomain.of', 'example', 'co.uk')
        >>> '.'.join(d.split_hostname())
        'some.subdomain.of.example.co.uk'

        :returns: Subdomain, domain and TLD.
        :rtype: tuple(str, str, str)
        """
        return split_hostname(self.hostname)


    #--------------------------------------------------------------------------
    # Read-only properties.

    @property
    def url(self):
        scheme = self.__scheme
        fragment = self.__fragment
        request_uri = self.request_uri
        if scheme:
            scheme += "://"
        if fragment:
            request_uri = "%s#%s" % (request_uri, quote(fragment, safe=''))
        return "%s%s%s" % (scheme, self.netloc, request_uri)

    @property
    def base_url(self):
        scheme = self.__scheme
        if scheme:
            scheme += "://"
        base_url = scheme + self.netloc
        if scheme != "mailto":
            base_url += "/"
        return base_url

    @property
    def request_uri(self):
        path = quote_plus(self.__path, safe='/')
        query = self.query
        if query:
            char = self.__query_char
            if path.endswith(char):
                path = path + query
            else:
                path = "%s%s%s" % (path, char, query)
        return path


    #--------------------------------------------------------------------------
    # Read-write properties.

    @property
    def scheme(self):
        return self.__scheme

    @scheme.setter
    def scheme(self, scheme):
        if scheme:
            scheme = to_utf8( scheme.strip().lower() )
            if scheme.endswith('://'):
                scheme = scheme[:-3].strip()
            if scheme and scheme not in self.default_ports:
                raise ValueError("URL scheme not supported: %s" % scheme)
        else:
            scheme = ''
        self.__scheme = scheme

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        if not username:
            username = ''
        else:
            username = to_utf8(username)
        self.__username = username

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        if not password:
            password = ''
        else:
            password = to_utf8(password)
        self.__password = password

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, host):
        if not host:
            host = ''
        else:
            host = to_utf8(host)
            if host.startswith('[') and host.endswith(']'):
                host = host.upper()
            else:
                host = host.strip().lower()
        self.__host = host

    @property
    def port(self):
        port = self.__port
        if not port:
            port = self.default_ports.get(self.__scheme, None)
        return port

    @port.setter
    def port(self, port):
        if not port:
            port = None
        elif not 1 <= port <= 65535:
            raise ValueError("Bad port number: %r" % port)
        self.__port = port

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        if not path:
            path = '/'
        else:
            path = to_utf8(path)
        if not path.startswith('/'):
            path = '/' + path
        if path == '/' and self.__scheme == 'mailto':
            path = ''
        self.__path = path

    @property
    def fragment(self):
        return self.__fragment

    @fragment.setter
    def fragment(self, fragment):
        if not fragment:
            fragment = ''
        else:
            fragment = to_utf8(fragment)
            if fragment.startswith('#'):
                warn("You don't need to use a leading '#' when setting the"
                     " fragment, this may be an error!", stacklevel=3)
        self.__fragment = fragment

    @property
    def query_char(self):
        return self.__query_char

    @query_char.setter
    def query_char(self, query_char):
        if not query_char:
            query_char = '?'
        else:
            query_char = to_utf8(query_char)
            if query_char not in ('?', '/'):
                raise ValueError(
                    "Invalid query separator character: %r" % query_char)
        self.__query_char = query_char

    @property
    def query(self):
        # TODO: according to this: https://en.wikipedia.org/wiki/URL_normalization
        # sorting the query parameters may break semantics. To fix this we may want
        # to try to preserve the original order when possible. The problem then is
        # we'd "see" URLs with the same parameters in different order as different.
        if not self.__query_params:
            if self.__query is not None:  # when it can't be parsed
                return self.__query
            return ''
        return '&'.join( '%s=%s' % ( quote(k, safe=''), quote(v, safe='') )
                         for (k, v) in sorted(self.__query_params.iteritems()) )

    @query.setter
    def query(self, query):
        if query and query.startswith('?'):
            warn("You don't need to use a leading '?' when setting the query"
                 " string, this may be an error!", stacklevel=3)
        if not query:
            query_params = {}
        else:
            try:
                # much faster than parse_qsl()
                query_params = dict(( map(unquote_plus, (to_utf8(token) + '=').split('=', 2)[:2])
                                      for token in query.split('&') ))
                if len(query_params) == 1 and not query_params.values()[0]:
                    query_params = {}
                else:
                    query = None
            except Exception:
                ##raise   # XXX DEBUG
                query_params = {}
        self.__query, self.__query_params = query, query_params

    @property
    def query_params(self):
        return self.__query_params

    @query_params.setter
    def query_params(self, query_params):
        if query_params is None:
            self.__query = None
            self.__query_params = {}
        else:
            query_params = dict(query_params)
            self.__query = None
            self.__query_params = query_params
            self.__query = self.query


    #--------------------------------------------------------------------------
    # Aliases.

    @property
    def all_extensions(self):
        """
        When the filename of an URL has a double extension, this property
        will give you all of them instead of just the last one (as
        'extension' does).

        Example:

        >>> from golismero.api.net.web_utils import ParsedURL
        >>> d = ParsedURL("http://www.example.com/malicious.pdf.exe")
        >>> d.filename
        'malicious.pdf.exe'
        >>> d.filebase
        'malicious.pdf'
        >>> d.extension
        '.exe'
        >>> d.minimal_filebase
        'malicious'
        >>> d.all_extensions
        '.pdf.exe'
        >>> d.extension = '.test'
        >>> d.filename
        'malicious.pdf.test'
        >>> d.all_extensions = '.malware'
        >>> d.filename
        'malicious.malware'
        """
        ext = self.filename
        pos = ext.find(".")
        if pos > 0:
            return ext[ pos : ]
        return ""

    @all_extensions.setter
    def all_extensions(self, extension):
        filename  = self.filename
        dot_pos   = filename.find(".")
        filebase  = filename[ : dot_pos ] if dot_pos > 0 else filename
        if extension and extension[0] != ".":
            extension = "." + extension
        self.path = join(self.directory, filebase + extension)

    @property
    def minimal_filebase(self):
        ":see: all_extensions"
        return self.filename[ : -len(self.all_extensions) ]

    @minimal_filebase.setter
    def minimal_filebase(self, filebase):
        self.filename = filebase + self.all_extensions

    @property
    def directory(self):
        return split(self.__path)[0]

    @directory.setter
    def directory(self, directory):
        self.path = join(directory, self.filename)

    hostname = host
    folder = directory

    @property
    def filename(self):
        return split(self.__path)[1]

    @filename.setter
    def filename(self, filename):
        self.path = join(self.directory, filename)

    @property
    def filebase(self):
        return splitext(self.filename)[0]

    @filebase.setter
    def filebase(self, filebase):
        self.path = join(self.directory, filebase + self.extension)

    @property
    def extension(self):
        return splitext(self.filename)[1]

    @extension.setter
    def extension(self, extension):
        if extension:
            if "." in extension[1:]:
                raise ValueError("To set a double extension use the all_extensions property instead")
            self.path = join(self.directory, self.filebase + (extension if extension[0] == "." else "." + extension))
        else:
            self.path = join(self.directory, self.filebase)

    @property
    def netloc(self):
        host = self.__host
        if not (host.startswith('[') and host.endswith(']')):
            host = quote(host, safe='.')
        port = self.port
        auth = self.auth
        if port and port in self.default_ports.values():
            port = None
        if auth:
            host = "%s@%s" % (auth, host)
        if port:
            host = "%s:%s" % (host, port)
        return host

    @netloc.setter
    def netloc(self, netloc):
        if '@' in netloc:
            auth, host = netloc.split('@', 1)
        else:
            auth, host = None, netloc
        port = ''
        if host and host[0] == '[':
            host, port = host[1:].split(']', 1)
            if ':' in port:
                _host, port = port.split(':', 1)
                if not host:
                    host = _host
        elif ':' in host:
            host, port = host.split(':', 1)
        if '%' in port:
            port = unquote(port)
        if port:
            port = int(port)
        if host:
            host = unquote_plus(host)
        self.auth = auth  # TODO: roll back changes if it fails
        self.host = host
        self.port = port

    @property
    def auth(self):
        auth = ''
        username = self.__username
        password = self.__password
        if username:
            if password:
                auth = "%s:%s" % (quote(username, safe=''), quote(password, safe=''))
            else:
                auth = quote(username, safe='')
        elif password:
            auth = ":%s" % quote(password, safe='')
        return auth

    @auth.setter
    def auth(self, auth):
        if auth:
            if ':' in auth:
                username, password = auth.split(':', 1)
                self.__username = unquote_plus(username)
                self.__password = unquote_plus(password)
            else:
                self.__username = unquote_plus(auth)
                self.__password = ''
        else:
            self.__username = ''
            self.__password = ''

    @property
    def subdomain(self):
        return self.split_hostname()[0]

    @subdomain.setter
    def subdomain(self, subdomain):
        _, domain, tld = self.split_hostname()
        self.hostname = ".".join((subdomain, domain, tld))

    @property
    def domain(self):
        return self.split_hostname()[1]

    @domain.setter
    def domain(self, domain):
        subdomain, _, tld = self.split_hostname()
        self.hostname = ".".join((subdomain, domain, tld))

    @property
    def tld(self):
        return self.split_hostname()[2]

    @tld.setter
    def tld(self, tld):
        subdomain, domain, _ = self.split_hostname()
        self.hostname = ".".join((subdomain, domain, tld))


#------------------------------------------------------------------------------
class HTMLElement (object):
    """
    HTML element object.
    """


    #--------------------------------------------------------------------------
    def __init__(self, tag_name, attrs, content):
        """
        :param tag_name: HTML tag name.
        :type tag_name: str

        :param attr: HTML tag attributes.
        :type attr: dict(str -> str)

        :param content: Raw HTML.
        :type content: str
        """
        self.__tag_name = to_utf8(tag_name)
        self.__content  = to_utf8(content)
        self.__attrs = {
            to_utf8(k): to_utf8(v)
            for k,v in attrs.iteritems()
        }


    #--------------------------------------------------------------------------
    def __str__(self):
        return "%s:%s" % (self.__tag_name, str(self.__attrs))


    #--------------------------------------------------------------------------
    @property
    def tag_name(self):
        """
        :returns: HTML tag name.
        :rtype: str
        """
        return self.__tag_name


    #--------------------------------------------------------------------------
    @property
    def attrs(self):
        """
        :returns: HTML tag attributes.
        :rtype: dict(str -> str)
        """
        return self.__attrs


    #--------------------------------------------------------------------------
    @property
    def content(self):
        """
        :returns: Raw HTML.
        :rtype: str
        """
        return self.__content


#------------------------------------------------------------------------------
class HTMLParser(object):
    """
    HTML parser.

    HTMLParser is a transparent wrapper for the other libraries.
    This parser aims to simplify the logic of HTML parsing.

    .. warning::
       You should use this function instead of calling other libraries to ensure
       your plugin remains compatible with future versions of GoLismero.

    Example:

    >>> from golismero.api.net.web_utils import HTMLParser
    >>> html_info = \"\"\"<html>
    ... <head>
    ...   <title>My sample page</title>
    ... </head>
    ... <body>
    ...   <a href="http://www.mywebsitelink.com">Link 1</a>
    ...   <p>
    ...     <img src="/images/my_image.png" />
    ...   </p>
    ... </body>
    ... </html>\"\"\"
    ...
    >>> html_parsed = HTMLParser(html_info)
    >>> html_parsed.links
    [<golismero.api.net.web_utils.HTMLElement object at 0x109ca8b50>]
    >>> html_parsed.links[0].tag_name
    'a'
    >>> html_parsed.links[0].tag_content
    'Link 1'
    >>> html_parsed.links[0].attrs
    {'href': 'http://www.mywebsitelink.com'}
    >>> html_parsed.images[0].tag_name
    'img'
    >>> html_parsed.images[0].tag_content
    ''
    """


    #--------------------------------------------------------------------------
    def __init__(self, data):
        """
        :param data: Raw HTML content.
        :type data: str
        """

        # Raw HTML content
        self.__raw_data = to_utf8(data)

        # Init parser
        self.__html_parser = BeautifulSoup(self.__raw_data)

        #
        # Parsed HTML elementes
        #

        # All elements
        self.__all_elements = None

        # HTML forms
        self.__html_forms = None

        # Images in HTML
        self.__html_images = None

        # Links in HTML
        self.__html_links = None

        # CSS links
        self.__html_css = None

        # CSS embedded
        self.__html_css_embedded = None

        # Javascript
        self.__html_javascript = None

        # Javascript embedded
        self.__html_javascript_embedded = None

        # Objects
        self.__html_objects = None

        # Metas
        self.__html_metas = None

        # Title
        self.__html_title = None


    #--------------------------------------------------------------------------
    def __convert_to_HTMLElements(self, data):
        """
        Convert parser format to list of HTML Elements.

        :return: list of HTMLElements
        """
        return [
            HTMLElement(
                x.name.encode("utf-8"),
                { v[0].encode("utf-8"): v[1].encode("utf-8") for v in x.attrs},
                "".join(( str(item) for item in x.contents if item != "\n"))
                ) for x in data
        ]


    #--------------------------------------------------------------------------
    @property
    def raw_data(self):
        """
        :return: Get raw HTML code
        :rtype: str
        """
        return self.__raw_data


    #--------------------------------------------------------------------------
    @property
    def elements(self):
        """
        :return: Get all HTML elements as a list of HTMLElement objects
        :rtype: list(HTMLElement)
        """
        if self.__all_elements is None:
            m_result = self.__html_parser.findAll()
            self.__all_elements = self.__convert_to_HTMLElements(m_result)
        return self.__all_elements


    #--------------------------------------------------------------------------
    @property
    def forms(self):
        """
        :return: Get forms from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_forms is None:
            m_elem = self.__html_parser.findAll("form")
            self.__html_forms = self.__convert_to_HTMLElements(m_elem)
        return self.__html_forms


    #--------------------------------------------------------------------------
    @property
    def images(self):
        """
        :return: Get images from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_images is None:
            m_elem = self.__html_parser.findAll("img")
            self.__html_images = self.__convert_to_HTMLElements(m_elem)
        return self.__html_images


    #--------------------------------------------------------------------------
    @property
    def url_links(self):
        """
        :return: Get links from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_links is None:
            m_elem = self.__html_parser.findAll("a")
            self.__html_links = self.__convert_to_HTMLElements(m_elem)
        return self.__html_links


    #--------------------------------------------------------------------------
    @property
    def css_links(self):
        """
        :return: Get CSS links from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_css is None:
            m_elem = self.__html_parser.findAll(name="link", attrs={"rel":"stylesheet"})
            self.__html_css = self.__convert_to_HTMLElements(m_elem)
        return self.__html_css


    #--------------------------------------------------------------------------
    @property
    def javascript_links(self):
        """
        :return: Get JavaScript links from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_javascript is None:
            m_elem = self.__html_parser.findAll(name="script", attrs={"src": True})
            self.__html_javascript = self.__convert_to_HTMLElements(m_elem)
        return self.__html_javascript


    #--------------------------------------------------------------------------
    @property
    def css_embedded(self):
        """
        :return: Get embedded CSS from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_css_embedded is None:
            m_elem = self.__html_parser.findAll("style")
            self.__html_css_embedded = self.__convert_to_HTMLElements(m_elem)
        return self.__html_css_embedded


    #--------------------------------------------------------------------------
    @property
    def javascript_embedded(self):
        """
        :return: Get embedded JavaScript from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_javascript_embedded is None:
            m_elem = self.__html_parser.findAll(name="script", attrs={"src": False})
            self.__html_javascript_embedded = self.__convert_to_HTMLElements(m_elem)
        return self.__html_javascript_embedded


    #--------------------------------------------------------------------------
    @property
    def metas(self):
        """
        :return: Get meta tags from HTML as a list of HTMLElement objects
        :rtype: HTMLElement
        """
        if self.__html_metas is None:
            m_elem = self.__html_parser.findAll(name="meta")
            self.__html_metas = self.__convert_to_HTMLElements(m_elem)
        return self.__html_metas


    #--------------------------------------------------------------------------
    @property
    def title(self):
        """
        :return: Get title from HTML as a HTMLElement object
        :rtype: HTMLElement
        """
        if self.__html_title is None:
            m_elem = self.__html_parser.findAll(name="title", recursive=False, limit=1)
            self.__html_title = m_elem.name.encode("utf-8")
        return self.__html_title


    #--------------------------------------------------------------------------
    @property
    def objects(self):
        """
        :return: Get object tags from HTML as a list of HTMLElement objects
        :rtype: HTMLElement"""

        if self.__html_objects is None:
            m_elem = self.__html_parser.findAll(name="object")

            m_result = []
            m_result_append_bind = m_result.append

            for obj in m_elem:
                # Get attrs
                m_ojb_attr = { v[0].encode("utf-8"): v[1].encode("utf-8") for v in obj.attrs }

                # Add param attr
                m_ojb_attr["param"] = {}

                # Add value for params
                update = m_ojb_attr["param"].update
                for param in obj.findAllNext("param"):
                    update({ k[0].encode("utf-8"): k[1].encode("utf-8") for k in param.attrs})

                m_raw_content = "".join((str(item) for item in obj.contents if item != "\n"))

                m_result_append_bind(HTMLElement(obj.name.encode("utf-8"), m_ojb_attr, m_raw_content))

            self.__html_objects = m_result

        return self.__html_objects
