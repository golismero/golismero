#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML document.
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

__all__ = ["HTML"]

from . import File
from .. import identity
from ...net.web_utils import HTMLParser
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class HTML(File):
    """
    HTML document.

    This object contains all of relevant tags of a HTML document:

    - title
    - links
    - forms
    - images
    - objects
    - metas
    - css_links
    - css_embedded
    - javascript_links

    Also contains a property to access all tags:

    - elements

    You can also get the raw HTML code.

    - raw_data

    .. note::
       The HTML parser used is internally selected on runtime,
       depends of your installed libraries.

    Example:

        >>> from golismero.api.data.information.html import HTML
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
        >>> html_parsed = HTML(html_info)
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

        # Parent constructor
        super(HTML, self).__init__()


    #--------------------------------------------------------------------------
    @property
    def display_name(self):
        return "HTML Content"


    #--------------------------------------------------------------------------
    @identity
    def raw_data(self):
        """
        :return: Raw HTML content.
        :rtype: str
        """
        return self.__raw_data


    #--------------------------------------------------------------------------
    @property
    def elements(self):
        """
        :return: All HTML elements.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).elements


    #--------------------------------------------------------------------------
    @property
    def forms(self):
        """
        :return: HTML form tags.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).forms


    #--------------------------------------------------------------------------
    @property
    def images(self):
        """
        :return: Image tags.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).images


    #--------------------------------------------------------------------------
    @property
    def url_links(self):
        """
        :return: Link tags.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).url_links


    #--------------------------------------------------------------------------
    @property
    def css_links(self):
        """
        :return: CSS links.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).css_links


    #--------------------------------------------------------------------------
    @property
    def javascript_links(self):
        """
        :return: JavaScript links.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).javascript_links


    #--------------------------------------------------------------------------
    @property
    def css_embedded(self):
        """
        :return: Embedded CSS.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).css_embedded


    #--------------------------------------------------------------------------
    @property
    def javascript_embedded(self):
        """
        :return: Embedded JavaScript.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).javascript_embedded


    #--------------------------------------------------------------------------
    @property
    def metas(self):
        """
        :return: Meta tags.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).metas


    #--------------------------------------------------------------------------
    @property
    def title(self):
        """
        :return: Document title.
        :rtype: HTMLElement
        """
        return HTMLParser(self.raw_data).title


    #--------------------------------------------------------------------------
    @property
    def objects(self):
        """
        :return: Object tags.
        :rtype: list(HTMLElement)
        """
        return HTMLParser(self.raw_data).objects
