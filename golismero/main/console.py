#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Console output.
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

__all__ = ["Console", "colorize", "colorize_substring", "get_terminal_size"]

from ..api.logger import Logger

# do not use the "from sys import" form, or coloring won't work on Windows
import sys

import atexit
import os.path

from colorizer import colored


#------------------------------------------------------------------------------
# Map of colors

# Color names mapped to themselves
m_colors = {
    'blue'      : 'blue',
    'green'     : 'green',
    'cyan'      : 'cyan',
    'magenta'   : 'magenta',
    'grey'      : 'grey',
    'red'       : 'red',
    'yellow'    : 'yellow',
    'white'     : 'white',
}

# Colors for the Windows console.
if os.path.sep == "\\":
    m_colors.update({

        # Fix "grey", it doesn't work on Windows
        'grey'      : 'white',

        # String log levels to color names
        'info'      : 'cyan',
        'low'       : 'green',
        'middle'    : 'white',
        'high'      : 'magenta',
        'critical'  : 'yellow',

        # Integer log levels to color names
        0           : 'cyan',
        1           : 'green',
        2           : 'white',
        3           : 'magenta',
        4           : 'yellow',
    })

# Colors for all other operating systems.
else:
    m_colors.update({

        # String log levels to color names
        'info'      : 'blue',
        'low'       : 'cyan',
        'middle'    : 'white',
        'high'      : 'red',
        'critical'  : 'yellow',

        # Integer log levels to color names
        0           : 'blue',
        1           : 'cyan',
        2           : 'white',
        3           : 'red',
        4           : 'yellow',
    })


#------------------------------------------------------------------------------
def colorize_substring(text, substring, level_or_color):
    """
    Colorize a substring in a text depending of the type of alert:
    - Information
    - Low
    - Middle
    - Hight
    - Critical

    :param text: Full text.
    :type text: str

    :param substring: Text to find and colorize.
    :type substring: str

    :param level_or_color: May be an integer with level (0-4) or string with values: info, low, middle, high, critical.
    :type level_or_color: int | str

    :returns: Colorized text.
    :rtype: str
    """

    #
    # XXX TODO:
    #
    # We also probably need to parse existing ANSI escape codes
    # to know what's the color of the surrounding text, otherwise
    # we'll only properly colorize substrings in non colored text.
    #
    # Maybe we can settle with this: indicate a color for the text
    # and a color for the substring. Should work in all situations
    # we _currently_ need to handle.
    #

    # Check for trivial cases.
    if text and substring and Console.use_colors:

        # Parse the color name or level into
        # a color value that colored() expects.
        try:
            level_or_color = level_or_color.lower()
        except AttributeError:
            pass
        color = m_colors[level_or_color]

        # Loop for each occurrence of the substring.
        m_pos = 0
        while 1:

            # Find the substring in the text.
            m_pos = text.find(substring, m_pos)

            # If not found, break out of the loop.
            if m_pos < 0:
                break

            # Split the text where the substring was found.
            m_prefix  = text[:m_pos]
            m_content = text[m_pos: m_pos + len(substring)]
            m_suffix  = text[m_pos + len(substring):]

            # Patch the text to colorize the substring.
            m_content = colored(m_content, color)
            text = "%s%s%s" % (m_prefix, m_content, m_suffix)

            # Update the current position and keep searching.
            m_pos = len(m_prefix) + len(m_content)

    # Return the patched text.
    return text


#------------------------------------------------------------------------------
def colorize(text, level_or_color):
    """
    Colorize a text depends of type of alert:
    - Information
    - Low
    - Middle
    - High
    - Critical

    :param text: text to colorize.
    :type text: int with level (0-4) or string with values: info, low, middle, high, critical.

    :param level_or_color: color name or integer with level selected.
    :type level_or_color: str or integer (0-4).

    :returns: str -- string with information to print.
    """
    if Console.use_colors:
        try:
            level_or_color = level_or_color.lower()
        except AttributeError:
            pass
        return colored(text, m_colors[level_or_color])
    else:
        return text


#------------------------------------------------------------------------------
# excerpt borrowed from: http://stackoverflow.com/a/6550596/426293

def get_terminal_size():
    import platform
    current_os = platform.system()
    tuple_xy=None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os == 'Linux' or current_os == 'Darwin' or  current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy

def _get_terminal_size_windows():
    res=None
    try:
        from ctypes import windll, create_string_buffer

        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
         left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None

def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        import subprocess
        proc=subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output=proc.communicate(input=None)
        cols=int(output[0])
        proc=subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        output=proc.communicate(input=None)
        rows=int(output[0])
        return (cols,rows)
    except:
        return None

def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            import os
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            import os
            env = os.environ
            cr = (env['LINES'], env['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])


#------------------------------------------------------------------------------
class Console (object):
    """
    Console I/O wrapper.
    """


    #--------------------------------------------------------------------------
    # Verbose levels

    DISABLED     = Logger.DISABLED
    STANDARD     = Logger.STANDARD
    VERBOSE      = Logger.VERBOSE
    MORE_VERBOSE = Logger.MORE_VERBOSE

    # Current verbose level
    level = STANDARD

    # Use colors?
    use_colors = True


    #--------------------------------------------------------------------------
    @classmethod
    def _display(cls, message):
        """
        Write a message into output

        :param message: message to write
        :type message: str
        """
        try:
            if message:
                sys.stdout.write("%s\n" % message)
                sys.stdout.flush()
        except Exception,e:
            print "[!] Error while writing to output onsole: %s" % str(e)


    #--------------------------------------------------------------------------
    @classmethod
    def display(cls, message):
        """
        Write a message into output

        :param message: message to write
        :type message: str
        """
        if  cls.level >= cls.STANDARD:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_verbose(cls, message):
        """
        Write a message into output with more verbosity

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.VERBOSE:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_more_verbose(cls, message):
        """
        Write a message into output with even more verbosity

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.MORE_VERBOSE:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def _display_error(cls, message):
        """
        Write a error message into output

        :param message: message to write
        :type message: str
        """
        try:
            if message:
                sys.stderr.write("%s\n" % message)
                sys.stderr.flush()
        except Exception,e:
            print "[!] Error while writing to error console: %s" % str(e)


    #--------------------------------------------------------------------------
    @classmethod
    def display_error(cls, message):
        """
        Write a error message into output

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.STANDARD:
            cls._display_error(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_error_verbose(cls, message):
        """
        Write a error message into output with more verbosity

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.VERBOSE:
            cls._display_error(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_error_more_verbose(cls, message):
        """
        Write a error message into output with more verbosity

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.MORE_VERBOSE:
            cls._display_error(message)


    #--------------------------------------------------------------------------
    @classmethod
    def _atexit_restore_console(cls):
        """
        This method is called automatically by an exit hook to restore the
        console colors before quitting.
        """
        if cls.use_colors:
            sys.stdout.write( colored("") )


#------------------------------------------------------------------------------
# Register the atexit hook to restore the console.
atexit.register(Console._atexit_restore_console)
