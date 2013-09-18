#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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


# Fix the module path for the tests.
import sys
import os
from os import path
try:
    _FIXED_PATH_
except NameError:
    here = path.split(path.abspath(__file__))[0]
    if not here:  # if it fails use cwd instead
        here = path.abspath(os.getcwd())
    golismero = path.join(here, "..")
    thirdparty_libs = path.join(golismero, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        sys.path.insert(0, thirdparty_libs)
        sys.path.insert(0, golismero)
    _FIXED_PATH_ = True


# Imports.
from golismero.api.data.information.http import HTTP_Headers, HTTP_Request, HTTP_Response
from golismero.api.net.web_utils import ParsedURL
from golismero.main.testing import PluginTester


# Test cases for HTTP headers.
cases_http_headers = (

    # ---

    ("normal HTTP headers",

     ("Host: www.example.com\r\n"
      "Connection: keep-alive\r\n"
      "Content-Length: 0\r\n"
      "Content-Encoding: plain\r\n"
      "Transport-Encoding: plain\r\n"
      "Pragma: no-cache\r\n"
      "\r\n"),

     (("Host", "www.example.com"),
      ("Connection", "keep-alive"),
      ("Content-Length", "0"),
      ("Content-Encoding", "plain"),
      ("Transport-Encoding", "plain"),
      ("Pragma", "no-cache")),

     {"host": "www.example.com",
      "connection": "keep-alive",
      "content-length": "0",
      "content-encoding": "plain",
      "transport-encoding": "plain",
      "pragma": "no-cache"}
    ),

    # ---

    ("multiline HTTP headers",

     ("Host: www.example.com\r\n"
      "Set-Cookie: example=true,\r\n"
      "            multiline=true\r\n"
      "Location: http://www.example.com/index.php\r\n"
      "\r\n"),

     (("Host", "www.example.com"),
      ("Set-Cookie", "example=true, multiline=true"),
      ("Location", "http://www.example.com/index.php")),

     {"host": "www.example.com",
      "set-cookie": "example=true, multiline=true",
      "location": "http://www.example.com/index.php"}
    ),

    # ---

    ("duplicated HTTP headers",

     ("Host: www.example.com\r\n"
      "Set-Cookie: example=true\r\n"
      "Set-Cookie: duplicated=true\r\n"
      "Location: http://www.example.com/index.php\r\n"
      "\r\n"),

     (("Host", "www.example.com"),
      ("Set-Cookie", "example=true"),
      ("Set-Cookie", "duplicated=true"),
      ("Location", "http://www.example.com/index.php")),

     {"host": "www.example.com",
      "set-cookie": "example=true, duplicated=true",
      "location": "http://www.example.com/index.php"}
    ),

    # ---

    ("broken HTTP headers",

     ("Host: www.example.com\r\n"
      "Set-Cookie: example=true\r\n"
      "\r\n"
      "Location: http://www.example.com/index.php\r\n"
      "\r\n"),

     (("Host", "www.example.com"),
      ("Set-Cookie", "example=true")),

     {"host": "www.example.com",
      "set-cookie": "example=true"}
    ),

    # ---

    ("HTTP headers with extra whitespace",

     ("Host  \t  :   \t   www.example.com   \t   \r\n"
      "X-Whatever::::: ::::: some data goes here \r\n"
      "\t   and here too   \r\n"
      "Set-Cookie: example=true,   \t   \r\n"
      "     \t        multiline=true  \t  \r\n"
      "Set-Cookie:  \t   duplicated=true  \t \r\n"
      "Pragma: no-cache\r\n"
      "\r\n"),

     (("Host", "www.example.com"),
      ("X-Whatever", ":::: ::::: some data goes here and here too"),
      ("Set-Cookie", "example=true, multiline=true"),
      ("Set-Cookie", "duplicated=true"),
      ("Pragma", "no-cache")),

     {"host": "www.example.com",
      "x-whatever": ":::: ::::: some data goes here and here too",
      "set-cookie": "example=true, multiline=true, duplicated=true",
      "pragma": "no-cache"}
    ),

    # ---
)


# This tests the HTTP headers parser.
def test_http_headers():
    with PluginTester():

        # Test the methods.
        print "Testing HTTP_Header() methods..."
        raw_headers = (
            "Host: www.example.com\r\n"
            "Connection: keep-alive\r\n"
            "Content-Length: 0\r\n"
            "Content-Encoding: plain\r\n"
            "Transport-Encoding: plain\r\n"
            "Pragma: no-cache\r\n"
            "\r\n"
        )
        headers = HTTP_Headers(raw_headers)
        assert str(headers) == raw_headers
        assert headers["cOnNeCtIoN"] == "keep-alive"
        assert headers.get("FAKE", "fake") == "fake"
        assert headers.get("NotHere") == None
        try:
            print headers["lalalala"]
            assert False
        except KeyError:
            pass
        try:
            print headers.get(object())
            assert False
        except TypeError:
            pass
        try:
            print headers.get(object(), "lalala")
            assert False
        except TypeError:
            pass
        try:
            print headers[object()]
            assert False
        except TypeError:
            pass
        assert headers[0] == "Host: www.example.com\r\n"
        assert headers[3] == "Content-Encoding: plain\r\n"
        assert headers[-1] == "Pragma: no-cache\r\n"
        try:
            print headers[6]
            assert False
        except IndexError:
            pass
        try:
            print headers[-7]
            assert False
        except IndexError:
            pass
        assert headers[1:3] == "Connection: keep-alive\r\nContent-Length: 0\r\n"
        assert headers[-3:-1] == "Content-Encoding: plain\r\nTransport-Encoding: plain\r\n"
        assert headers[3:] == "Content-Encoding: plain\r\nTransport-Encoding: plain\r\nPragma: no-cache\r\n"
        assert headers[-2:] == "Transport-Encoding: plain\r\nPragma: no-cache\r\n"
        assert headers[-100:] == raw_headers[:-2]
        assert not headers[:-7]
        assert not headers[6:]
        assert headers[:100] == raw_headers[:-2]
        assert list(headers) == [
            "Host: www.example.com\r\n",
            "Connection: keep-alive\r\n",
            "Content-Length: 0\r\n",
            "Content-Encoding: plain\r\n",
            "Transport-Encoding: plain\r\n",
            "Pragma: no-cache\r\n",
        ]
        assert list(headers.iterkeys()) == [
            "Host",
            "Connection",
            "Content-Length",
            "Content-Encoding",
            "Transport-Encoding",
            "Pragma",
        ]
        assert list(headers.itervalues()) == [
            "www.example.com",
            "keep-alive",
            "0",
            "plain",
            "plain",
            "no-cache",
        ]
        assert list(headers.iteritems()) == [
            ("Host", "www.example.com"),
            ("Connection", "keep-alive"),
            ("Content-Length", "0"),
            ("Content-Encoding", "plain"),
            ("Transport-Encoding", "plain"),
            ("Pragma", "no-cache"),
        ]
        original = sorted(headers.to_tuple())
        orig_dict = dict(original)
        headers = HTTP_Headers.from_items(original)
        assert headers.to_tuple() == tuple(original)
        parsed = headers.to_dict()
        headers = HTTP_Headers.from_items(orig_dict.items())
        assert sorted(headers.to_tuple()) == original
        assert headers.to_dict() == parsed
        headers = HTTP_Headers.from_items(HTTP_Request.DEFAULT_HEADERS)
        assert headers.to_tuple() == HTTP_Request.DEFAULT_HEADERS
        parsed = headers.to_dict()
        headers = HTTP_Headers.from_items(sorted(parsed.items()))
        assert headers.to_dict() == parsed
        assert headers.to_tuple() == tuple(sorted(parsed.items()))

        # Run parser test cases.
        for title, raw_headers, original, parsed in cases_http_headers:
            print "Testing parser with %s..." % title
            headers = HTTP_Headers(raw_headers)
            assert str(headers) == raw_headers
            assert headers.to_tuple() == original
            assert headers.to_dict() == parsed
            headers = HTTP_Headers.from_items(original)
            assert headers.to_tuple() == original
            assert headers.to_dict() == parsed
            headers = HTTP_Headers.from_items(parsed.items())
            assert headers.to_dict() == parsed


# This tests the HTTP request parser.
def test_http_request():
    with PluginTester():

        print "Testing a simple GET request..."
        request = HTTP_Request("http://www.example.com/index.html")
        assert request.method == "GET"
        assert request.url == "http://www.example.com/index.html"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.1"
        assert isinstance(request.headers, HTTP_Headers)
        assert request.post_data == None
        assert request.request_uri == "/index.html"
        assert request.hostname == "www.example.com"
        assert request.user_agent == "Mozilla/5.0 (compatible, GoLismero/2.0 The Web Knife; +https://github.com/golismero/golismero)"
        assert request.accept_language == "en-US"
        assert request.accept == "*/*"
        assert request.referer == None
        assert request.cookie == None
        assert request.content_type == None
        assert request.content_length == None

        print "Testing a simple POST request..."
        request = HTTP_Request("http://www.example.com/form.php", post_data="hola=manola")
        assert request.method == "POST"
        assert request.url == "http://www.example.com/form.php"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.1"
        assert isinstance(request.headers, HTTP_Headers)
        assert request.post_data == "hola=manola"
        assert request.request_uri == "/form.php"
        assert request.hostname == "www.example.com"
        assert request.user_agent == "Mozilla/5.0 (compatible, GoLismero/2.0 The Web Knife; +https://github.com/golismero/golismero)"
        assert request.accept_language == "en-US"
        assert request.accept == "*/*"
        assert request.referer == None
        assert request.cookie == None
        assert request.content_type == "application/x-www-form-urlencoded"
        assert request.content_length == len("hola=manola")

        print "Testing a custom GET request (1)..."
        t_headers = (("Cookie", "lala=pepe"), ("Referer", "http://www.example.com/"))
        request = HTTP_Request("http://www.example.com/index.html", headers=t_headers, version="1.0")
        assert request.method == "GET"
        assert request.url == "http://www.example.com/index.html"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.0"
        assert request.headers.to_tuple() == t_headers
        assert request.post_data == None
        assert request.request_uri == "/index.html"
        assert request.hostname == None
        assert request.user_agent == None
        assert request.accept_language == None
        assert request.accept == None
        assert request.referer == "http://www.example.com/"
        assert request.cookie == "lala=pepe"
        assert request.content_type == None
        assert request.content_length == None

        print "Testing a custom GET request (2)..."
        d_headers = {"Cookie": "lala=pepe", "Referer": "http://www.example.com/"}
        request = HTTP_Request("http://www.example.com/index.html", headers=d_headers, version="1.0")
        assert request.method == "GET"
        assert request.url == "http://www.example.com/index.html"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.0"
        assert request.headers.to_tuple() == tuple(sorted(d_headers.items()))
        assert request.post_data == None
        assert request.request_uri == "/index.html"
        assert request.hostname == None
        assert request.user_agent == None
        assert request.accept_language == None
        assert request.accept == None
        assert request.referer == "http://www.example.com/"
        assert request.cookie == "lala=pepe"
        assert request.content_type == None
        assert request.content_length == None

        print "Testing a custom GET request (3)..."
        o_headers = HTTP_Headers.from_items(t_headers)
        request = HTTP_Request("http://www.example.com/form.php?hola=manola", headers=o_headers, version="1.0")
        assert request.method == "GET"
        assert request.url == "http://www.example.com/form.php?hola=manola"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.0"
        assert request.headers is o_headers
        assert request.post_data == None
        assert request.request_uri == "/form.php?hola=manola"
        assert request.hostname == None
        assert request.user_agent == None
        assert request.accept_language == None
        assert request.accept == None
        assert request.referer == "http://www.example.com/"
        assert request.cookie == "lala=pepe"
        assert request.content_type == None
        assert request.content_length == None

        print "Testing a custom POST request..."
        request = HTTP_Request("http://www.example.com/form.php", post_data="hola=manola", headers=t_headers, version="1.0")
        assert request.method == "POST"
        assert request.url == "http://www.example.com/form.php"
        assert isinstance(request.parsed_url, ParsedURL)
        assert request.protocol == "HTTP"
        assert request.version == "1.0"
        assert request.headers.to_tuple() == t_headers
        assert request.post_data == "hola=manola"
        assert request.request_uri == "/form.php"
        assert request.hostname == None
        assert request.user_agent == None
        assert request.accept_language == None
        assert request.accept == None
        assert request.referer == "http://www.example.com/"
        assert request.cookie == "lala=pepe"
        assert request.content_type == None
        assert request.content_length == None


# Test cases for HTTP responses.
cases_http_response = (

    # ---

    ("full HTTP 1.1 response",
     {
      "status":   "200",
      "reason":   "OK",
      "protocol": "HTTP",
      "version":  "1.1",
      "data":     "hola manola",
      "raw_response": (
          "HTTP/1.1 200 OK\r\n"
          "Server: lalalala\r\n"
          "Content-Length: 11\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
          "hola manola"
      ),
      "raw_headers": (
          "Server: lalalala\r\n"
          "Content-Length: 11\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
     }
    ),

    # ---

    ("HTTP 1.1 response with no data",
     {
      "status":   "500",
      "reason":   "Bad Request",
      "protocol": "HTTP",
      "version":  "1.1",
      "data":     None,
      "raw_response": (
          "HTTP/1.1 500 Bad Request\r\n"
          "Server: lalalala\r\n"
          "Content-Length: 0\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
      "raw_headers": (
          "Server: lalalala\r\n"
          "Content-Length: 0\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
     }
    ),

    # ---

    ("full HTTP 1.0 response",
     {
      "status":   "200",
      "reason":   "OK",
      "protocol": "HTTP",
      "version":  "1.0",
      "data":     "hola manola",
      "raw_response": (
          "HTTP/1.0 200 OK\r\n"
          "Server: lalalala\r\n"
          "Content-Length: 11\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
          "hola manola"
      ),
      "raw_headers": (
          "Server: lalalala\r\n"
          "Content-Length: 11\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
     }
    ),

    # ---

    ("HTTP 1.0 response with no data",
     {
      "status":   "500",
      "reason":   "Bad Request",
      "protocol": "HTTP",
      "version":  "1.0",
      "data":     None,
      "raw_response": (
          "HTTP/1.0 500 Bad Request\r\n"
          "Server: lalalala\r\n"
          "Content-Length: 0\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
      "raw_headers": (
          "Server: lalalala\r\n"
          "Content-Length: 0\r\n"
          "Set-Cookie: pepe=momo\r\n"
          "\r\n"
      ),
     }
    ),

    # ---

    ("HTTP 1.0 response with no headers nor data",
     {
      "status":   "404",
      "reason":   "Not Found",
      "protocol": "HTTP",
      "version":  "1.0",
      "data":     None,
      "raw_response": (
          "HTTP/1.0 404 Not Found\r\n"
          "\r\n"
      ),
      "raw_headers": "\r\n",
     }
    ),

    # ---

    ("broken HTTP 1.0 response with only version and status code",
     {
      "status":   "404",
      "reason":   "Not Found",
      "protocol": "HTTP",
      "version":  "1.0",
      "data":     None,
      "raw_response": (
          "HTTP/1.0 404\r\n"
          "\r\n"
      ),
      "raw_headers": "\r\n",
     }
    ),

    # ---

)


# This tests the HTTP response parser.
def test_http_response():
    with PluginTester():

        # Run test cases.
        for title, kwargs in cases_http_response:
            print "Testing %s..." % title
            request = HTTP_Request("http://www.example.com/index.html")
            kw_1 = kwargs.copy()
            kw_2 = {"raw_response": kw_1.pop("raw_response")}
            kw_3 = kw_1.copy()
            kw_3["headers"] = HTTP_Headers(kw_3.pop("raw_headers"))
            for kw in (kw_1, kw_2, kw_3):
                response = HTTP_Response(request, **kw)
                assert response.identity in request.links
                assert request.identity in response.links
                assert str(response.headers) == kwargs["raw_headers"]
                for key, value in kwargs.iteritems():
                    if key == "raw_response" and "broken" in title:
                        continue
                    try:
                        assert getattr(response, key) == value
                    except AssertionError:
                        print "  key == %r" % key
                        print "  value == %r" % value
                        print "  getattr(response, key) == %r" % getattr(response, key)
                        raise

        # Test HTTP 0.9.
        print "Testing HTTP 0.9 response..."
        request  = HTTP_Request("http://www.example.com/index.html", version="0.9")
        response = HTTP_Response(request, data="hola manola")
        assert response.raw_response == "hola manola"
        assert response.raw_headers  == None
        assert response.headers      == None
        assert response.status       == "200"
        assert response.reason       == "OK"
        assert response.protocol     == "HTTP"
        assert response.version      == "0.9"


# Run all tests from the command line.
if __name__ == "__main__":
    test_http_headers()
    test_http_request()
    test_http_response()
