#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plain text data.
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

__all__ = ["Text"]

from .binary import Binary
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class Text(Binary):
    """
    Plain text data.
    """


    #--------------------------------------------------------------------------
    def __init__(self, data, content_type = "text/plain"):
        super(Text, self).__init__(to_utf8(data), content_type)
