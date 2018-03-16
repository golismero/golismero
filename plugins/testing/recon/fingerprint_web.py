#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from golismero.api.config import Config
from golismero.api.data import discard_data
from golismero.api.data.information.http import HTTP_Raw_Request
from golismero.api.data.information.fingerprint import WebServerFingerprint
from golismero.api.data.resource.url import BaseURL
from golismero.api.logger import Logger
from golismero.api.net import NetworkException
from golismero.api.net.http import HTTP
from golismero.api.net.web_utils import ParsedURL, urljoin
from golismero.api.plugin import TestingPlugin
from golismero.api.text.wordlist import WordListLoader

from collections import Counter, OrderedDict, defaultdict
from re import compile


SERVER_PATTERN = compile(r"([\w\W\s\d]+)[\s\/]+([\d\w\.]+)")


__doc__ = """

Fingerprint techniques are based on the fantastic paper of httprecon project, and their databases:

- Doc: http://www.computec.ch/projekte/httprecon/?s=documentation
- Project page: http://www.computec.ch/projekte/httprecon


This plugin try to a fingerprinting over web servers.

Step 1
------

Define the methods used:

1 Check the Banner.
2 Check the order headers in HTTP response.
3 Check the rest of headers.


Step 2
------

Then assigns a weight to each method:

1. -> 50%
2. -> 20%
3. -> 30% (divided by the number of test for each header)


Step 3
------

We have 9 request with:

1. GET / HTTP/1.1
2. GET /index.php HTTP/1.1
3. GET /404_file.html HTTP/1.1
4. HEAD / HTTP/1.1
5. OPTIONS / HTTP/1.1
6. DELETE / HTTP/1.1
7. TEST / HTTP/1.1
8. GET / 9.8
9. GET /<SCRIPT>alert</script> HTTP/1.1 -> Any web attack.

Step 4
------

For each type of response analyze the HTTP headers trying to find matches and
multiply for their weight.

Step 5
------

Sum de values obtained in step 4, for each test in step 3.

Step 6
------

Get the 3 highter values os matching.


For example
-----------

For an Apache 1.3.26 we will have these results for a normal GET:

- Banner (any of these options):

 + Apache/1.3.26 (Linux/SuSE) mod_ssl/2.8.10 OpenSSL/0.9.6g PHP/4.2.2
 + Apache/1.3.26 (UnitedLinux) mod_python/2.7.8 Python/2.2.1 PHP/4.2.2 mod_perl/1.27
 + Apache/1.3.26 (Unix)
 + Apache/1.3.26 (Unix) Debian GNU/Linux mod_ssl/2.8.9 OpenSSL/0.9.6g PHP/4.1.2 mod_webapp/1.2.0-dev
 + Apache/1.3.26 (Unix) Debian GNU/Linux PHP/4.1.2
 + Apache/1.3.26 (Unix) mod_gzip/1.3.19.1a PHP/4.3.11 mod_ssl/2.8.9 OpenSSL/0.9.6
 + MIT Web Server Apache/1.3.26 Mark/1.5 (Unix) mod_ssl/2.8.9 OpenSSL/0.9.7c

- A specific order for the rest of HTTP headers (any of these options):

 + Date,Server,Accept-Ranges,Content-Type,Content-Length,Via
 + Date,Server,Connection,Content-Type
 + Date,Server,Keep-Alive,Connection,Transfer-Encoding,Content-Type
 + Date,Server,Last-Modified,ETag,Accept-Ranges,Content-Length,Connection,Content-Type
 + Date,Server,Last-Modified,ETag,Accept-Ranges,Content-Length,Keep-Alive,Connection,Content-Type
 + Date,Server,Set-Cookie,Content-Type,Set-Cookie,Keep-Alive,Connection,Transfer-Encoding
 + Date,Server,X-Powered-By,Keep-Alive,Connection,Transfer-Encoding,Content-Type
 + Date,Server,X-Powered-By,Set-Cookie,Expires,Cache-Control,Pragma,Set-Cookie,Set-Cookie,Keep-Alive,Connection,Transfer-Encoding,Content-Type
 + Date,Server,X-Powered-By,Set-Cookie,Set-Cookie,Expires,Last-Modified,Cache-Control,Pragma,Keep-Alive,Connection,Transfer-Encoding,Content-Type

- The value of the rest of headers must be:

 * Content-Type (any of these options):

  + text/html
  + text/html; charset=iso-8859-1
  + text/html;charset=ISO-8859-1

 * Cache-Control (any of these options):

  + no-store, no-cache, must-revalidate, post-check=0, pre-check=0
  + post-check=0, pre-check=0

 * Connection (any of these options):

  + close
  + Keep-Alive

 * Quotes types must be double for ETag field:

  + ETag: "0", instead of ETag: '0'

 * E-Tag length (any of these options):

  + 0
  + 20
  + 21
  + 23

 * Pragma (any of these options):

  + no-cache

 * Format of headers. After a bash, the letter is uncapitalized, for http headers. For example:

  + Content-type, instead of Content-\*\*T\*\*ype.

 * Has spaces between names and values. For example:

  + E-Tag:0; instead of: E-Tag:0

 * Protocol name used in request is 'HTTP'. For example:

  + GET / HTTP/1.1

 * The status text for a response of HTTP.

   GET / HTTP/1.1
   Host: misite.com

   HTTP/1.1 200 \*\*OK\*\*
   \.\.\.\.

 * X-Powered-By (any of these options):

  + PHP/4.1.2
  + PHP/4.2.2
  + PHP/4.3.11
"""


#------------------------------------------------------------------------------
class ServerFingerprinting(TestingPlugin):
    """
    Plugin to fingerprint web servers.
    """


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [BaseURL]


    #--------------------------------------------------------------------------
    def run(self, info):
        """
        Main function for server fingerprint. Get an URL and return the fingerprint results.

        :param info: Base URL.
        :type info: BaseURL

        :return: Fingerprint.
        :rtype: WebServerFingerprint
        """
        m_main_url = info.url

        Logger.log_more_verbose("Starting webserver fingerprinting plugin for site: %s" % m_main_url)

        #
        # Analyze HTTP protocol
        #
        m_server_name, \
        m_server_version, \
        m_canonical_name, \
        m_webserver_complete_desc, \
        m_related_webservers, \
        m_others                       = http_simple_analyzer(m_main_url, self.update_status, 5) # http_analyzers(m_main_url, self.update_status, 100)

        Logger.log_more_verbose("Fingerprint - Server: %s | Version: %s" % (m_server_name, m_server_version))

        m_return = WebServerFingerprint(m_server_name, m_server_version, m_webserver_complete_desc, m_canonical_name, m_related_webservers, m_others)

        # Associate resource
        m_return.add_resource(info)

        # Return the fingerprint
        return m_return


#------------------------------------------------------------------------------
#
# Web server detection
#
#------------------------------------------------------------------------------
def http_simple_analyzer(main_url, update_status_func, number_of_entries=4):
    """Simple method to get fingerprint server info

    :param main_url: Base url to test.
    :type main_url: str

    :param update_status_func: function used to update the status of the process
    :type update_status_func: function

    :param number_of_entries: number of resutls tu return for most probable web servers detected.
    :type number_of_entries: int

    :return: a typle as format: Web server family, Web server version, Web server complete description, related web servers (as a dict('SERVER_RELATED' : set(RELATED_NAMES))), others web server with their probabilities as a dict(CONCRETE_WEB_SERVER, PROBABILITY)
    """

    m_actions = {
        'GET'        : { 'wordlist' : 'Wordlist_get'            , 'weight' : 1 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/' },
        'LONG_GET'   : { 'wordlist' : 'Wordlist_get_long'       , 'weight' : 1 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/%s' % ('a' * 200) },
        'NOT_FOUND'  : { 'wordlist' : 'Wordlist_get_notfound'   , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/404_NOFOUND__X02KAS' },
        'HEAD'       : { 'wordlist' : 'Wordlist_head'           , 'weight' : 3 , 'protocol' : 'HTTP/1.1', 'method' : 'HEAD'     , 'payload': '/' },
        'OPTIONS'    : { 'wordlist' : 'Wordlist_options'        , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'OPTIONS'  , 'payload': '/' },
        'DELETE'     : { 'wordlist' : 'Wordlist_delete'         , 'weight' : 5 , 'protocol' : 'HTTP/1.1', 'method' : 'DELETE'   , 'payload': '/' },
        'TEST'       : { 'wordlist' : 'Wordlist_attack'         , 'weight' : 5 , 'protocol' : 'HTTP/1.1', 'method' : 'TEST'     , 'payload': '/' },
        'INVALID'    : { 'wordlist' : 'Wordlist_wrong_method'   , 'weight' : 5 , 'protocol' : 'HTTP/9.8', 'method' : 'GET'      , 'payload': '/' },
        'ATTACK'     : { 'wordlist' : 'Wordlist_wrong_version'  , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': "/etc/passwd?format=%%%%&xss=\x22><script>alert('xss');</script>&traversal=../../&sql='%20OR%201;"}
    }

    m_d                   = ParsedURL(main_url)
    m_hostname            = m_d.hostname
    m_port                = m_d.port
    m_scheme              = m_d.scheme
    m_debug               = False # Only for develop
    i                     = 0
    m_counters            = HTTPAnalyzer()
    m_data_len            = len(m_actions) # Var used to update the status
    m_banners_counter     = Counter()

    for l_action, v in m_actions.iteritems():
        if m_debug:
            print "###########"
        l_method      = v["method"]
        l_payload     = v["payload"]
        l_proto       = v["protocol"]
        #l_wordlist    = v["wordlist"]

        # Each type of probe hast different weight.
        #
        # Weights go from 0 - 5
        #
        l_weight      = v["weight"]

        # Make the raw request
        l_raw_request = "%(method)s %(payload)s %(protocol)s\r\nHost: %(host)s\r\n\r\n" % (
            {
                "method"     : l_method,
                "payload"    : l_payload,
                "protocol"   : l_proto,
                "host"       : m_hostname,
                "port"       : m_port
            }
        )
        if m_debug:
            print "REQUEST"
            print l_raw_request

        # Do the connection
        l_response = None
        try:
            m_raw_request = HTTP_Raw_Request(l_raw_request)
            discard_data(m_raw_request)
            l_response = HTTP.make_raw_request(
                host        = m_hostname,
                port        = m_port,
                proto       = m_scheme,
                raw_request = m_raw_request,
                callback    = check_raw_response)
            if l_response:
                discard_data(l_response)
        except NetworkException,e:
            Logger.log_error_more_verbose("Server-Fingerprint plugin: No response for host '%s:%d' with method '%s'. Message: %s" % (m_hostname, m_port, l_method, str(e)))
            continue

        if not l_response:
            Logger.log_error_more_verbose("No response for host '%s:%d' with method '%s'." % (m_hostname, m_port, l_method))
            continue

        if m_debug:
            print "RESPONSE"
            print l_response.raw_headers


        # Update the status
        update_status_func((float(i) * 100.0) / float(m_data_len))
        Logger.log_more_verbose("Making '%s' test." % l_method)
        i += 1

        # Analyze for each wordlist
        #
        # Store the server banner
        try:
            m_banners_counter[l_response.headers["Server"]] += l_weight
        except KeyError:
            pass

        l_server_name = None
        try:
            l_server_name = l_response.headers["Server"]
        except KeyError:
            continue

        m_counters.simple_inc(l_server_name, l_method, l_weight)

    return parse_analyzer_results(m_counters, m_banners_counter, number_of_entries)




def http_analyzers(main_url, update_status_func, number_of_entries=4):
    """
    Analyze HTTP headers for detect the web server. Return a list with most possible web servers.

    :param main_url: Base url to test.
    :type main_url: str

    :param update_status_func: function used to update the status of the process
    :type update_status_func: function

    :param number_of_entries: number of resutls tu return for most probable web servers detected.
    :type number_of_entries: int

    :return: Web server family, Web server version, Web server complete description, related web servers (as a dict('SERVER_RELATED' : set(RELATED_NAMES))), others web server with their probabilities as a dict(CONCRETE_WEB_SERVER, PROBABILITY)
    """

    # Load wordlist directly related with a HTTP fields.
    # { HTTP_HEADER_FIELD : [wordlists] }
    m_wordlists_HTTP_fields = {
        "Accept-Ranges"              : "accept-range",
        "Server"                     : "banner",
        "Cache-Control"              : "cache-control",
        "Connection"                 : "connection",
        "Content-Type"               : "content-type",
        "WWW-Authenticate"           : "htaccess-realm",
        "Pragma"                     : "pragma",
        "X-Powered-By"               : "x-powered-by"
    }

    m_actions = {
        'GET'        : { 'wordlist' : 'Wordlist_get'            , 'weight' : 1 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/' },
        'LONG_GET'   : { 'wordlist' : 'Wordlist_get_long'       , 'weight' : 1 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/%s' % ('a' * 200) },
        'NOT_FOUND'  : { 'wordlist' : 'Wordlist_get_notfound'   , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': '/404_NOFOUND__X02KAS' },
        'HEAD'       : { 'wordlist' : 'Wordlist_head'           , 'weight' : 3 , 'protocol' : 'HTTP/1.1', 'method' : 'HEAD'     , 'payload': '/' },
        'OPTIONS'    : { 'wordlist' : 'Wordlist_options'        , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'OPTIONS'  , 'payload': '/' },
        'DELETE'     : { 'wordlist' : 'Wordlist_delete'         , 'weight' : 5 , 'protocol' : 'HTTP/1.1', 'method' : 'DELETE'   , 'payload': '/' },
        'TEST'       : { 'wordlist' : 'Wordlist_attack'         , 'weight' : 5 , 'protocol' : 'HTTP/1.1', 'method' : 'TEST'     , 'payload': '/' },
        'INVALID'    : { 'wordlist' : 'Wordlist_wrong_method'   , 'weight' : 5 , 'protocol' : 'HTTP/9.8', 'method' : 'GET'      , 'payload': '/' },
        'ATTACK'     : { 'wordlist' : 'Wordlist_wrong_version'  , 'weight' : 2 , 'protocol' : 'HTTP/1.1', 'method' : 'GET'      , 'payload': "/etc/passwd?format=%%%%&xss=\x22><script>alert('xss');</script>&traversal=../../&sql='%20OR%201;"}
    }


    # Store results for others HTTP params
    m_d                   = ParsedURL(main_url)
    m_hostname            = m_d.hostname
    m_port                = m_d.port
    m_debug               = False # Only for develop

    # Counter of banners. Used when others methods fails.
    m_banners_counter     = Counter()

    # Score counter
    m_counters = HTTPAnalyzer(debug=m_debug)

    # Var used to update the status
    m_data_len = len(m_actions)
    i          = 1 # element in process


    for l_action, v in m_actions.iteritems():
        if m_debug:
            print "###########"
        l_method      = v["method"]
        l_payload     = v["payload"]
        l_proto       = v["protocol"]
        l_wordlist    = v["wordlist"]

        # Each type of probe hast different weight.
        #
        # Weights go from 0 - 5
        #
        l_weight      = v["weight"]

        # Make the URL
        l_url         = urljoin(main_url, l_payload)

        # Make the raw request
        #l_raw_request = "%(method)s %(payload)s %(protocol)s\r\nHost: %(host)s:%(port)s\r\nConnection: Close\r\n\r\n" % (
        l_raw_request = "%(method)s %(payload)s %(protocol)s\r\nHost: %(host)s\r\n\r\n" % (
            {
                "method"     : l_method,
                "payload"    : l_payload,
                "protocol"   : l_proto,
                "host"       : m_hostname,
                "port"       : m_port
            }
        )
        if m_debug:
            print "REQUEST"
            print l_raw_request

        # Do the connection
        l_response = None
        try:
            m_raw_request = HTTP_Raw_Request(l_raw_request)
            discard_data(m_raw_request)
            l_response = HTTP.make_raw_request(
                host        = m_hostname,
                port        = m_port,
                raw_request = m_raw_request,
                callback    = check_raw_response)
            if l_response:
                discard_data(l_response)
        except NetworkException,e:
            Logger.log_error_more_verbose("Server-Fingerprint plugin: No response for URL (%s) '%s'. Message: %s" % (l_method, l_url, str(e)))
            continue

        if not l_response:
            Logger.log_error_more_verbose("No response for URL '%s'." % l_url)
            continue

        if m_debug:
            print "RESPONSE"
            print l_response.raw_headers


        # Update the status
        update_status_func((float(i) * 100.0) / float(m_data_len))
        Logger.log_more_verbose("Making '%s' test." % (l_wordlist))
        i += 1

        # Analyze for each wordlist
        #
        # Store the server banner
        try:
            m_banners_counter[l_response.headers["Server"]] += l_weight
        except KeyError:
            pass

        #
        # =====================
        # HTTP directly related
        # =====================
        #
        #
        for l_http_header_name, l_header_wordlist in m_wordlists_HTTP_fields.iteritems():

            # Check if HTTP header field is in response
            if l_http_header_name not in l_response.headers:
                continue

            l_curr_header_value = l_response.headers[l_http_header_name]

            # Generate concrete wordlist name
            l_wordlist_path     = Config.plugin_extra_config[l_wordlist][l_header_wordlist]

            # Load words for the wordlist
            l_wordlist_instance = WordListLoader.get_wordlist_as_dict(l_wordlist_path)
            # Looking for matches
            l_matches           = l_wordlist_instance.matches_by_value(l_curr_header_value)

            m_counters.inc(l_matches, l_action, l_weight, l_http_header_name, message="HTTP field: " + l_curr_header_value)

        #
        # =======================
        # HTTP INdirectly related
        # =======================
        #
        #

        #
        # Status code
        # ===========
        #
        l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["statuscode"])
        # Looking for matches
        l_matches           = l_wordlist_instance.matches_by_value(l_response.status)

        m_counters.inc(l_matches, l_action, l_weight, "statuscode", message="Status code: " + l_response.status)


        #
        # Status text
        # ===========
        #
        l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["statustext"])
        # Looking for matches
        l_matches           = l_wordlist_instance.matches_by_value(l_response.reason)

        m_counters.inc(l_matches, l_action, l_weight, "statustext", message="Status text: " + l_response.reason)


        #
        # Header space
        # ============
        #
        # Count the number of spaces between HTTP field name and their value, for example:
        # -> Server: Apache 1
        # The number of spaces are: 1
        #
        # -> Server:Apache 1
        # The number of spaces are: 0
        #
        l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["header-space"])
        # Looking for matches
        try:
            l_http_value        = l_response.headers[0] # get the value of first HTTP field
            l_spaces_num        = str(abs(len(l_http_value) - len(l_http_value.lstrip())))
            l_matches           = l_wordlist_instance.matches_by_value(l_spaces_num)

            m_counters.inc(l_matches, l_action, l_weight, "header-space", message="Header space: " + l_spaces_num)

        except IndexError:
            print "index error header space"
            pass


        #
        # Header capitalafterdash
        # =======================
        #
        # Look for non capitalized first letter of field name, for example:
        # -> Content-type: ....
        # Instead of:
        # -> Content-Type: ....
        #
        l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["header-capitalafterdash"])
        # Looking for matches
        l_valid_fields     = [x for x in l_response.headers.iterkeys() if "-" in x]

        if l_valid_fields:

            l_h = l_valid_fields[0]

            l_value = l_h.split("-")[1] # Get the second value: Content-type => type
            l_dush  = None

            if l_value[0].isupper(): # Check first letter is lower
                l_dush = 1
            else:
                l_dush = 0

            l_matches           = l_wordlist_instance.matches_by_value(l_dush)
            m_counters.inc(l_matches, l_action, l_weight, "header-capitalizedafterdush", message="Capital after dash: %s" % str(l_dush))

        #
        # Header order
        # ============
        #
        l_header_order  = ','.join(l_response.headers.iterkeys())

        l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["header-order"])
        l_matches           = l_wordlist_instance.matches_by_value(l_header_order)

        m_counters.inc(l_matches, l_action, l_weight, "header-order", message="Header order: " + l_header_order)


        #
        # Protocol name
        # ============
        #
        # For a response like:
        # -> HTTP/1.0 200 OK
        #    ....
        #
        # Get the 'HTTP' value.
        #
        try:
            l_proto             = l_response.protocol # Get the 'HTTP' text from response, if available
            if l_proto:
                l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["protocol-name"])
                l_matches           = l_wordlist_instance.matches_by_value(l_proto)

                m_counters.inc(l_matches, l_action, l_weight, "proto-name", message="Proto name: " + l_proto)

        except IndexError:
            print "index error protocol name"
            pass


        #
        # Protocol version
        # ================
        #
        # For a response like:
        # -> HTTP/1.0 200 OK
        #    ....
        #
        # Get the '1.0' value.
        #
        try:
            l_version           = l_response.version # Get the '1.0' text from response, if available
            if l_version:
                l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["protocol-version"])
                l_matches           = l_wordlist_instance.matches_by_value(l_version)

                m_counters.inc(l_matches, l_action, l_weight, "proto-version", message="Proto version: " + l_version)

        except IndexError:
            print "index error protocol version"
            pass



        if "ETag" in l_response.headers:
            l_etag_header       = l_response.headers["ETag"]
            #
            # ETag length
            # ================
            #
            l_etag_len          = len(l_etag_header)
            l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["etag-legth"])
            l_matches           = l_wordlist_instance.matches_by_value(l_etag_len)

            m_counters.inc(l_matches, l_action, l_weight, "etag-length", message="ETag length: " + str(l_etag_len))


            #
            # ETag Quotes
            # ================
            #
            l_etag_striped          = l_etag_header.strip()
            if l_etag_striped.startswith("\"") or l_etag_striped.startswith("'"):
                l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["etag-quotes"])
                l_matches           = l_wordlist_instance.matches_by_value(l_etag_striped[0])

                m_counters.inc(l_matches, l_action, l_weight, "etag-quotes", message="Etag quotes: " + l_etag_striped[0])

        if "Vary" in l_response.headers:
            l_vary_header       = l_response.headers["Vary"]
            #
            # Vary delimiter
            # ================
            #
            # Checks if Vary header delimiter is something like this:
            # -> Vary: Accept-Encoding,User-Agent
            # Or this:
            # -> Vary: Accept-Encoding, User-Agent
            #
            l_var_delimiter     = ", " if l_vary_header.find(", ") else ","
            l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["vary-delimiter"])
            l_matches           = l_wordlist_instance.matches_by_value(l_var_delimiter)

            m_counters.inc(l_matches, l_action, l_weight, "vary-delimiter", message="Vary delimiter: " + l_var_delimiter)

            #
            # Vary capitalizer
            # ================
            #
            # Checks if Vary header delimiter is something like this:
            # -> Vary: Accept-Encoding,user-Agent
            # Or this:
            # -> Vary: accept-encoding,user-agent
            #
            l_vary_capitalizer  = str(0 if l_vary_header == l_vary_header.lower() else 1)
            l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["vary-capitalize"])
            l_matches           = l_wordlist_instance.matches_by_value(l_vary_capitalizer)

            m_counters.inc(l_matches, l_action, l_weight, "vary-capitalize", message="Vary capitalizer: " + l_vary_capitalizer)


            #
            # Vary order
            # ================
            #
            # Checks order between vary values:
            # -> Vary: Accept-Encoding,user-Agent
            # Or this:
            # -> Vary: User-Agent,Accept-Encoding
            #
            l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["vary-order"])
            l_matches           = l_wordlist_instance.matches_by_value(l_vary_header)

            m_counters.inc(l_matches, l_action, l_weight, "vary-order", message="Vary order: " + l_vary_header)


        #
        # =====================
        # HTTP specific options
        # =====================
        #
        #
        if l_action == "HEAD":
            #
            # HEAD Options
            # ============
            #
            l_option            = l_response.headers.get("Allow")
            if l_option:
                l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["options-public"])
                # Looking for matches
                l_matches           = l_wordlist_instance.matches_by_value(l_option)

                m_counters.inc(l_matches, l_action, l_weight, "options-allow", message="HEAD option: " + l_option)


        if l_action == "OPTIONS" or l_action == "INVALID" or l_action == "DELETE":
            if "Allow" in l_response.headers:
                #
                # Options allow
                # =============
                #
                l_option            = l_response.headers.get("Allow")
                if l_option:
                    l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["options-public"])
                    # Looking for matches
                    l_matches           = l_wordlist_instance.matches_by_value(l_option)

                    m_counters.inc(l_matches, l_action, l_weight, "options-allow", message="OPTIONS allow: "  + l_action + " # " + l_option)


                #
                # Allow delimiter
                # ===============
                #
                l_option            = l_response.headers.get("Allow")
                if l_option:
                    l_var_delimiter     = ", " if l_option.find(", ") else ","
                    l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["options-delimited"])
                    # Looking for matches
                    l_matches           = l_wordlist_instance.matches_by_value(l_var_delimiter)

                    m_counters.inc(l_matches, l_action, l_weight, "options-delimiter", message="OPTION allow delimiter " + l_action + " # " + l_option)


            if "Public" in l_response.headers:
                #
                # Public response
                # ===============
                #
                l_option            = l_response.headers.get("Public")
                if l_option:
                    l_wordlist_instance = WordListLoader.get_wordlist_as_dict(Config.plugin_extra_config[l_wordlist]["options-public"])
                    # Looking for matches
                    l_matches           = l_wordlist_instance.matches_by_value(l_option)

                    m_counters.inc(l_matches, l_action, l_weight, "options-public", message="Public response: " + l_action + " # " + l_option)


    if m_debug:
        print "Common score"
        print m_counters.results_score.most_common(10)
        print "Common score complete"
        print m_counters.results_score_complete.most_common(10)
        print "Common count"
        print m_counters.results_count.most_common(10)
        print "Common count complete"
        print m_counters.results_count_complete.most_common(10)
        print "Determinators"
        print "============="
        for a in m_counters.results_score_complete.most_common(10):
        #for k,v in m_counters.results_determinator_complete.iteritems():
            k = a[0]
            print ""
            print k
            print "-" * len(k)
            for l,v in m_counters.results_determinator_complete[k].iteritems():
                print "   %s (%s  [ %s ] )" % (l, ','.join(v), str(len(v)))


    return parse_analyzer_results(m_counters, m_banners_counter, number_of_entries)


#------------------------------------------------------------------------------
def parse_analyzer_results(analyzer, banner_counter, number_of_entries=4):
    """
    Parse analyzer results and gets the values:

    :param analyzer: a HTTPAnalyzer instance.
    :type analyzer: HTTPAnalyzer

    :param banner_counter: simple Counter with a number of banner for each server
    :type banner_counter: Counter

    :return: a tuple as format (server_family, server_version, canonical_name, complete_server_name, related_servers, other_probability_servers)
    :rtype: tupple
    """


    #
    # Filter the results
    #
    m_other_servers_prob = OrderedDict() # { WEB_SERVER, PROBABILITY }

    # Get web server family. F.E: Apache
    m_server_family         = None
    m_server_version        = None
    m_server_related        = None
    m_server_complete       = None
    m_server_canonical_name = None
    m_counters              = analyzer
    m_banners_counter       = banner_counter

    # If fingerprint found
    if m_counters.results_score.most_common():

        l_tmp_server_info       = m_counters.results_score.most_common(1)[0][0]
        l_tmp_info              = l_tmp_server_info.split("-")

        m_server_family         = l_tmp_info[0]
        m_server_version        = l_tmp_info[1]
        m_server_related        = m_counters.related_webservers[l_tmp_server_info]
        m_server_canonical_name = m_counters.canonical_webserver_name[l_tmp_server_info]

        # Get concrete versions and the probability
        m_base_percent = m_counters.results_score_complete.most_common(1)[0][1] # base value used for calculate percents
        for v in m_counters.results_score_complete.most_common(25):
            l_server_name    = v[0]
            l_server_prob    = v[1]

            if m_server_family.lower() not in l_server_name.lower():
                continue

            # Asociate complete web server info with most probable result
            if not m_server_complete and m_server_version in l_server_name:
                m_server_complete = l_server_name

            # Add the probabilities as a float between 0 and 1
            m_other_servers_prob[l_server_name] = float(l_server_prob) / float(m_base_percent)

            # Get only 4 results
            if len(m_other_servers_prob) >= number_of_entries:
                break

        # Save nulls
        if not m_server_complete:
            m_server_complete = "Unknown"

    else:
        try:
            l_banner = m_banners_counter.most_common(n=1)[0][0]
        except IndexError:
            l_banner = "Unknown"
        if l_banner:
            m_server_family, m_server_version, m_server_canonical_name, m_server_related  = calculate_server_track(l_banner)
            m_server_complete                  = l_banner
            m_other_servers_prob               = dict()
        else:
            m_server_family         = "Unknown"
            m_server_version        = "Unknown"
            m_server_related        = set()
            m_server_canonical_name = "Unknown"
            m_server_complete       = "Unknown web server"
            m_other_servers_prob    = dict()

    return m_server_family, m_server_version, m_server_canonical_name, m_server_complete, m_server_related, m_other_servers_prob


#------------------------------------------------------------------------------
class HTTPAnalyzer(object):


    #--------------------------------------------------------------------------
    def __init__(self, debug = False):

        self.__HTTP_fields_weight = {
            "accept-ranges"                : 1,
            "server"                       : 4,
            "cache-control"                : 2,
            "connection"                   : 2,
            "content-type"                 : 1,
            "etag-length"                  : 5,
            "etag-quotes"                  : 2,
            "header-capitalizedafterdush"  : 2,
            "header-order"                 : 10,
            "header-space"                 : 2,
            "www-authenticate"             : 3,
            "pragma"                       : 2,
            "proto-name"                   : 1,
            "proto-version"                : 2,
            "statuscode"                   : 4,
            "statustext"                   : 4,
            "vary-capitalize"              : 2,
            "vary-delimiter"               : 2,
            "vary-order"                   : 3,
            "x-powered-by"                 : 3,
            "options-allow"                : 1,
            "options-public"               : 2,
            "options-delimiter"            : 2
        }

        self.__debug = debug

        #
        # Store structures. Format:
        #
        # { SERVER_NAME: int }
        #
        # Where:
        # - SERVER_NAME -> Discovered server name
        # - int         -> Number of wordlist that matches this server
        #
        # Store results for HTTP directly related fields

        # Scores:
        #
        # Count server + major version: nginx-1.5.1-r2 -> nginx-1.5
        self.__results_score          = Counter()
        # Count server + all revision: nginx-1.5.1-r2
        self.__results_score_complete = Counter()

        # Simple counters:
        #
        # Count server + major version: nginx-1.5.1-r2 -> nginx-1.5
        self.__results_count          = Counter()
        # Count server + all revision: nginx-1.5.1-r2
        self.__results_count_complete = Counter()
        # Canonical name for a server: {'Internet Information Server' : "iis"}
        self.__results_canonical      = defaultdict(str)
        # Stores the related servers to one web servers: {'IIS': 'hyperion' }
        self.__results_related        = defaultdict(set)

        #
        # Determinator parameters for each server. Format:
        # {'SERVER_NAME':
        #    {
        #       'HTTP_FIELD' : (HTTP_METHODS)
        #    }
        # }
        #
        # Examples:
        #
        # {'nginx':
        #    {
        #       'options-public' : ('GET', 'PUT')
        #    }
        # }
        #
        #
        self.__determinator          = defaultdict(lambda: defaultdict(set))
        self.__determinator_complete = defaultdict(lambda: defaultdict(set))


    #--------------------------------------------------------------------------
    def inc(self, test_lists, method, method_weight, types, message = ""):
        """
        Increment values associated with the fields as parameters.

        :param test_list: List with server informations.
        :type test_list: dict(KEY, list(VALUES))

        :param method: HTTP method used to make the request.
        :type method: str

        :param method_weight: The weight associated to the HTTP method.
        :type method_weight: int

        :param types: HTTP field to process.
        :type types: str

        :param message: Message to debug the method call
        :type message: str

        :return: Don't return anything
        """
        if test_lists:
            l_types = types.lower()

            # Debug info
            if self.__debug:
                print "%s: %s" % (message, l_types)

            # Get parsed web server list
            l_server_splited = [ calculate_server_track(server) for server in test_lists]

            # Count only one time of each web server
            for u in l_server_splited:
                l_server                = "%s-%s" % (u[0], u[1]) # (Server name, Server version)
                self.__results_count[l_server] += 1 * method_weight
                self.__results_score[l_server] += self.__HTTP_fields_weight[l_types] * method_weight

                # Stores the canonical name
                self.__results_canonical[l_server] = u[2]

                # Stores the related servers to this web server
                self.__results_related[l_server].update(u[3])

                # Store determinators
                self.__determinator[l_server][l_types].add(method)

            # Count all info
            for l_full_server_name in test_lists:

                #m_results_http_fields[server] += 1 * l_weight
                self.__results_count_complete[l_full_server_name] += 1 * method_weight
                self.__results_score_complete[l_full_server_name] += self.__HTTP_fields_weight[l_types] * method_weight

                # Store determinators
                self.__determinator_complete[l_full_server_name][l_types].add(method)


    #--------------------------------------------------------------------------
    def simple_inc(self, server_name, method, method_weight, message = ""):
        """
        Increment values associated with the fields as parameters.

        :param server_name: String with the server name
        :type server_name: str

        :param method: HTTP method used to make the request.
        :type method: str

        :param method_weight: The weight associated to the HTTP method.
        :type method_weight: int

        :param message: Message to debug the method call
        :type message: str

        :return: Don't return anything
        """
        if server_name:

            # Debug info
            if self.__debug:
                print "%s: %s" % (method, message)

            # Get parsed web server
            l_server_splited                   = calculate_server_track(server_name)
            l_server                           = "%s-%s" % (l_server_splited[0], l_server_splited[1]) # (Server name, Server version)

            # Counting
            self.__results_count[l_server]     += 1 * method_weight

            # Stores the canonical name
            self.__results_canonical[l_server] = l_server_splited[2]

            # Stores the related servers to this web server
            self.__results_related[l_server].update(l_server_splited[3])


    #--------------------------------------------------------------------------
    @property
    def results_score(self):
        return self.__results_score


    #--------------------------------------------------------------------------
    @property
    def results_score_complete(self):
        return self.__results_score_complete


    #--------------------------------------------------------------------------
    @property
    def results_count(self):
        return self.__results_count


    #--------------------------------------------------------------------------
    @property
    def results_count_complete(self):
        return self.__results_count_complete


    #--------------------------------------------------------------------------
    @property
    def results_determinator(self):
        return self.__determinator


    #--------------------------------------------------------------------------
    @property
    def related_webservers(self):
        return self.__results_related


    #--------------------------------------------------------------------------
    @property
    def canonical_webserver_name(self):
        return self.__results_canonical


    #--------------------------------------------------------------------------
    @property
    def results_determinator_complete(self):
        return self.__determinator_complete


#------------------------------------------------------------------------------
#
# Aux functions
#
#------------------------------------------------------------------------------
def check_raw_response(request, response):

    # Returns True to continue, False to cancel.
    return (

        # Check the content length is not too large.
        response.content_length is not None and response.content_length < 200000

    )


def calculate_server_track(server_name):
    """
    from nginx/1.5.1-r2 -> ("nginx", "1.5.1")

    :return: tuple with server family and their version
    :rtype: tuple(SERVER_FAMILY, SERVER_VERSION, FAMILY_CANONICAL_NAME, RELATED_WEBSERVERS=set(str(RELATED_WEBSERVERS)))
    """

    # Name -> nginx

    #
    # Get server version
    # ------------------
    #
    # Transform strings like:
    #
    # nginx/1.5.1    -> "1.5"
    # nginx 1.5.1-r2 -> "1.5"
    # nginx/1.5.1v5  -> "1.5"
    # Microsoft IIS 6.0 -> "6.0"
    #
    if not server_name:
        raise ValueError("Empty value")

    m_server_version_tmp_search = SERVER_PATTERN.search(server_name)

    if not m_server_version_tmp_search:
        m_server_version     = "Unknown"
    else:
        m_server_version_tmp = m_server_version_tmp_search.group(2)

        try:

            # if version has format: 6.0v1 or 2.0
            if m_server_version_tmp.count(".") == 1:
                m_server_version = m_server_version_tmp
            else:
                # Major version: 1.5.1 -> 1.5
                l_i = nindex(m_server_version_tmp, ".", 2)

                if l_i != -1:
                    m_server_version = m_server_version_tmp[:l_i]
                else:
                    m_server_version = m_server_version_tmp

        except ValueError:
            m_server_version = "Unknown"

    #
    # Get server family
    # ------------------
    #
    # Get the server name from a database from with a keyworks to most common
    # web servers.
    #
    # Load keys an related servers
    m_servers_keys, m_servers_related_tmp = get_fingerprinting_wordlist(Config.plugin_config["keywords"])

    # Looking for web server in the keys
    m_resultsc = Counter()
    for l_family, l_keys in m_servers_keys.iteritems():
        for k in l_keys:
            if k in server_name:
                m_resultsc[l_family] +=1


    # There is keys for this web server?
    if len(m_resultsc.most_common(10)) == 0:
        m_server_canonical_name = "unknown"
    else:
        m_server_canonical_name = m_resultsc.most_common(1)[0][0]

    #
    # Checks For server name
    #
    if m_server_version_tmp_search and len(m_server_version_tmp_search.groups()) == 2:
        m_server_name = m_server_version_tmp_search.group(1)
    elif m_server_canonical_name != "unknown":
        m_server_name = m_server_canonical_name
    else:
        m_server_name = "unknown"

    try:
        m_servers_related = m_servers_related_tmp[m_server_canonical_name]
    except KeyError:
        m_servers_related = set()

    return (m_server_name, m_server_version, m_server_canonical_name, m_servers_related)


#------------------------------------------------------------------------------
def nindex(str_in, substr, nth):
    """
    From and string get nth ocurrence of substr
    """

    m_slice  = str_in
    n        = 0
    m_return = None
    while nth:
        try:
            n += m_slice.index(substr) + len(substr)
            m_slice = str_in[n:]
            nth -= 1
        except ValueError:
            break
    try:
        m_return = n - 1
    except ValueError:
        m_return = 0

    return m_return


#------------------------------------------------------------------------------
def get_fingerprinting_wordlist(wordlist):
    """
    Load the wordlist of fingerprints and prepare the info in a dict.

    It using as a keys the name of the server family and, as value, an
    iterable with the keywords related with this web server.

    :return: The results of load of webservers keywords info and related webservers.
    :rtype: tuple(WEBSERVER_KEYWORDS, RELATED_SERVES) <=>  (dict(SERVERNAME: set(str(KEYWORDS))), dict(SERVER_NAME, set(str(RELATED_SERVERS)))
    """

    # Load the wordlist
    m_w = WordListLoader.get_wordlist_as_dict(wordlist, separator=";", smart_load=True)

    # Load references.
    #
    #   References in the wordlist are specified by # prefix.
    #
    already_parsed    = set()
    related           = defaultdict(set)
    m_webservers_keys = extend_items(m_w, already_parsed, related)

    return (m_webservers_keys, related)


#------------------------------------------------------------------------------
def extend_items(all_items, already_parsed, related, ref = None):
    """
    Recursive function to walk the tree of fingerprinting keywords.

    Returns an ordered list with the keywords associated.

    In related dict, stores the relations. For example:

    If you have this keywordlist:

        >>> open("keywords.txt").readlines()
        iis: IIS, ISA
        hyperion: #iis

    The `related` dict would be:

        >>> print related
        defaultdict(<type 'set'>, {'iis': set(['hyperion'])})

    :param all_items: raw wordlist with references.
    :type all_items: dict

    :param already_parsed: tuples with the keys already parsed.
    :type already_parsed: Set

    :param ref: key to explore. Optional param.
    :type ref: str

    :param related: dict to store the related webservers.
    :type related: dict(SERVER_NAME, set(str(RELATED_WEBSERVER)))

    :return: Ordered dict with the discovered info.
    :rtype: OrderedDict
    """
    m_return        = defaultdict(set)
    m_return_update = m_return.update

    # Stop point
    if ref:
        try:
            if ref not in already_parsed:
                already_parsed.add(ref)
                for l_v in all_items[ref]:
                    if l_v.startswith("#"):
                        # Follow the reference
                        m_return_update(extend_items(all_items, already_parsed, related, ref=l_v[1:]))

                        # Add to reference
                        related[l_v[1:]].add(ref)
                    else:
                        m_return[ref].add(l_v)
        except KeyError:
            pass
    else:
        for k, v in all_items.iteritems():
            if k not in already_parsed:
                already_parsed.add(k)
                for l_v in v:
                    if l_v.startswith("#"):
                        # Follow the reference
                        m_return_update(extend_items(all_items, already_parsed, related, ref=l_v[1:]))

                        # Add to reference
                        related[l_v[1:]].add(k)
                    else:
                        m_return[k].add(l_v)

    return m_return
