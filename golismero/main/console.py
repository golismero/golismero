#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Console output.
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

__all__ = ["Console",
           "colorize", "colorize_traceback", "colorize_substring",
           "get_terminal_size"]

from ..api.logger import Logger

# Do not use the "from sys import" form, or coloring won't work on Windows.
import sys

import atexit
import os.path

from colorizer import colored
from warnings import warn


#------------------------------------------------------------------------------
# Map of colors

# Color names mapped to themselves.
m_colors = {
    None        : None,
    'blue'      : 'blue',
    'green'     : 'green',
    'cyan'      : 'cyan',
    'magenta'   : 'magenta',
    'grey'      : 'grey',
    'gray'      : 'grey',  # tomayto, tomahto...
    'red'       : 'red',
    'yellow'    : 'yellow',
    'white'     : 'white',

    # String log levels to color names.
    'informational' : 'blue',
    'low'           : 'cyan',
    'middle'        : None,
    'high'          : 'magenta',
    'critical'      : 'red',

    # Integer log levels to color names.
    0 : 'blue',
    1 : 'cyan',
    2 : None,
    3 : 'red',
    4 : 'yellow',
}

# Colors that need an increase in brightness.
m_make_brighter = ['blue', 'grey', 'red']


#------------------------------------------------------------------------------
def colorize_substring(text, substring, level_or_color):
    """
    Colorize a substring within a text to be displayed on the console.

    :param text: Full text.
    :type text: str

    :param substring: Text to find and colorize.
    :type substring: str

    :param level_or_color:
        Color name or risk level name.
        See the documentation for colorize() for more details.
    :type level_or_color: str

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
            m_content = colorize(m_content, level_or_color)
            text = "%s%s%s" % (m_prefix, m_content, m_suffix)

            # Update the current position and keep searching.
            m_pos = len(m_prefix) + len(m_content)

    # Return the patched text.
    return text


#------------------------------------------------------------------------------
def colorize(text, level_or_color):
    """
    Colorize a text to be displayed on the console.

    The following color names may be used:

     - Blue
     - Cyan
     - Green
     - Grey (or gray)
     - Magenta
     - Red
     - Yellow
     - White

    The following risk levels may be used in lieu of colors:

     - Informational (0)
     - Low (1)
     - Middle (2)
     - High (3)
     - Critical (4)

    :param text: Text to colorize.
    :type text: str

    :param level_or_color: Color name or risk level name.
    :type level_or_color: str

    :returns: Colorized text.
    :rtype: str
    """

    # Check if colors are enabled.
    if Console.use_colors:

        # Parse the color name or level into
        # a color value that colored() expects.
        try:
            level_or_color = level_or_color.lower()
        except AttributeError:
            pass
        color = m_colors[level_or_color]

        # Colorize the text.
        if color:
            if color in m_make_brighter:
                text = colored(text, color, attrs=["bold"])
            else:
                text = colored(text, color)

    # Return the text.
    return text


#------------------------------------------------------------------------------
def colorize_traceback(traceback):
    """
    Colorize a Python traceback to be displayed on the console.

    :param traceback: Traceback to colorize.
    :type traceback: str

    :returns: Colorized traceback.
    :rtype: str
    """
    if not traceback or not traceback.startswith(
            "Traceback (most recent call last):"):
        return traceback
    try:
        lines = traceback.split("\n")
        assert lines[-1] == ""
        exc_line = lines[-2]
        p = exc_line.find(":")
        if p > 0:
            lines[-2] = "%s: %s" % (
                colorize(exc_line[:p], "red"), exc_line[p+2:])
        else:
            lines[-2] = colorize(exc_line, "red")
        for i in xrange(1, len(lines) - 2, 2):
            file_line = lines[i]
            assert file_line.startswith("  File \""), repr(file_line)
            p = 8
            q = file_line.find('"', p)
            assert q > p, (p, q)
            filename = file_line[p:q]
            r = q + 8
            assert file_line[q:r] == "\", line ", (q, r, file_line[q:r])
            s = file_line.find(",", r)
            line_num = int(file_line[r:s])
            t = s + 5
            assert file_line[s:t] == ", in ", (s, t, file_line[s:t])
            function = file_line[t:]
            filename = os.path.join(
                os.path.dirname(filename),
                colorize(os.path.basename(filename), "cyan"))
            line_num = colorize(str(line_num), "cyan")
            function = colorize(function, "cyan")
            lines[i] = "  File \"%s\", line %s, in %s" % \
                       (filename, line_num, function)
            lines[i + 1] = colorize(lines[i + 1], "yellow")
        return "\n".join(lines)
    except Exception, e:
        warn(str(e), RuntimeWarning)
        return traceback


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
    Console output wrapper.
    """


    #--------------------------------------------------------------------------
    # Verbose levels.

    DISABLED     = Logger.DISABLED
    MINIMAL      = Logger.MINIMAL
    VERBOSE      = Logger.VERBOSE
    MORE_VERBOSE = Logger.MORE_VERBOSE

    # Current verbose level.
    level = VERBOSE

    # Use colors?
    use_colors = True


    #--------------------------------------------------------------------------
    @classmethod
    def _display(cls, message):
        """
        Write a message to standard output.

        :param message: message to write
        :type message: str
        """
        try:
            ##if sys.platform in ("win32", "cygwin"):
            ##    message = message.decode("utf-8").encode("latin-1")
            sys.stdout.write("%s\n" % (message,))
            sys.stdout.flush()
        except Exception,e:
            print "[!] Error while writing to output console: %s" % str(e)


    #--------------------------------------------------------------------------
    @classmethod
    def display(cls, message):
        """
        Write a message to standard output, as long as the current log level
        is at least MINIMAL.

        :param message: message to write
        :type message: str
        """
        if  cls.level >= cls.MINIMAL:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_verbose(cls, message):
        """
        Write a message to standard output, as long as the current log level
        is at least VERBOSE.

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.VERBOSE:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_more_verbose(cls, message):
        """
        Write a message to standard output, as long as the current log level
        is at least MORE_VERBOSE.

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.MORE_VERBOSE:
            cls._display(message)


    #--------------------------------------------------------------------------
    @classmethod
    def _display_error(cls, message):
        """
        Write a message to standard error.

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
        Write a message to standard error, as long as the current log level
        is at least MINIMAL.

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.MINIMAL:
            cls._display_error(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_error_verbose(cls, message):
        """
        Write a message to standard error, as long as the current log level
        is at least VERBOSE.

        :param message: message to write
        :type message: str
        """
        if cls.level >= cls.VERBOSE:
            cls._display_error(message)


    #--------------------------------------------------------------------------
    @classmethod
    def display_error_more_verbose(cls, message):
        """
        Write a message to standard error, as long as the current log level
        is at least MORE_VERBOSE.

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
        try:
            if cls.use_colors:
                sys.stdout.write( colored("") )
        except:
            pass


#------------------------------------------------------------------------------
# Register the atexit hook to restore the console.
atexit.register(Console._atexit_restore_console)
