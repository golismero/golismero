#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Universal Resource Locator (URL).
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

__all__ = ["BaseUrl", "FolderUrl", "Url"]

from . import Resource
from .domain import Domain
from .ip import IP
from .. import identity
from ...config import Config
from ...net.web_utils import ParsedURL


#------------------------------------------------------------------------------
class _AbstractUrl(Resource):
    """
    Abstract class for all URL based resources.
    """

    # Not true, but this bypasses an integrity check in the metaclass.
    resource_type = Resource.RESOURCE_URL


    #--------------------------------------------------------------------------
    def __init__(self, url):
        """
        :param url: Absolute URL.
        :type url: str

        :raises ValueError: Relative URLs are not allowed.
        """

        if not isinstance(url, basestring):
            raise TypeError("Expected string, got %r instead" % type(url))
        url = str(url)

        # Parse, verify and canonicalize the URL.
        # TODO: if relative, make it absolute using the referer when available.
        parsed = ParsedURL(url)
        if not parsed.host or not parsed.scheme:
            raise ValueError("Only absolute URLs must be used! Got: %r" % url)
        if parsed.scheme == "mailto":
            raise ValueError("For emails use the Email type instead! Got: %r" % url)
        if parsed.scheme not in ("http", "https", "ftp"):
            raise ValueError("URL scheme not supported: %r" % parsed.scheme)
        url = parsed.url

        # URL.
        self.__url = url

        # Parsed URL.
        self.__parsed_url = parsed

        # Parent constructor.
        super(_AbstractUrl, self).__init__()


    #--------------------------------------------------------------------------

    @identity
    def url(self):
        """
        :return: URL in canonical form.
        :rtype: str
        """
        return self.__url


    #--------------------------------------------------------------------------

    @property
    def parsed_url(self):
        """
        :return: URL in decomposed form.
        :rtype: ParsedURL
        """
        return self.__parsed_url

    @property
    def hostname(self):
        """
        :return: Hostname this URL points to.
        :rtype: str
        """
        return self.parsed_url.hostname

    @property
    def path(self):
        """
        :return: Path component of the URL.
        :rtype: str
        """
        return self.parsed_url.path

    @property
    def is_https(self):
        """
        :return: True if it's HTTPS, False otherwise.
        :rtype: bool
        """
        return self.parsed_url.scheme == "https"


    #--------------------------------------------------------------------------
    def __str__(self):
        return self.url


    #--------------------------------------------------------------------------
    def __repr__(self):
        cls = self.__class__.__name__
        if "." in cls:
            cls = cls[ cls.rfind(".") + 1 : ]
        return "<%s url=%r>" % (cls, self.url)


    #--------------------------------------------------------------------------
    def is_in_scope(self):
        return self.url in Config.audit_scope


#------------------------------------------------------------------------------
class Url(_AbstractUrl):
    """
    Universal Resource Locator (URL).

    You can get the URL in canonical form:

    - url

    In deconstructed form:

    - parsed_url

    The current crawling depth level:

    - depth

    And some extra information needed to build an HTTP request:

    - method
    - url_params
    - post_params
    - referer
    """

    resource_type = Resource.RESOURCE_URL


    #--------------------------------------------------------------------------
    def __init__(self, url, method = "GET", post_params = None, referer = None):
        """
        :param url: Absolute URL.
        :type url: str

        :param method: HTTP method.
        :type method: str

        :param post_params: POST parameters.
        :type post_params: dict(str -> str)

        :param referer: Referrer URL.
        :type referer: str

        :raises ValueError: Currently, relative URLs are not allowed.
        """

        # Validate the argument types.
        if not isinstance(method, str):
            raise TypeError("Expected string, got %r instead" % type(method))
        if post_params is not None and not isinstance(post_params, dict):
            raise TypeError("Expected dict, got %r instead" % type(post_params))
        if referer is not None and not isinstance(referer, str):
            raise TypeError("Expected string, got %r instead" % type(referer))

        # Save the properties.
        self.__method      = method if method else "GET"
        self.__post_params = post_params if post_params else {}
        self.__referer     = referer

        # Call the parent constructor.
        super(Url, self).__init__(url)

        # Increment the crawling depth by one.
        self.depth += 1


    #--------------------------------------------------------------------------
    def __repr__(self):
        s = "<Url url=%r, method=%r, params=%r, referer=%r, depth=%r>"
        s %= (self.url, self.method, self.post_params, self.referer, self.depth)
        return s


    #--------------------------------------------------------------------------

    @identity
    def method(self):
        """
        :return: HTTP method.
        :rtype: str
        """
        return self.__method

    @identity
    def post_params(self):
        """
        :return: POST parameters.
        :rtype: dict(str)
        """
        return self.__post_params


    #--------------------------------------------------------------------------

    @property
    def url_params(self):
        """
        :return: GET parameters.
        :rtype: dict(str -> str)
        """
        query = self.parsed_url.query
        if type(query) not in (str, unicode):
            return query
        return {}

    @property
    def has_url_param(self):
        """
        :return: True if there are GET parameters, False otherwise.
        :rtype: bool
        """
        return bool(self.url_params)

    @property
    def has_post_param(self):
        """
        :return: True if there are POST parameters, False otherwise.
        :rtype: bool
        """
        return bool(self.post_params)

    @property
    def referer(self):
        """
        :return: Referer for this URL.
        :rtype: str
        """
        return self.__referer


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        if self.is_in_scope():
            result = FolderUrl.from_url(self.url)
            result.append( BaseUrl(self.url) )
            try:
                result.append( IP(self.hostname) )
            except ValueError:
                result.append( Domain(self.hostname) )
            return result
        return []


#------------------------------------------------------------------------------
class BaseUrl(_AbstractUrl):
    """
    Base URL.

    Unlike the Url type, which refers to any URL, this type is strictly for
    root level URLs in a web server. Plugins that only run once per web server
    should probably receive this data type.

    For example, a plugin receiving both BaseUrl and Url may get this input:

    - BaseUrl("http://www.example.com/")
    - Url("http://www.example.com/")
    - Url("http://www.example.com/index.php")
    - Url("http://www.example.com/admin.php")
    - Url("http://www.example.com/login.php")

    Notice how the root level URL is sent twice,
    once as BaseUrl and again the more generic Url.
    """

    resource_type = Resource.RESOURCE_BASE_URL


    #--------------------------------------------------------------------------
    def __init__(self, url):
        """
        :param url: Any **absolute** URL. The base will be extracted from it.
        :type url: str

        :raises ValueError: Only absolute URLs must be used.
        """

        # Validate the argument types.
        if not isinstance(url, basestring):
            raise TypeError("Expected string, got %r instead" % type(url))
        url = str(url)

        # Parse, verify and canonicalize the URL.
        parsed = ParsedURL(url)
        if not parsed.host or not parsed.scheme:
            raise ValueError("Only absolute URLs must be used! Got: %r" % url)

        # Convert it into a base URL.
        parsed.auth = None
        parsed.path = "/"
        parsed.fragment = None
        parsed.query = None
        parsed.query_char = None
        url = parsed.url

        # Call the parent constructor.
        super(BaseUrl, self).__init__(url)

        # Reset the crawling depth.
        self.depth = 0


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        if self.is_in_scope():
            try:
                return [IP(self.hostname)]
            except ValueError:
                return [Domain(self.hostname)]
        return []


#------------------------------------------------------------------------------
class FolderUrl(_AbstractUrl):
    """
    Folder URL.

    Unlike the Url type, which refers to an URL that's linked or somehow found
    to be valid, the FolderUrl type refers to inferred URLs to folders detected
    within another URL.

    This makes it semantically different, since there's no guarantee that the
    URL actually points to a valid resource, nor that it belongs to the normal
    web access flow.

    For example, a plugin receiving both FolderUrl and Url may get this input:

    - Url("http://www.example.com/wp-content/uploads/2013/06/attachment.pdf")
    - FolderUrl("http://www.example.com/wp-content/uploads/2013/06/")
    - FolderUrl("http://www.example.com/wp-content/uploads/2013/")
    - FolderUrl("http://www.example.com/wp-content/uploads/")
    - FolderUrl("http://www.example.com/wp-content/")

    Note that the folder URLs may or may not be sent again as an Url object.
    For example, for a site that has a link to the "incoming" directory in its
    index page, we may get something like this:

    - Url("http://www.example.com/index.html")
    - Url("http://www.example.com/incoming/")
    - FolderUrl("http://www.example.com/incoming/")

    FolderUrl objects are never sent for the root folder of a web site.
    For that, see the BaseUrl data type.
    """

    resource_type = Resource.RESOURCE_FOLDER_URL


    #--------------------------------------------------------------------------
    def __init__(self, url):
        """
        :param url: Absolute URL to a folder.
        :type url: str

        :raises ValueError: The URL wasn't absolute or didn't point to a folder.
        """

        if not isinstance(url, basestring):
            raise TypeError("Expected string, got %r instead" % type(url))
        url = str(url)

        # Parse, verify and canonicalize the URL.
        parsed = ParsedURL(url)
        if not parsed.host or not parsed.scheme:
            raise ValueError("Only absolute URLs must be used! Got: %r" % url)
        if not parsed.path.endswith("/"):
            raise ValueError("URL does not point to a folder! Got: %r" % url)

        # Call the parent constructor.
        super(FolderUrl, self).__init__(parsed.url)


    #--------------------------------------------------------------------------
    @staticmethod
    def from_url(url):
        """
        :param url: Any **absolute** URL. The folder will be extracted from it.
        :type url: str

        :returns: Inferred folder URLs.
        :rtype: list(FolderUrl)

        :raises ValueError: Only absolute URLs must be used.
        """
        assert isinstance(url, basestring)

        # Parse, verify and canonicalize the URL.
        parsed = ParsedURL(url)
        if not parsed.host or not parsed.scheme:
            raise ValueError("Only absolute URLs must be used! Got: %r" % url)

        # Extract the folders from the path.
        path = parsed.path
        folders = path.split("/")
        if not path.endswith("/"):
            folders.pop()

        # Convert the URL to a base URL.
        parsed.auth = None
        parsed.path = "/"
        parsed.fragment = None
        parsed.query = None
        parsed.query_char = None

        # Generate a new folder URL for each folder.
        folder_urls = {parsed.url}
        for folder in folders:
            if folder:
                parsed.path += folder + "/"
                folder_urls.add(parsed.url)

        # Return the generated URLs.
        return [FolderUrl(x) for x in folder_urls]


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        if self.is_in_scope():
            result = [ BaseUrl(self.url) ]
            try:
                result.append( IP(self.hostname) )
            except ValueError:
                result.append( Domain(self.hostname) )
            return result
        return []
