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


# Imports
from golismero.api.net.web_utils import ParsedURL, parse_url
from warnings import catch_warnings



# The most rudimentary test cases. If these fail, there's no point in continuing.
basic = (

    # Vainilla URLs for each supported schema.
    'http://example.com/',
    'https://example.com/',
    'ftp://asmith@ftp.example.org/',

    # Full URL, query string can be parsed.
    'http://username:password@example.com:1234/path?query=string#fragment_id',

    # Full URL, query string cannot be parsed.
    'http://username:password@example.com:1234/path?query_string#fragment_id',

    # Sorted query string parameters (when parseable).
    'http://example.com/path?a=1&b=2&c=3',

    # Using / as a query string separator.
    'http://example.com/very/long/path/query=string',
    'http://example.com/shorter/path/query=string',
    'http://example.com/path/query=string',
    'http://example.com/query=string',

    # IPv4 hosts.
    'http://192.168.1.1/',
    'http://192.168.1.1/index.html',

    # IPv6 hosts.
    # https://www.ietf.org/rfc/rfc2732.txt
    'http://[FEDC:BA98:7654:3210:FEDC:BA98:7654:3210]:81/index.html',
    'http://[1080:0:0:0:8:800:200C:417A]/index.html',
    'http://[3FFE:2A00:100:7031::1]/',
    'http://[1080::8:800:200C:417A]/foo',
    'http://[::192.9.5.5]/ipng',
    'http://[::FFFF:129.144.52.38]:81/index.html',
    'http://[2010:836B:4179::836B:4179]/',

)

def test_basic_urls():
    print "Testing basic URL parsing..."
    for url in basic:
        ##pprint(parse_url(url).url)
        assert parse_url(url).url == url


# Simple test cases.
simple = (

    # Full http url.
    {
        'url'              : 'http://user:pass@www.site.com/folder/index.php?param=value#anchor',
        'request_uri'      : '/folder/index.php?param=value',
        'scheme'           : 'http',
        'host'             : 'www.site.com',
        'port'             : 80,
        'username'         : 'user',
        'password'         : 'pass',
        'auth'             : 'user:pass',
        'netloc'           : 'user:pass@www.site.com',
        'subdomain'        : 'www',
        'domain'           : 'site',
        'tld'              : 'com',
        'path'             : '/folder/index.php',
        'directory'        : '/folder',
        'filename'         : 'index.php',
        'filebase'         : 'index',
        'minimal_filebase' : 'index',
        'extension'        : '.php',
        'all_extensions'   : '.php',
        'query'            : 'param=value',
        'query_char'       : '?',
        'query_params'     : { 'param' : 'value' },
        'fragment'         : 'anchor',
    },

    # Simple http url with double extension.
    {
        'url'              : 'http://www.google.com@www.example.com:8080/malware.pdf.exe',
        'request_uri'      : '/malware.pdf.exe',
        'scheme'           : 'http',
        'host'             : 'www.example.com',
        'port'             : 8080,
        'username'         : 'www.google.com',
        'password'         : '',
        'auth'             : 'www.google.com',
        'netloc'           : 'www.google.com@www.example.com:8080',
        'subdomain'        : 'www',
        'domain'           : 'example',
        'tld'              : 'com',
        'path'             : '/malware.pdf.exe',
        'directory'        : '/',
        'filename'         : 'malware.pdf.exe',
        'filebase'         : 'malware.pdf',
        'minimal_filebase' : 'malware',
        'extension'        : '.exe',
        'all_extensions'   : '.pdf.exe',
        'query'            : '',
        'query_char'       : '?',
        'query_params'     : {},
        'fragment'         : '',
    },

    # Simple https url.
    {
        'url'              : 'https://www.example.com/',
        'request_uri'      : '/',
        'scheme'           : 'https',
        'host'             : 'www.example.com',
        'port'             : 443,
        'username'         : '',
        'password'         : '',
        'auth'             : '',
        'netloc'           : 'www.example.com',
        'subdomain'        : 'www',
        'domain'           : 'example',
        'tld'              : 'com',
        'path'             : '/',
        'directory'        : '/',
        'filename'         : '',
        'filebase'         : '',
        'minimal_filebase' : '',
        'extension'        : '',
        'all_extensions'   : '',
        'query'            : '',
        'query_char'       : '?',
        'query_params'     : {},
        'fragment'         : '',
    },

    # Simple ftp url.
    {
        'url'              : 'ftp://ftp.example.com/file.txt',
        'request_uri'      : '/file.txt',
        'scheme'           : 'ftp',
        'host'             : 'ftp.example.com',
        'port'             : 21,
        'username'         : '',
        'password'         : '',
        'auth'             : '',
        'netloc'           : 'ftp.example.com',
        'subdomain'        : 'ftp',
        'domain'           : 'example',
        'tld'              : 'com',
        'path'             : '/file.txt',
        'directory'        : '/',
        'filename'         : 'file.txt',
        'filebase'         : 'file',
        'minimal_filebase' : 'file',
        'extension'        : '.txt',
        'all_extensions'   : '.txt',
        'query'            : '',
        'query_char'       : '?',
        'query_params'     : {},
        'fragment'         : '',
    },

    # Simple mailto url.
    {
        'url'              : 'mailto://user@example.com?subject=Hi%21',
        'request_uri'      : '?subject=Hi%21',
        'scheme'           : 'mailto',
        'host'             : 'example.com',
        'port'             : 25,
        'username'         : 'user',
        'password'         : '',
        'auth'             : 'user',
        'netloc'           : 'user@example.com',
        'subdomain'        : '',
        'domain'           : 'example',
        'tld'              : 'com',
        'path'             : '',
        'directory'        : '',
        'filename'         : '',
        'filebase'         : '',
        'minimal_filebase' : '',
        'extension'        : '',
        'all_extensions'   : '',
        'query'            : 'subject=Hi%21',
        'query_char'       : '?',
        'query_params'     : { 'subject' : 'Hi!' },
        'fragment'         : '',
    },

    # Localhost url.
    {
        'url'              : 'http://localhost:1234/#fragment',
        'request_uri'      : '/',
        'scheme'           : 'http',
        'host'             : 'localhost',
        'port'             : 1234,
        'username'         : '',
        'password'         : '',
        'auth'             : '',
        'netloc'           : 'localhost:1234',
        'subdomain'        : '',
        'domain'           : 'localhost',
        'tld'              : '',
        'path'             : '/',
        'directory'        : '/',
        'filename'         : '',
        'filebase'         : '',
        'minimal_filebase' : '',
        'extension'        : '',
        'all_extensions'   : '',
        'query'            : '',
        'query_char'       : '?',
        'query_params'     : {},
        'fragment'         : 'fragment',
    },
)


# Test of the URL parser.
def test_url_parser():
    print "Testing URL parsing for all properties..."
    for case in simple:
        url = case['url']
        d = ParsedURL(url)
        for key, value in case.iteritems():
            try:
                assert getattr(d, key) == value
            except AssertionError:
                print "-" * 79
                print "Failed test case: %r" % url
                print "Attribute name: %r" % key
                print "Expected value: %r" % value
                print "Got instead:    %r" % getattr(d, key)
                print "-" * 79
                raise


# Test cases for URL canonicalization.
equivalent = (

    # Case insensitive scheme and hostname, automatically add the trailing slash.
    (
        'http://example.com',
        'http://example.com/',
        'HTTP://EXAMPLE.COM',
        'HTTP://EXAMPLE.COM/',
    ),

    # Default port number.
    (
        'http://example.com',
        'http://example.com:80',
        'http://example.com/', # sanitized
        'http://example.com:80/',
    ),
    (
        'https://example.com',
        'https://example.com:443',
        'https://example.com/', # sanitized
        'https://example.com:443/',
    ),
    (
        'ftp://example.com',
        'ftp://example.com:21',
        'ftp://example.com/', # sanitized
        'ftp://example.com:21/',
    ),

    # Sorting of query parameters, handling of missing values.
    (
        'http://example.com/path?query=string&param=value&orphan',
        'http://example.com/path?query=string&param=value&orphan=',
        'http://example.com/path?orphan&query=string&param=value',
        'http://example.com/path?orphan=&query=string&param=value',
        'http://example.com/path?orphan=&param=value&query=string', # sanitized
    ),
    (
        'http://example.com/path?query=string&param=value&orphan#fragment_id',
        'http://example.com/path?query=string&param=value&orphan=#fragment_id',
        'http://example.com/path?orphan&query=string&param=value#fragment_id',
        'http://example.com/path?orphan=&query=string&param=value#fragment_id',
        'http://example.com/path?orphan=&param=value&query=string#fragment_id', # sanitized
    ),

    # Sanitization of pathological cases.
    (
        "http://user:name:password@example.com",    # broken
        "http://user:name%3Apassword@example.com/", # sanitized
    ),
    (
        "http://lala@pepe@example.com",    # broken
        "http://lala@pepe%40example.com/", # sanitized
    ),
    (
        "http://example.com/path%2Ffile", # broken
        "http://example.com/path/file",   # sanitized
    ),
    (
        "http://example%2Ecom/", # broken
        "http://example.com/",   # sanitized
    ),
    (
        "h%74%74p://example.com/", # broken
        "http://example.com/",     # sanitized
    ),
    (
        "http://example.com/file name with spaces", # broken
        "http://example.com/file+name+with+spaces", # sanitized
    ),

)

def test_equivalent_urls():
    print "Testing URL sanitization..."
    for url_list in equivalent:
        normalized = set()
        for url in url_list:
            normalized.add(parse_url(url).url)
        ##pprint(normalized)
        assert len(normalized) == 1
        normal = normalized.pop()
        ##print
        ##print normal, url_list
        assert normal in url_list


# Test cases for relative URLs.

# Relative URLs, base: http://example.com/path/
relative = (
    ('/robots.txt', 'http://example.com/robots.txt'),
    ('index.php?query=string', 'http://example.com/path/index.php?query=string'),
    ('#fragment', 'http://example.com/path/#fragment'),
)

def test_relative_urls():
    print "Testing relative URL parsing..."
    for rel, ab in relative:
        ##print rel
        ##print parse_url(relative, 'http://example.com/path/').url
        ##print ab
        assert parse_url(rel, 'http://example.com/path/').url == ab


# Test cases for URL parsing errors.
errors = (

    # Unsupported scheme.
    "bogus://example.com",
    "data:11223344",
    "javascript:alert('xss')",
    "file://C:/Windows/System32/calc.exe",

    # Broken scheme.
    "http:/example.com",
    "http:example.com",
)

def test_url_errors():
    print "Testing URL parsing errors..."
    for url in errors:
        try:
            parse_url(url).url
            raise AssertionError(url)
        except ValueError:
            pass


# Some manual testing.
def test_url_parser_custom():
    print "Testing URL modification and reparsing..."

    # Relative URLs.
    assert ParsedURL("/index.html", base_url="http://www.example.com").url == "http://www.example.com/index.html"
    assert ParsedURL("index.html", base_url="http://www.example.com/folder/").url == "http://www.example.com/folder/index.html"
    assert ParsedURL("index.html", base_url="http://www.example.com/folder").url == "http://www.example.com/index.html"

    # Setters.
    d = ParsedURL("http://www.example.com")
    assert d.path == "/"
    d.path = "/index.html"
    assert d.url == "http://www.example.com/index.html"
    assert d.path == "/index.html"
    assert d.port == 80
    d.scheme = "https"
    assert d.url == "https://www.example.com/index.html"
    assert d.port == 443
    d.port = 8080
    assert d.port == 8080
    assert d.url == "https://www.example.com:8080/index.html"
    d.scheme = "http://"
    assert d.port == 8080
    assert d.url == "http://www.example.com:8080/index.html"
    d.port = None
    assert d.port == 80
    assert d.url == "http://www.example.com/index.html"
    d.path = "index.html"
    assert d.path == "/index.html"
    assert d.url == "http://www.example.com/index.html"
    d.host = "www.site.com"
    assert d.url == "http://www.site.com/index.html"
    d.netloc = "user:pass@www.site.com"
    assert d.url == "http://user:pass@www.site.com/index.html"
    assert d.username == "user"
    assert d.password == "pass"
    d.username = "someone"
    assert d.url == "http://someone:pass@www.site.com/index.html"
    assert d.netloc == "someone:pass@www.site.com"
    d.password = "secret"
    assert d.url == "http://someone:secret@www.site.com/index.html"
    assert d.netloc == "someone:secret@www.site.com"
    assert d.auth == "someone:secret"
    d.password = None
    assert d.url == "http://someone@www.site.com/index.html"
    assert d.netloc == "someone@www.site.com"
    assert d.auth == "someone"
    d.password = "secret"
    assert d.url == "http://someone:secret@www.site.com/index.html"
    assert d.netloc == "someone:secret@www.site.com"
    assert d.auth == "someone:secret"
    d.username = None
    assert d.url == "http://:secret@www.site.com/index.html"
    assert d.netloc == ":secret@www.site.com"
    assert d.auth == ":secret"
    d.auth = "test:key"
    assert d.url == "http://test:key@www.site.com/index.html"
    assert d.netloc == "test:key@www.site.com"
    assert d.username == "test"
    assert d.password == "key"
    d.auth = None
    assert d.url == "http://www.site.com/index.html"
    assert d.netloc == "www.site.com"
    assert d.username == ""
    assert d.password == ""
    d.fragment = "fragment"
    assert d.url == "http://www.site.com/index.html#fragment"
    assert d.fragment == "fragment"
    d.fragment = None
    assert d.url == "http://www.site.com/index.html"
    assert d.fragment == ""
    d.query = "key=value&param=data"
    assert d.url == "http://www.site.com/index.html?key=value&param=data"
    assert d.query_char == "?"
    assert d.query == "key=value&param=data"
    assert d.query_params == { "key": "value", "param": "data" }
    d.query_params["test"] = "me"
    assert d.url == "http://www.site.com/index.html?key=value&param=data&test=me"
    assert d.query == "key=value&param=data&test=me"
    assert d.query_params == { "key": "value", "param": "data", "test": "me" }
    d.query_params = { "some": "thing" }
    assert d.url == "http://www.site.com/index.html?some=thing"
    assert d.query == "some=thing"
    assert d.query_params == { "some": "thing" }
    d.query = "a=b&c"
    assert d.url == "http://www.site.com/index.html?a=b&c="
    assert d.query == "a=b&c="
    assert d.query_params == { "a": "b", "c": "" }
    d.query = "teststring".encode("rot13")
    assert d.url == "http://www.site.com/index.html?" + "teststring".encode("rot13")
    assert d.query == "teststring".encode("rot13")
    assert d.query_params == {}
    d.query = "test string".encode("base64")[:-1]
    assert d.url == "http://www.site.com/index.html?" + "test string".encode("base64")[:-1]
    assert d.query == "test string".encode("base64")[:-1]
    assert d.query_params == {}
    d.query = "test string".encode("base64")
    assert d.url == "http://www.site.com/index.html?" + "test string".encode("base64")[:-1] + "%0A"
    assert d.query == "test string".encode("base64")[:-1] + "%0A"
    assert d.query_params == {"test string".encode("base64")[:-2]: "\n"}
    d.query = "test=me"
    d.query_char = "/"
    assert d.url == "http://www.site.com/index.html/test=me"
    assert d.query_char == "/"
    assert d.query == "test=me"
    assert d.query_params == { "test": "me" }
    d.fragment = "frag"
    assert d.url == "http://www.site.com/index.html/test=me#frag"

    # Methods.
    d.hostname = "this.is.a.subdomain.of.example.co.uk"
    assert ".".join(d.split_hostname()) == d.host
    assert d.split_hostname() == ("this.is.a.subdomain.of", "example", "co.uk")
    d.path = "/folder.with.extensions/file.pdf.exe"
    assert d.get_all_extensions(directory_allowed = False, double_allowed = True)  == [".pdf", ".exe"]
    assert d.get_all_extensions(directory_allowed = True,  double_allowed = True)  == [".with", ".extensions", ".pdf", ".exe"]
    assert d.get_all_extensions(directory_allowed = False, double_allowed = False) == [".exe"]
    assert d.get_all_extensions(directory_allowed = True,  double_allowed = False) == [".extensions", ".exe"]
    assert d.get_all_extensions(directory_allowed = False                        ) == [".pdf", ".exe"]
    assert d.get_all_extensions(                           double_allowed = False) == [".extensions", ".exe"]
    assert d.get_all_extensions(                                                 ) == [".with", ".extensions", ".pdf", ".exe"]

    # Exceptions.
    last_url = d.url
    try:
        d.query_char = "*"
        assert False
    except ValueError:
        pass
    try:
        d.scheme = "fake://"
        assert False
    except ValueError:
        pass
    try:
        d.port = "fake"
        assert False
    except ValueError:
        pass
    try:
        d.port = -1
        assert False
    except ValueError:
        pass
    try:
        d.port = 80000
        assert False
    except ValueError:
        pass
    assert d.url == last_url

    # Warnings.
    with catch_warnings(record=True) as w:
        d.fragment = "#test"
        d.query = "?test=me"
    assert len(w) == 2


# Run all tests from the command line.
if __name__ == "__main__":
    test_basic_urls()
    test_equivalent_urls()
    test_relative_urls()
    test_url_errors()
    test_url_parser()
    test_url_parser_custom()
