#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
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

import os

try:
    import cPickle as Pickle
except ImportError:
    import pickle as Pickle


#------------------------------------------------------------------------------

signatures = {

    'PWS': '^(<html>[\s]*<head><title>Index of /</title></head>[\s]*<body bgcolor="white">[\s]*<h1>Index of /[\/\-\w\_\;]*</h1><hr><pre>)',

    'Apache 2.2': '^(<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">[\s]*<html>[\s]*<head>[\s]*<title>Index of /[\/\-\w\_\;]*</title>[\s]*</head>[\s]*<body>[\s]*<h1>Index of /</h1>[\s]*<ul><li>)',

    'Apache 2.2.x': '^(<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">[\s]*<html>[\s]*<head>[\s]*<title>Index of /[\/\-\w\_\;]*</title>[\s]*</head>[\s]*<body>[\s]*<h1>Index of \/</h1>[\s]*<table><tr><th>)',

    'lighttpd/1.4.31': '^(<\?xml version="1.0" encoding="utf-8"\?>[\s]*<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">[\s]*<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">[\s]*<head>[\s]*<title>Index of /[\/\-\w\_\;]*</title>[\s]*<style type="text/css">[\s]*a, a:active {text-decoration: none; color: blue;}[\s]*a:visited {color: #48468F;}[\s]*a:hover, a:focus {text-decoration: underline; color: red;}[\s]*body {background-color: #F5F5F5;}[\s]*h2 {margin-bottom: 12px;}[\s]*table {margin-left: 12px;}[\s]*th, td { font: 90% monospace; text-align: left;}[\s]*th { font-weight: bold; padding-right: 14px; padding-bottom: 3px;}[\s]*td {padding-right: 14px;}[\s]*td.s, th.s {text-align: right;}[\s]*div.list { background-color: white; border-top: 1px solid #646464; border-bottom: 1px solid #646464; padding-top: 10px; padding-bottom: 14px;}[\s]*div.foot { font: 90% monospace; color: #787878; padding-top: 4px;}[\s]*</style>[\s]*</head>[\s]*<body>[\s]*<h2>Index of /microsoft/</h2>[\s]*<div class="list">[\s]*<table summary="Directory Listing" cellpadding="0" cellspacing="0">[\s]*<thead><tr><th class="n">Name</th><th class="m">Last Modified</th><th class="s">Size</th><th class="t">Type</th></tr></thead>[\s]*<tbody>)'

}


#-------------------------------------------------------------------------------
def main():
    signatures_file = os.path.join(os.path.split(__file__)[0], "signatures.dat")

    # Dump the info
    Pickle.dump(signatures, open(signatures_file, "wb"), protocol=2)

if __name__ == '__main__':
    main()
