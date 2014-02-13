#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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

__all__ = ["Families", "Plugin"]

from standalone import models


#------------------------------------------------------------------------------
class Families(models.StandaloneModel):
    family_name      = models.CharField(max_length=250, primary_key=True)


#------------------------------------------------------------------------------
class Plugin(models.StandaloneModel):
    #plugin_name      = models.CharField(max_length=250)
    plugin_id        = models.BigIntegerField(max_length=250, primary_key=True)
    plugin_file_name = models.CharField(max_length=255)

    family           = models.ForeignKey(Families)
