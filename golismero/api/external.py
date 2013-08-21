#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
External tools API.
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

__all__ = ["run_external_tool", "win_to_cygwin_path", "cygwin_to_win_path"]

import ntpath
import subprocess

# TODO: Use pexpect to run tools interactively.


#------------------------------------------------------------------------------
def run_external_tool(command, args = None, env = None):
    """
    Run an external tool and fetch the output.

    Standard and error output are combined.

    .. warning: SECURITY WARNING: Be *extremely* careful when passing
                data coming from the target servers to this function.
                Failure to properly validate the data may result in
                complete compromise of your machine! See:
                https://www.owasp.org/index.php/Command_Injection

    :param command: Command to execute.
    :type command: str

    :param args: Arguments to be passed to the command.
    :type args: list(str)

    :param env: Environment variables to be passed to the command.
    :type env: dict(str -> str)

    :returns: Output from the tool and the exit status code.
    :rtype: tuple(str, int)
    """
    #
    # We put a large and nasty security warning here mostly to scare the noobs,
    # because subprocess is generally safe when you don't run in "shell" mode
    # nor invoke bash directly - i.e. when you know what the hell you're doing.
    #
    # Still, especially on Windows, some external programs are really stupid
    # when it comes to parsing their own command line, so caveat emptor.
    #
    if not args:
        args = []
    else:
        args = list(args)
    args.insert(0, command)
    try:
        code   = 0
        output = subprocess.check_output(args, executable = command, env = env)
    except subprocess.CalledProcessError, e:
        code   = e.returncode
        output = e.output
    return output, code


#------------------------------------------------------------------------------
def win_to_cygwin_path(path):
    """
    Converts a Windows path to a Cygwin path.

    :param path: Windows path to convert.
        Must be an absolute path.
    :type path: str

    :returns: Cygwin path.
    :rtype: str

    :raises ValueError: Cannot convert the path.
    """
    drive, path = ntpath.splitdrive(path)
    if not drive:
        raise ValueError("Not an absolute path!")
    t = { "\\": "/", "/": "\\/" }
    path = "".join( t.get(c, c) for c in path )
    return "/cygdrive/%s%s" % (drive[0].lower(), path)


#------------------------------------------------------------------------------
def cygwin_to_win_path(path):
    """
    Converts a Cygwin path to a Windows path.
    Only paths starting with "/cygdrive/" can be converted.

    :param path: Cygwin path to convert.
        Must be an absolute path.
    :type path: str

    :returns: Windows path.
    :rtype: str

    :raises ValueError: Cannot convert the path.
    """
    if not path.startswith("/cygdrive/"):
        raise ValueError(
            "Only paths starting with \"/cygdrive/\" can be converted.")
    drive = path[10].upper()
    path = path[11:]
    i = 0
    r = []
    while i < len(path):
        c = path[i]
        if c == "\\":
            r.append( path[i+1:i+2] )
            i += 2
            continue
        if c == "/":
            c = "\\"
        r.append(c)
        i += 1
    path = "".join(r)
    return "%s:%s" % (drive, path)
