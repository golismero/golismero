#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""GoLISMERO - Simple web analisis
Copyright (C) 2011-2012 Daniel Garcia dani@estotengoqueprobarlo.es
Written by: Henri Salo <henri@nerv.fi>

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

# For golismero / garcia daniel as a first step to get rid of symlink-problems

try:
    import sys
    import git
    import httplib
except ImportError, e:
    sys.exit(e)


# FQDN of SCM
scm_url = 'code.google.com'
# Location of project in FQDN
scm_url_location = '/p/golismero/'


def check_scm_url_aliveness(scm_url, scm_url_location):
    """Does a verification if URL is alive. Please note that HTTPS certification is not validated. Returns True if alive and False if not."""
    if not scm_url and scm_url_location:
        print 'Error. Not all parameters defined in check_scm_url_aliveness.'
        return
    print('Testing for URL aliveness: %s' % 'https://' + scm_url + scm_url_location)
    conn = httplib.HTTPSConnection(scm_url)
    conn.request('GET', scm_url_location)
    res = conn.getresponse()
    if res.status == int('200'):
        print('URL alive: %s' % 'https://' + scm_url + scm_url_location)
        return True
    else:
        """HTTP-error codes that at least should be checked here: 4xx, 5xx
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        """
        print('URL not alive: %s' % 'https://' + scm_url + scm_url_location)
        return False


def update_git_repo(scm_url, scm_url_location):
    """Calls URL verification and updates a GIT-repo."""
    if not scm_url and scm_url_location:
        print 'Error. Not all parameters defined in check_scm_url_aliveness.'
        return
    if not check_scm_url_aliveness(scm_url, scm_url_location):
        print 'Update failed as URL did not return error code 200.'
        return
    full_url = scm_url + scm_url_location
    print 'Updating from URL: %s' % 'https://' + full_url
    git.Git().checkout(force=True)


def update():
    update_git_repo(scm_url, scm_url_location)
