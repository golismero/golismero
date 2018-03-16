#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTTP protocol API for GoLismero.
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
Golismero project mail: contact@golismero-project.com

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

__all__ = ["HTTP"]

from . import ConnectionSlot, NetworkException, NetworkOutOfScope
from .cache import NetworkCache
from .web_utils import detect_auth_method, get_auth_obj
from ..config import Config
from ..data import LocalDataCache, discard_data
from ..data.information.http import HTTP_Request, HTTP_Response, HTTP_Raw_Request
from ..data.resource.url import URL
from ...common import Singleton, get_data_folder

from hashlib import md5
from os import environ
from os.path import join
from requests import Session
from requests.cookies import cookiejar_from_dict
from requests.exceptions import RequestException
from socket import socket, error, getaddrinfo, SOCK_STREAM
from ssl import wrap_socket
from StringIO import StringIO
from time import time


#------------------------------------------------------------------------------
class _HTTP(Singleton):
    """
    HTTP protocol API for GoLismero.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        self.__session = None


    #--------------------------------------------------------------------------
    def _initialize(self):
        """
        .. warning: Called automatically by GoLismero. Do not call!
        """

        # Start a new session.
        self.__session = Session()

        # Load the proxy settings.
        proxy_addr = Config.audit_config.proxy_addr
        if proxy_addr:
            proxy_port = Config.audit_config.proxy_port
            if proxy_port:
                proxy_addr = "%s:%s" % (proxy_addr, proxy_port)
            auth_user = Config.audit_config.proxy_user
            auth_pass = Config.audit_config.proxy_pass
            auth, _ = detect_auth_method(proxy_addr)
            self.__session.auth = get_auth_obj(auth, auth_user, auth_pass)
            self.__session.proxies = {
                "http":  proxy_addr,
                "https": proxy_addr,
                "ftp":   proxy_addr,
            }

        # Load the cookies.
        cookie = Config.audit_config.cookie
        if cookie:
            self.__session.cookies = cookiejar_from_dict(cookie)

        # Set User Agent
        self.__user_agent = Config.audit_config.user_agent


    #--------------------------------------------------------------------------
    def _finalize(self):
        """
        .. warning: Called automatically by GoLismero. Do not call!
        """
        self.__session = None


    #--------------------------------------------------------------------------
    def get_url(self, url, method = "GET", callback = None,
                     timeout = 10.0, use_cache = None, allow_redirects = True,
                     allow_out_of_scope = False):
        """
        Send a simple HTTP request to the server and get the response back.

        :param url: URL to request.
        :type url: str

        :param method: HTTP method.
        :type method: str

        :param callback: Callback function.
        :type callback: callable

        :param timeout: Timeout in seconds.
            The minimum value is 0.5 and the maximum is 100.0. Any other values
            will be silently converted to either one of them.
        :type timeout: int | float

        :param use_cache: Control the use of the cache.
                          Use True to force the use of the cache,
                          False to force not to use it,
                          or None for automatic.
        :type use_cache: bool | None

        :param allow_redirects: True to follow redirections, False otherwise.
        :type allow_redirects: bool

        :param allow_out_of_scope: True to allow requests out of scope, False otherwise.
        :type allow_out_of_scope: bool

        :returns: HTTP response, or None if the request was cancelled.
        :rtype: HTTP_Response | None

        :raises NetworkOutOfScope: The resource is out of the audit scope.
            Note that this can happen even if the URL has been checked against
            Config.audit_scope -- if the server responds with a
            redirection against another URL that's out of scope.
        :raises NetworkException: A network error occurred.
        """
        request = HTTP_Request(url, method = method, user_agent=self.__user_agent)
        LocalDataCache.on_autogeneration(request)
        return self.make_request(request, callback = callback,
                                 timeout = timeout, use_cache = use_cache,
                                 allow_redirects = allow_redirects,
                                 allow_out_of_scope = allow_out_of_scope)


    #--------------------------------------------------------------------------
    def make_request(self, request, callback = None,
                     timeout = 10.0, use_cache = None,
                     allow_redirects = True,
                     allow_out_of_scope = False):
        """
        Send an HTTP request to the server and get the response back.

        :param request: HTTP request to send.
        :type request: HTTP_Request

        :param callback: Callback function.
        :type callback: callable

        :param timeout: Timeout in seconds.
            The minimum value is 0.5 and the maximum is 100.0. Any other values
            will be silently converted to either one of them.
        :type timeout: int | float

        :param use_cache: Control the use of the cache.
                          Use True to force the use of the cache,
                          False to force not to use it,
                          or None for automatic.
        :type use_cache: bool | None

        :param allow_redirects: True to follow redirections, False otherwise.
        :type allow_redirects: bool

        :param allow_out_of_scope: True to allow requests out of scope, False otherwise.
        :type allow_out_of_scope: bool

        :returns: HTTP response, or None if the request was cancelled.
        :rtype: HTTP_Response | None

        :raises NetworkOutOfScope: The resource is out of the audit scope.
        :raises NetworkException: A network error occurred.
        """

        # Check initialization.
        if self.__session is None:
            self._initialize()

        # Check the arguments.
        if not isinstance(request, HTTP_Request):
            raise TypeError("Expected HTTP_Request, got %r instead" % type(request))
        if callback is not None and not callable(callback):
            raise TypeError(
                "Expected callable (function, class, instance with __call__),"
                " got %r instead" % type(callback)
            )
        if use_cache not in (True, False, None):
            raise TypeError("Expected bool or None, got %r instead" % type(use_cache))

        # Check the request scope.
        if not request.is_in_scope() and allow_out_of_scope is False:
            raise NetworkOutOfScope("URL out of scope: %s" % request.url)

        # Sanitize the timeout value.
        if timeout:
            timeout = float(timeout)
            if timeout > 100.0:
                timeout = 100.0
            elif timeout < 0.5:
                timeout = 0.5
        else:
            timeout = 0.5

        # If the cache is enabled, try to fetch the cached response.
        cache_key = None
        if use_cache is not False:
            cache_key = "%s|%s|%s" % (request.method, request.url, request.post_data)
            cache_key = md5(cache_key).hexdigest()
            cached_resp = NetworkCache.get(cache_key, request.parsed_url.scheme)

            # Do we have a cache hit?
            if cached_resp is not None:

                # Build the HTTP response object.
                raw_response, elapsed = cached_resp
                response = HTTP_Response(
                    request      = request,
                    raw_response = raw_response,
                    elapsed      = elapsed,
                )

                # Call the user-defined callback.
                if callback is not None:
                    cont = callback(request,
                                    request.url,
                                    response.status,
                                    response.content_length,
                                    response.content_type)

                    # If the callback wants to abort...
                    if not cont:

                        # Discard the response.
                        discard_data(response)

                        # Abort.
                        return

                # Return the response.
                return response

        # Use a connection slot.
        with ConnectionSlot(request.hostname):

            # Filter the Host header to work around a Requests quirk.
            headers = request.headers.to_dict()
            try:
                del headers['host']
            except KeyError:
                pass

            # Send the request.
            try:
                t1 = time()
                resp = self.__session.request(
                    method  = request.method,
                    url     = request.url,
                    headers = headers,
                    data    = request.post_data,
                    ##files   = request.files,   # not supported yet!
                    verify  = False,
                    stream  = True,
                    timeout = timeout,
                    allow_redirects = allow_redirects,
                )
                t2 = time()
            except RequestException, e:
                raise NetworkException(str(e))

            try:

                # Get the response properties.
                url = resp.url
                status_code  = str(resp.status_code)
                content_type = resp.headers.get("Content-Type")
                try:
                    content_length = int(resp.headers["Content-Length"])
                except Exception:
                    content_length = None

                # If the final URL is different from the request URL,
                # abort if the new URL is out of scope.
                if url != request.url and url not in Config.audit_scope:
                    raise NetworkOutOfScope("URL out of scope: %s" % url)

                # Call the user-defined callback, and cancel if requested.
                if callback is not None:
                    cont = callback(request, url, status_code, content_length, content_type)
                    if not cont:
                        return

                # Autogenerate an URL object.
                # XXX FIXME: the depth level is broken!!!
                url_obj = None
                if url != request.url:
                    url_obj = URL(
                        url         = url,
                        method      = request.method,
                        post_params = request.post_data,
                        referer     = request.referer,
                    )
                    LocalDataCache.on_autogeneration(url_obj)

                # Download the contents.
                try:
                    t3 = time()
                    data = resp.content
                    t4 = time()
                except RequestException, e:
                    raise NetworkException(str(e))

                # Calculate the elapsed time.
                elapsed = (t2 - t1) + (t4 - t3)

                # Build an HTTP_Response object.
                # Since the requests library won't let us access the raw
                # response bytes, we have to "reconstruct" them.
                response = HTTP_Response(
                    request = request,
                    status  = status_code,
                    headers = resp.headers,
                    data    = data,
                    elapsed = elapsed,
                )

                # Link it to the originating URL.
                if url_obj is not None:
                    response.add_resource(url_obj)

                # If the cache is enabled, store the response in the cache.
                # When possible use the original key instead of recalculating it.
                # XXX FIXME the cache timestamps are broken!!!
                if use_cache is True or (use_cache is None and response.is_cacheable()):
                    if cache_key is None:
                        cache_key = "%s|%s|%s" % (request.method, url, request.post_data)
                        cache_key = md5(cache_key).hexdigest()
                    cached_resp = (response.raw_response, elapsed)
                    NetworkCache.set(cache_key, cached_resp, request.parsed_url.scheme)

                # Return the HTTP_Response object.
                return response

            finally:

                # Close the connection.
                resp.close()


    #--------------------------------------------------------------------------
    def make_raw_request(self, raw_request, host, port = 80, proto = "http",
                 callback = None, timeout = 10.0):
        """
        Send a raw HTTP request to the server and get the response back.

        .. note: This method does not support the use of the cache or a proxy.

        .. warning::
           This method only returns the HTTP response headers, **NOT THE CONTENT**.

        :param raw_request: Raw HTTP request to send.
        :type raw_request: HTTP_Raw_Request

        :param host: Hostname or IP address to connect to.
        :type host: str

        :param port: TCP port to connect to.
        :type port: int

        :param proto: Network protocol (that is, the URL scheme).
        :type proto: str

        :param callback: Callback function.
        :type callback: callable

        :param timeout: Timeout in seconds.
            The minimum value is 0.5 and the maximum is 100.0. Any other values
            will be silently converted to either one of them.
        :type timeout: int | float

        :param use_cache: Control the use of the cache.
                          Use True to force the use of the cache,
                          False to force not to use it,
                          or None for automatic.
        :type use_cache: bool | None

        :returns: HTTP response, or None if the request was cancelled.
        :rtype: HTTP_Response | None

        :raises NetworkOutOfScope: The resource is out of the audit scope.
        :raises NetworkException: A network error occurred.
        """

        # Abort if a proxy is configured, because we don't support this yet.
        if Config.audit_config.proxy_addr:
            raise NotImplementedError("Proxy not yet supported")

        # Check the arguments.
        if type(raw_request) is str:
            raw_request = HTTP_Raw_Request(raw_request)
            LocalDataCache.on_autogeneration(raw_request)
        elif not isinstance(raw_request, HTTP_Raw_Request):
            raise TypeError("Expected HTTP_Raw_Request, got %r instead" % type(raw_request))
        if type(host) == unicode:
            raise NotImplementedError("Unicode hostnames not yet supported")
        if type(host) != str:
            raise TypeError("Expected str, got %r instead" % type(host))
        if proto not in ("http", "https"):
            raise ValueError("Protocol must be 'http' or 'https', not %r" % proto)
        if port is None:
            if proto == "http":
                port = 80
            elif proto == "https":
                port = 443
            else:
                assert False, "internal error!"
        elif type(port) not in (int, long):
            raise TypeError("Expected int, got %r instead" % type(port))
        if port < 1 or port > 32767:
            raise ValueError("Invalid port number: %d" % port)
        if callback is not None and not callable(callback):
            raise TypeError(
                "Expected callable (function, class, instance with __call__),"
                " got %r instead" % type(callback)
            )

        # Check the request scope.
        if host not in Config.audit_scope:
            raise NetworkOutOfScope("Host out of scope: %s" % host)

        # Sanitize the timeout value.
        if timeout:
            timeout = float(timeout)
            if timeout > 100.0:
                timeout = 100.0
            elif timeout < 0.5:
                timeout = 0.5
        else:
            timeout = 0.5

        # Resolve the hostname.
        # FIXME: we're only using the first item, but we could use more
        #        than one, for example iterate through them if they fail.
        family, socktype, sockproto, canonname, sockaddr = \
            getaddrinfo(host, port, 0, SOCK_STREAM)[0]

        # Get a connection slot.
        with ConnectionSlot(host):

            # Start the timer.
            t1 = time()

            # Connect to the server.
            try:
                s = socket(family, socktype, sockproto)
                try:
                    s.settimeout(timeout)
                    s.connect(sockaddr)
                    try:
                        if proto == "https":
                            s = wrap_socket(s)

                        # Send the HTTP request.
                        s.sendall(raw_request.raw_request)

                        # Get the HTTP response headers.
                        raw_response = StringIO()
                        while True:
                            data = s.recv(1)
                            if not data:
                                raise NetworkException(
                                    "Server has closed the connection")
                            raw_response.write(data)
                            if raw_response.getvalue().endswith("\r\n\r\n"):
                                break   # full HTTP headers received
                            if len(raw_response.getvalue()) > 65536:
                                raise NetworkException(
                                    "Response headers too long")

                        # Stop the timer.
                        t2 = time()

                        # Call the user-defined callback,
                        # and cancel if requested.
                        if callback is not None:
                            temp_request  = HTTP_Raw_Request(
                                raw_request.raw_request)
                            temp_response = HTTP_Response(
                                temp_request,
                                raw_response = raw_response.getvalue()
                            )
                            discard_data(temp_request)
                            discard_data(temp_response)
                            cont = callback(temp_request, temp_response)
                            if not cont:
                                return
                            del temp_request
                            del temp_response

                        # Start the timer.
                        t3 = time()

                        # Download the contents.
                        #
                        #
                        #
                        # XXX TODO
                        #
                        #
                        #

                        # Stop the timer.
                        t4 = time()

                        # Return the HTTP_Response object.
                        return HTTP_Response(
                            request      = raw_request,
                            raw_response = raw_response.getvalue(),
                            elapsed      = (t2 - t1) + (t4 - t3),
                        )

                    # Close the connection and clean up the socket.
                    finally:
                        try:
                            s.shutdown(2)
                        except Exception:
                            pass
                finally:
                    try:
                        s.close()
                    except Exception:
                        pass

            # On socket errors, send an exception.
            except error, e:
                raise NetworkException(str(e))

        # Should never reach this point.
        raise Exception("INTERNAL ERROR")


#------------------------------------------------------------------------------

# Singleton pattern.
HTTP = _HTTP()
