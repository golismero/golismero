#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: http://golismero-project.com
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

from golismero.api.config import Config
from golismero.api.data import discard_data
from golismero.api.data.information.webserver_fingerprint import WebServerFingerprint
from golismero.api.data.resource.url import FolderUrl, Url
from golismero.api.data.vulnerability.information_disclosure.url_disclosure import UrlDisclosure
from golismero.api.logger import Logger
from golismero.api.net.http import HTTP
from golismero.api.net.web_utils import ParsedURL
from golismero.api.text.matching_analyzer import MatchingAnalyzer, get_diff_ratio
from golismero.api.text.wordlist import WordListLoader
from golismero.api.text.text_utils import generate_random_string

from golismero.api.plugin import TestingPlugin
from functools import partial
from urlparse import urljoin


__doc__ = """

.. note:
   Acknowledgments:

   We'd like to thank @capi_x for his idea on how
   to detect fake 200 responses from servers by
   issuing known good and bad queries and diffing
   them to calculate the deviation.

   https://twitter.com/capi_x
"""


#-------------------------------------------------------------------------

# Impact vectors. Available values: 0 - 4.
severity_vectors = {
    "suffixes" : 4,
    "prefixes" : 3,
    "file_extensions": 3,
    "permutations" : 3,
    "predictables": 4,
    "directories": 2
}


#----------------------------------------------------------------------
class PredictablesDisclosureBruteforcer(TestingPlugin):


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [FolderUrl]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        m_url = info.url

        Logger.log_more_verbose("Start to process URL: %r" % m_url)

        #
        # Get the remote web server fingerprint
        #
        m_webserver_finger = info.get_associated_informations_by_category(WebServerFingerprint.information_type)

        m_wordlist = set()
        # There is fingerprinting information?
        if m_webserver_finger:

            m_webserver_finger = m_webserver_finger.pop()

            m_server_canonical_name = m_webserver_finger.name_canonical
            m_servers_related       = m_webserver_finger.related # Set with related web servers

            #
            # Load wordlists
            #
            m_wordlist_update  = m_wordlist.update

            # Common wordlist
            try:
                w = Config.plugin_extra_config["common"]
                m_wordlist_update([l_w for l_w in w.itervalues()])
            except KeyError:
                pass


            # Wordlist of server name
            try:
                w = Config.plugin_extra_config["%s_predictables" % m_server_canonical_name]
                m_wordlist_update([l_w for l_w in w.itervalues()])
            except KeyError:
                pass

            # Wordlist of related with the server found
            try:
                for l_servers_related in m_servers_related:
                    w = Config.plugin_extra_config["%s_predictables" % m_server_canonical_name]
                    m_wordlist_update([l_w for l_w in w.itervalues()])
            except KeyError:
                pass

        else:

            # Common wordlists
            try:
                w = Config.plugin_extra_config["common"]
                m_wordlist.update([l_w for l_w in w.itervalues()])
            except KeyError:
                pass


        # Load content of wordlists
        m_urls           = set()
        m_urls_update    = m_urls.update

        # Fixed Url
        m_url_fixed      = m_url if m_url.endswith("/") else "%s/" % m_url

        for l_w in m_wordlist:
            # Use a copy of wordlist to avoid modify the original source
            l_loaded_wordlist = WordListLoader.get_advanced_wordlist_as_list(l_w)

            m_urls_update((urljoin(m_url_fixed, (l_wo[1:] if l_wo.startswith("/") else l_wo)) for l_wo in l_loaded_wordlist))

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['predictables'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))

        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
class SuffixesDisclosureBruteforcer(TestingPlugin):
    """
    Testing suffixes: index.php -> index_0.php
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Parse original URL
        m_url = info.url
        m_url_parts = info.parsed_url

        Logger.log_more_verbose("Bruteforcing URL: %s" % m_url)

        # If file is a javascript, css or image, do not run
        if info.parsed_url.extension[1:] in ('css', 'js', 'jpeg', 'jpg', 'png', 'gif', 'svg') or not m_url_parts.extension:
            Logger.log_more_verbose("Skipping URL: %s" % m_url)
            return

        #
        # Load wordlist for suffixes: index.php -> index_0.php
        #
        # COMMON
        m_urls = make_url_with_suffixes(get_list_from_wordlist("common_suffixes"), m_url_parts)

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['suffixes'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))

        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
class PrefixesDisclosureBruteforcer(TestingPlugin):
    """
    Testing changing extension of files
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Parse original URL
        m_url = info.url
        m_url_parts = info.parsed_url

        Logger.log_more_verbose("Bruteforcing URL: %s" % m_url)

        # If file is a javascript, css or image, do not run
        if info.parsed_url.extension[1:] in ('css', 'js', 'jpeg', 'jpg', 'png', 'gif', 'svg') or not m_url_parts.extension:
            Logger.log_more_verbose("Skipping URL: %s" % m_url)
            return

        #
        # Load wordlist for prefixes
        #
        # COMMON
        m_urls = make_url_with_prefixes(get_list_from_wordlist("common_prefixes"), m_url_parts)

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['prefixes'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))


        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
class FileExtensionsDisclosureBruteforcer(TestingPlugin):
    """
    Testing changing extension of files
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Parse original URL
        m_url = info.url
        m_url_parts = info.parsed_url

        Logger.log_more_verbose("Start to process URL: %s" % m_url)

        # If file is a javascript, css or image, do not run
        if info.parsed_url.extension[1:] in ('css', 'js', 'jpeg', 'jpg', 'png', 'gif', 'svg') or not m_url_parts.extension:
            Logger.log_more_verbose("Skipping URL: %s" % m_url)
            return

        #
        # Load wordlist for changing extension of files
        #
        # COMMON
        m_urls = make_url_changing_extensions(get_list_from_wordlist("common_extensions"), m_url_parts)

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['file_extensions'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))

        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
class PermutationsDisclosureBruteforcer(TestingPlugin):
    """
    Testing filename permutations
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Parse original URL
        m_url = info.url
        m_url_parts = info.parsed_url

        Logger.log_more_verbose("Bruteforcing URL: '%s'" % m_url)

        # If file is a javascript, css or image, do not run
        if info.parsed_url.extension[1:] in ('css', 'js', 'jpeg', 'jpg', 'png', 'gif', 'svg') or not m_url_parts.extension:
            Logger.log_more_verbose("Skipping URL: %s" % m_url)
            return

        #
        # Load wordlist for permutations
        #
        # COMMON
        m_urls = make_url_mutate_filename(m_url_parts)

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['permutations'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))
        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
class DirectoriesDisclosureBruteforcer(TestingPlugin):
    """
    Testing changing directories of files
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):
        return [Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # Parse original URL
        m_url = info.url
        m_url_parts = info.parsed_url

        Logger.log_more_verbose("Bruteforcing URL: %s" % m_url)

        # If file is a javascript, css or image, do not run
        if info.parsed_url.extension[1:] in ('css', 'js', 'jpeg', 'jpg', 'png', 'gif', 'svg') or not m_url_parts.extension:
            Logger.log_more_verbose("Skipping URL: %s" % m_url)
            return

        #
        # Load wordlist for changing directories
        #
        # COMMON
        m_urls = make_url_changing_folder_name(m_url_parts)

        # Generates the error page
        m_error_response = get_error_page(m_url)

        # Create the matching analyzer
        try:
            m_store_info = MatchingAnalyzer(m_error_response, min_ratio=0.65)
        except ValueError:
            # Thereis not information
            return

        # Create the partial funs
        _f = partial(process_url,
                     severity_vectors['directories'],
                     get_http_method(m_url),
                     m_store_info,
                     self.update_status,
                     len(m_urls))

        # Process the URLs
        for i, l_url in enumerate(m_urls):
            _f((i, l_url))

        # Generate and return the results.
        return generate_results(m_store_info.unique_texts)


#----------------------------------------------------------------------
def process_url(risk_level, method, matcher, updater_func, total_urls, url):
    """
    Checks if an URL exits.

    :param risk_level: risk level of the tested URL, if discovered.
    :type risk_level: int

    :param method: string with HTTP method used.
    :type method: str

    :param matcher: instance of MatchingAnalyzer object.
    :type matcher: `MatchingAnalyzer`

    :param updater_func: update_status function to send updates
    :type updater_func: update_status

    :param total_urls: total number of URL to globally process.
    :type total_urls: int

    :param url: a tuple with data: (index, the URL to process)
    :type url: tuple(int, str)
    """

    i, url = url

    updater_func((float(i) * 100.0) / float(total_urls))
    Logger.log_more_verbose("Trying to discover URL %s" % url)

    # Get URL
    p = None
    try:
        p = HTTP.get_url(url, use_cache=False, method=method)
        if p:
            discard_data(p)
    except Exception, e:
        Logger.log_more_verbose("Error while processing: '%s': %s" % (url, str(e)))

    # Check if the url is acceptable by comparing
    # the result content.
    #
    # If the maching level between the error page
    # and this url is greater than 52%, then it's
    # the same URL and must be discarded.
    #
    if p and p.status == "200":

        # If the method used to get URL was HEAD, get complete URL
        if method != "GET":
            try:
                p = HTTP.get_url(url, use_cache=False, method="GET")
                if p:
                    discard_data(p)
            except Exception, e:
                Logger.log_more_verbose("Error while processing: '%s': %s" % (url, str(e)))

        # Append for analyze and display info if is accepted
        if matcher.analyze(p.raw_response, url=url, risk=risk_level):
            updater_func(text="Discovered partial url: '%s'" % url)


#----------------------------------------------------------------------
#
# Aux functions
#
#----------------------------------------------------------------------
def load_wordlists(wordlists):
    """
    Load the with names pased as parameter.

    This function receives a list of names of wordlist, defined in plugin
    configuration file, and return a dict with instances of wordlists.

    :param wordlists: list with wordlists names
    :type wordlists: list

    :returns: A dict with wordlists
    :rtype: dict
    """

    m_tmp_wordlist = {}

    # Get wordlist to load
    for l_w in wordlists:
        for wordlist_family, l_wordlists in Config.plugin_extra_config.iteritems():
            if wordlist_family.lower() in l_w.lower():
                m_tmp_wordlist[l_w] = l_wordlists

    # Load the wordlist
    m_return = {}
    for k, w_paths in m_tmp_wordlist.iteritems():
        m_return[k] = [WordListLoader.get_wordlist(w) for w in w_paths]

    return m_return


#----------------------------------------------------------------------
def get_http_method(url):
    """
    This function determinates if the method HEAD is available. To do that, compare between two responses:
    - One with GET method
    - One with HEAD method

    If both are seem more than 90%, the response are the same and HEAD method are not allowed.
    """

    m_head_response = HTTP.get_url(url, method="HEAD")  # FIXME handle exceptions!
    discard_data(m_head_response)

    m_get_response  = HTTP.get_url(url)  # FIXME handle exceptions!
    discard_data(m_get_response)

    # Check if HEAD reponse is different that GET response, to ensure that results are valids
    return "HEAD" if HTTP_response_headers_analyzer(m_head_response.headers, m_get_response.headers) < 0.90 else "GET"


#------------------------------------------------------------------------------
# HTTP response analyzer.

def HTTP_response_headers_analyzer(response_header_1, response_header_2):
    """
    Does a HTTP comparison to determinate if two HTTP response matches with the
    same content without need the body content. To do that, remove some HTTP headers
    (like Date or Cache info).

    Return a value between 0-1 with the level of difference. 0 is lowest and 1 the highest.

    - If response_header_1 is more similar to response_header_2, value will be near to 100.
    - If response_header_1 is more different to response_header_2, value will be near to 0.

    :param response_header_1: text with http response headers.
    :type response_header_1: http headers

    :param response_header_2: text with http response headers.
    :type response_header_2: http headers
    """

    m_invalid_headers = [
        "Date",
        "Expires",
        "Last-Modified",
    ]

    m_res1 = ''.join([ "%s:%s" % (k,v) for k,v in response_header_1.iteritems() if k not in m_invalid_headers ])
    m_res2 = ''.join([ "%s:%s" % (k,v) for k,v in response_header_2.iteritems() if k not in m_invalid_headers ])

    return get_diff_ratio(m_res1, m_res2)


#----------------------------------------------------------------------
def get_error_page(url):
    """
    Generates an error page an get their content.

    :param url: string with the base Url.
    :type url: str

    :return: a string with the content of response.
    :rtype: str
    """

    #
    # Generate an error in server to get an error page, using a random string
    #
    # Make the URL
    m_error_url      = "%s%s" % (url, generate_random_string())

    # Get the request
    m_error_response = HTTP.get_url(m_error_url)  # FIXME handle exceptions!
    discard_data(m_error_response)
    m_error_response = m_error_response.data


#----------------------------------------------------------------------
def generate_results(unique_texts):
    """
    Generates a list of results from a list of URLs as string format.

    :param unique_texts: list with a list of URL as string.
    :type unique_texts: list(Url)

    :return: a list of Url/UrlDiclosure.
    :type: list(Url|UrlDiclosure)
    """
    # Analyze resutls
    m_results        = []
    m_results_append = m_results.append

    for l_match in unique_texts:
        #
        # Set disclosure vulnerability
        l_url                      = Url(l_match.url)
        l_vuln                     = UrlDisclosure(l_url)

        # Set impact
        l_vuln.risk                = l_match.risk

        # Store
        m_results_append(l_url)
        m_results_append(l_vuln)

    return m_results


#----------------------------------------------------------------------
#
# Mutation functions
#
#----------------------------------------------------------------------
def make_url_with_prefixes(wordlist, url_parts):
    """
    Creates a set of URLs with prefixes.

    :param wordlist: Wordlist iterator.
    :type wordlist: WordList

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :returns: a set with urls.
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))

    if not wordlist:
        raise ValueError("Internal error!")

    m_new        = url_parts.copy() # Works with a copy
    m_return     = set()
    m_return_add = m_return.add
    m_filename   = m_new.filename
    for l_suffix in wordlist:

        # Format: _.index.php
        m_new.filename = "%s_%s" % (l_suffix, m_filename)
        m_return_add(m_new.url)

        # Format: .index_1.php
        m_new.filename = "%s%s" % (l_suffix, m_filename)
        m_return_add(m_new.url)

    return m_return


#----------------------------------------------------------------------
def make_url_with_suffixes(wordlist, url_parts):
    """
    Creates a set of URLs with suffixes.

    :param wordlist: Wordlist iterator.
    :type wordlist: WordList

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :returns: a set with urls.
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))

    if not wordlist:
        raise ValueError("Internal error!")

    m_new        = url_parts.copy() # Works with a copy
    m_return     = set()
    m_return_add = m_return.add
    m_filename   = m_new.filename
    for l_suffix in wordlist:

        # Format: index1.php
        m_new.filename = m_filename + str(l_suffix)
        m_return_add(m_new.url)

        # Format: index_1.php
        m_new.filename = "%s_%s" % (m_filename, l_suffix)
        m_return_add(m_new.url)

    return m_return


#----------------------------------------------------------------------
def make_url_mutate_filename(url_parts):
    """
    Creates a set of URLs with mutated filenames.

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :return: a set with URLs
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))

    # Change extension to upper case
    m_new                = url_parts.copy()
    m_new.all_extensions = m_new.all_extensions.upper()
    m_return             = set()
    m_return_add         = m_return.add

    m_return_add(m_new.url)

    # Adding numeric ends of filename
    m_new = url_parts.copy()
    filename = m_new.filename
    for n in xrange(5):

        # Format: index1.php
        m_new.filename = filename + str(n)
        m_return_add(m_new.url)

        # Format: index_1.php
        m_new.filename = "%s_%s" % (filename, str(n))
        m_return_add(m_new.url)

    return m_return


#----------------------------------------------------------------------
def make_url_changing_folder_name(url_parts):
    """
    Creates a set of URLs with prefixes.

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :returns: a set with urls.
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))


    # Making predictables
    m_new        = url_parts.copy()
    m_return     = set()
    m_return_add = m_return.add
    m_directory  = m_new.directory

    if len(m_directory.split("/")) > 1:
        for n in xrange(20):
            m_new.directory = "%s%s" % (m_directory, str(n))
            m_return_add(m_new.url)

        return m_return
    else:
        return set()


#----------------------------------------------------------------------
def make_url_with_files_or_folder(wordlist, url_parts):
    """
    Creates a set of URLs with guessed files and subfolders.

    :param wordlist: Wordlist iterator.
    :type wordlist: WordList

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :return: a set with URLs
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))

    if not wordlist:
        raise ValueError("Internal error!")

    m_wordlist_predictable = wordlist['predictable_files']
    if not m_wordlist_predictable:
        m_wordlist_predictable = set()
    m_wordlist_suffix = wordlist['suffixes']
    if not m_wordlist_suffix:
        m_wordlist_suffix = set()

    # Making predictables
    m_new        = url_parts.copy()
    m_return     = set()
    m_return_add = m_return.add
    for l_wordlist in m_wordlist_predictable:
        # For errors
        if not l_wordlist:
            Logger.log_error("Can't load wordlist for category: 'predictable_files'.")
            continue

        for l_path in l_wordlist:

            # Delete wordlist comment lines
            if l_path.startswith("#"):
                continue

            # Fix l_path
            l_fixed_path = l_path[1:] if l_path.startswith("/") else l_path

            m_new.filename = l_fixed_path
            m_return_add(m_new.url)

    # For locations source code of application, like:
    # www.site.com/folder/app1/ -> www.site.com/folder/app1.war
    #
    m_new = url_parts.copy()
    m_path = m_new.directory
    if m_path.endswith('/'):
        m_path = m_path[:-1]
    for l_wordlist in m_wordlist_suffix:
        # For errors
        if not l_wordlist:
            Logger.log_error("Can't load wordlist for category: 'suffixes'.")
            continue
        for l_suffix in l_wordlist:
            m_new.path = m_path + l_suffix
            m_return_add(m_new.url)

    return m_return


#----------------------------------------------------------------------
def make_url_changing_extensions(wordlist, url_parts):
    """
    Creates a set of URLs with alternative file extensions.

    :param wordlist: Wordlist iterator.
    :type wordlist: WordList

    :param url_parts: Parsed URL to mutate.
    :type url_parts: ParsedURL

    :return: a set with the URLs
    :rtype: set
    """

    if not isinstance(url_parts, ParsedURL):
        raise TypeError("Expected ParsedURL, got %s instead" % type(url_parts))

    if not wordlist:
        raise ValueError("Internal error!")

    # Making predictables
    m_new        = url_parts.copy()
    m_return     = set()
    m_return_add = m_return.add
    for l_suffix in wordlist:
        m_new.all_extensions = l_suffix
        m_return_add(m_new.url)

    return m_return


#----------------------------------------------------------------------
def is_folder_url(url_parts):
    """
    Determine if the given URL points to a folder or a file:

    if URL looks like:
    - www.site.com/
    - www.site.com

    then ==> Return True

    if URL looks like:
    - www.site.com/index.php
    - www.site.com/index.php?id=1&name=bb
    - www.site.com/index.php/id=1&name=bb

    then ==> Return False

    :param url_parts: Parsed URL to test.
    :type url_parts: ParsedURL

    :return: True if it's a folder, False otherwise.
    :rtype: bool
    """
    return url_parts.path.endswith('/') and not url_parts.query_char == '/'


#----------------------------------------------------------------------
def get_list_from_wordlist(wordlist):
    """
    Load the content of the wordlist and return a set with the content.

    :param wordlist: wordlist name.
    :type wordlist: str

    :return: a set with the results.
    :rtype result_output: set
    """

    try:
        m_commom_wordlists = set()

        for v in Config.plugin_extra_config[wordlist].itervalues():
            m_commom_wordlists.update(WordListLoader.get_advanced_wordlist_as_list(v))

        return m_commom_wordlists
    except KeyError,e:
        Logger.log_error_more_verbose(str(e))
        return set()
