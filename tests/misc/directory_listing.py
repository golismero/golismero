#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from golismero.api.data.resource.url import FolderUrl, Url

# - Vulnerability types:
# from golismero.api.data.vulnerability.information_disclosure.url_disclosure import UrlDisclosure

#from golismero.api.net.protocol import NetworkAPI
from golismero.api.plugin import TestingPlugin


#----------------------------------------------------------------------
class DirectoryListingPlugin(TestingPlugin):
    """
    This plugin detect and try to discover directory listing in folders and Urls.
    """


    #----------------------------------------------------------------------
    def get_accepted_info(self):

        return [FolderUrl, Url]


    #----------------------------------------------------------------------
    def recv_info(self, info):

        # XXX TO DO
        pass


#------------------------------------------------------------------------------
# Examples of directory listings for the most popular web servers.

DATA = {

'PWS':

"""<html>
    <head><title>Index of /</title></head>
    <body bgcolor="white">
    <h1>Index of /</h1><hr><pre><a href="../">../</a>""",

#------------------------------------------------------------------------------
'Apache 2.2':

"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
 <head>
  <title>Index of /</title>
 </head>
 <body>
<h1>Index of /</h1>
<ul><li><a href="daily-live/"> daily-live/</a></li>
<li><a href="daily-preinstalled/"> daily-preinstalled/</a></li>
<li><a href="edubuntu/"> edubuntu/</a></li>""",

#------------------------------------------------------------------------------
'Apache 2.2.16':

"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
 <head>
  <title>Index of /</title>
 </head>
 <body>
<h1>Index of /</h1>
<table><tr><th><img src="/icons/blank.gif" alt="[ICO]"></th><th><a href="?C=N;O=D">Name</a></th><th><a href="?C=M;O=A">Last modified</a></th><th><a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr><tr><th colspan="5"><hr></th></tr>
<tr><td valign="top"><img src="/icons/folder.gif" alt="[DIR]"></td><td><a href="3rd_Rock_From_the_Sun/">3rd_Rock_From_the_Sun/</a></td><td align="right">18-Oct-2009 10:15  </td><td align="right">  - </td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/layout.gif" alt="[   ]"></td><td><a href="10_Things_I_Hate_About_You_1x01_-_Pilot.pdf">10_Things_I_Hate_About_You_1x01_-_Pilot.pdf</a></td><td align="right">07-Nov-2009 13:52  </td><td align="right"> 95K</td><td>&nbsp;</td></tr>
<tr><td valign="top"><img src="/icons/folder.gif" alt="[""",

#------------------------------------------------------------------------------
'lighttpd/1.4.31':

"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>Index of /microsoft/</title>
<style type="text/css">
a, a:active {text-decoration: none; color: blue;}
a:visited {color: #48468F;}
a:hover, a:focus {text-decoration: underline; color: red;}
body {background-color: #F5F5F5;}
h2 {margin-bottom: 12px;}
table {margin-left: 12px;}
th, td { font: 90% monospace; text-align: left;}
th { font-weight: bold; padding-right: 14px; padding-bottom: 3px;}
td {padding-right: 14px;}
td.s, th.s {text-align: right;}
div.list { background-color: white; border-top: 1px solid #646464; border-bottom: 1px solid #646464; padding-top: 10px; padding-bottom: 14px;}
div.foot { font: 90% monospace; color: #787878; padding-top: 4px;}
</style>
</head>
<body>
<h2>Index of /microsoft/</h2>
<div class="list">
<table summary="Directory Listing" cellpadding="0" cellspacing="0">
<thead><tr><th class="n">Name</th><th class="m">Last Modified</th><th class="s">Size</th><th class="t">Type</th></tr></thead>
<tbody>
<tr><td class="n"><a href="../">Parent Directory</a>/</td><td class="m">&nbsp;</td><td class="s">- &nbsp;</td><td class="t">Directory</td></tr>
<tr><td class="n"><a href="6.0.6001.18000.367-KRMSDK_EN.iso">6.0.6001.18000.367-KRMSDK_EN.iso</a></td><td class="m">2010-Apr-20 11:46:33</td><td class="s">1.3G</td><td class="t">application/octet-stream</td></tr>
<tr><td class="n"><a href="6001.18000.080118-1840-kb3aikl_en.iso">6001.18000.080118-1840-kb3aikl_en.iso</a></td><td class="m">2009-Jan-19 02:07:02</td><td class="s">1.3G</td><td class="t">application/octet-stream</td></tr>
<tr><td class="n"><a href="""

}
