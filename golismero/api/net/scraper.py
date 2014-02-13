#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
URL scraping API.

This module contains utility functions to extract (scrape) URLs from data.
Currently only HTML and plain text data are supported.
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

    # Generic entry point.
    "extract",

    # Specific parsers for each data format.
    "extract_from_text",
    "extract_from_html",

    # Helper functions.
    "is_link",
]

from .web_utils import parse_url, urldefrag, urljoin

from BeautifulSoup import BeautifulSoup
from warnings import warn

import re
from codecs import decode
from chardet import detect


#------------------------------------------------------------------------------
# URL detection regex, by John Gruber.
# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
_re_url_readable = re.compile(r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""", re.I)


#------------------------------------------------------------------------------
# Wrappers for URIs in plain text
# http://www.w3.org/Addressing/URL/url-spec.txt
_re_url_rfc = re.compile(r"""\\<([^\\>]+\\:\\/\\/[^\\>]+)\\>""", re.I)


#------------------------------------------------------------------------------
def is_link(url, base_url):
    """
    Determines if an URL is a link to another resource.

    :param url: URL to test.
    :type url: str

    :param base_url: Base URL for the current document.
        Must not contain a fragment.
    :type base_url: str

    :returns: True if the URL points to another page or resource,
        False otherwise.
    :rtype: bool
    """
    try:

        # Parse the URL. If it can't be parsed, it's not a link.
        parsed = parse_url(url, base_url)

        # URLs that point to the same page
        # in a different fragment are not links.
        parsed.fragment = ""
        if parsed.url == base_url:
            return False

        # All other URLs are links.
        return True

    # On any parsing error assume it's not a link.
    except Exception:
        return False


#------------------------------------------------------------------------------
def extract_from_text(text, base_url = None, only_links = True):
    """
    Extract URLs from text.

    Implementation notes:

    - Unicode URLs are currently not supported.

    :param text: Text.
    :type text: str

    :param base_url: Base URL for the current document.
        If not specified, relative URLs are ignored.
    :type base_url: str

    :param only_links: If True, only extract links to other resources.
        If False, extract all URLs.
    :type only_links: bool

    :returns: Extracted URLs.
    :rtype: set(str)
    """

    # Trivial case.
    if not text:
        return set()

    # Check the type.
    if not isinstance(text, basestring):
        raise TypeError("Expected string, got %r instead" % type(text))

    # Set where the URLs will be collected.
    result = set()
    add_result = result.add

    # Remove the fragment from the base URL.
    if base_url:
        base_url = urldefrag(base_url)[0]

    # Look for URLs using regular expressions.
    for regex in (_re_url_rfc, _re_url_readable):
        for url in regex.findall(text):
            url = url[0]

            # XXX FIXME
            # Make sure the text is really ASCII text.
            # We don't support Unicode yet.
            try:
                url = str(url)
            except Exception:
                warn("Unicode URLs not yet supported: %r" % url)
                continue

            # If a base URL was given...
            if base_url:

                # Canonicalize the URL.
                # Discard it on parse error.
                try:
                    url = urljoin(base_url, url.strip())
                except Exception:
                    continue

                # Discard URLs that are not links to other pages or resources.
                if only_links and not is_link(url, base_url = base_url):
                    continue

            # If a base URL was NOT given...
            else:

                # Discard relative URLs.
                # Also discard it on parse error.
                try:
                    parsed = parse_url(url)
                    if not parsed.scheme or not parsed.netloc:
                        continue
                except Exception:
                    continue

            # Add the URL to the set.
            add_result(url)

    # Return the set of collected URLs.
    return result


#------------------------------------------------------------------------------
def extract_forms_from_html(raw_html, base_url):
    """
    Extract forms info from HTML.

    :param raw_html: Raw HTML data.
    :type raw_html: str

    :param base_url: Base URL for the current document.
    :type base_url: str

    :returns: Extracted form info.
    :rtype: list((URL, METHOD, list({ "name" : PARAM_NAME, "value" : PARAM_VALUE, "type" : PARAM_TYPE})))
    """

    # Set where the URLs will be collected.
    result = list()
    result_append = result.append

    # Remove the fragment from the base URL.
    base_url = urldefrag(base_url)[0]

    # Parse the raw HTML.
    bs = BeautifulSoup(decode(raw_html, detect(raw_html)["encoding"]))

    for form in bs.findAll("form"):
        target = form.get("action", None)
        method = form.get("method", "POST").upper()

        if not target:
            continue

        try:
            target = str(target)
        except Exception:
            warn("Unicode URLs not yet supported: %r" % target)
            continue

        # Canonicalize the URL.
        try:
            target = urljoin(base_url, target.strip())
        except Exception:
            continue

        form_params = []
        form_params_append = form_params.append
        for params in form.findAll("input"):
            if params.get("type") == "submit":
                continue

            form_params_append({
                "name": params.get("name", "NAME"),
                "value": params.get("value", "VALUE"),
                "type": params.get("type", "TYPE")})

        # Add to results
        result_append((target, method, form_params))

    return  result


#------------------------------------------------------------------------------
def extract_from_html(raw_html, base_url, only_links = True):
    """
    Extract URLs from HTML.

    Implementation notes:

    - The current implementation is fault tolerant, meaning it will try
      to extract URLs even if the HTML is malformed and browsers wouldn't
      normally see those links. This may therefore result in some false
      positives.

    - HTML5 tags are supported, including tags not currently supported by
      any major browser.

    :param raw_html: Raw HTML data.
    :type raw_html: str

    :param base_url: Base URL for the current document.
    :type base_url: str

    :param only_links: If True, only extract links to other resources.
        If False, extract all URLs.
    :type only_links: bool

    :returns: Extracted URLs.
    :rtype: set(str)
    """

    # Set where the URLs will be collected.
    result = set()
    add_result = result.add

    # Remove the fragment from the base URL.
    base_url = urldefrag(base_url)[0]

    # Parse the raw HTML.
    bs = BeautifulSoup(decode(raw_html, detect(raw_html)["encoding"]),
                       convertEntities = BeautifulSoup.ALL_ENTITIES)

    # Some sets of tags and attributes to look for.
    href_tags = {"a", "link", "area"}
    src_tags = {"script", "img", "iframe", "frame", "embed", "source", "track"}
    param_names = {"movie", "href", "link", "src", "url", "uri"}

    # Iterate once through all tags...
    for tag in bs.findAll():

        # Get the tag name, case insensitive.
        name = tag.name.lower()

        # Extract the URL from each tag that has one.
        url = None
        if name in href_tags:
            url = tag.get("href", None)
        elif name in src_tags:
            url = tag.get("src", None)
        elif name == "param":
            name = tag.get("name", "").lower().strip()
            if name in param_names:
                url = tag.get("value", None)
        ##elif name == "form":
        ##    url = tag.get("action", None)
        elif name == "object":
            url = tag.get("data", None)
        elif name == "applet":
            url = tag.get("code", None)
        elif name == "meta":
            name = tag.get("name", "").lower().strip()
            if name == "http-equiv":
                content = tag.get("content", "")
                p = content.find(";")
                if p >= 0:
                    url = content[ p + 1 : ]
        elif name == "base":
            url = tag.get("href", None)
            if url is not None:

                # XXX FIXME
                # Unicode URLs are not supported.
                try:
                    url = str(url)
                except Exception:
                    warn("Unicode URLs not yet supported: %r" % url)
                    continue

                # Update the base URL.
                try:
                    base_url = urljoin(base_url, url.strip(),
                                       allow_fragments = False)
                except Exception:
                    continue

        # If we found an URL in this tag...
        if url is not None:

            # XXX FIXME
            # Unicode URLs are not supported.
            try:
                url = str(url)
            except Exception:
                warn("Unicode URLs not yet supported: %r" % url)
                continue

            # Canonicalize the URL.
            try:
                url = urljoin(base_url, url.strip())
            except Exception:
                continue

            # Discard URLs that are not links to other pages or resources.
            if not only_links or is_link(url, base_url = base_url):

                # Add the URL to the set.
                add_result(url)

    # Return the set of collected URLs.
    return result


#------------------------------------------------------------------------------
def extract(raw_data, content_type, base_url, only_links = True):
    """
    Extract URLs from raw data.

    Implementation notes:

    - Unicode URLs are currently not supported.

    - The current implementation is fault tolerant, meaning it will try
      to extract URLs even if the HTML is malformed and browsers wouldn't
      normally see those links. This may therefore result in some false
      positives.

    - HTML5 tags are supported, including tags not currently supported by
      any major browser.

    :param raw_data: Raw data.
    :type raw_data: str

    :param content_type: MIME content type.
    :type content_type: str

    :param base_url: Base URL for the current document.
    :type base_url: str

    :param only_links: If True, only extract links to other resources.
        If False, extract all URLs.
    :type only_links: bool

    :returns: Extracted URLs.
    :rtype: set(str)
    """

    # Sanitize the content type.
    content_type = content_type.strip().lower()
    if ";" in content_type:
        content_type = content_type[ content_type.find(";") : ].strip()

    # HTML parser.
    if content_type == "text/html":
        urls = extract_from_html(raw_data, base_url, only_links)
        urls.update( extract_from_text(raw_data, base_url, only_links) )
        return urls

    # Generic plain text parser.
    if content_type.startswith("text/"):
        return extract_from_text(raw_data, base_url, only_links)

    # Unsupported content type.
    return set()
