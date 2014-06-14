#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Local file API.
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

__all__ = ["LocalFile"]  # More symbols added later, see the end of the file!

from .config import Config
from .logger import Logger
from ..common import Singleton, export_methods_as_functions

from os import path, listdir, walk

import tempfile


#------------------------------------------------------------------------------
class _LocalFile (Singleton):
    """
    Local file API.
    """


    #--------------------------------------------------------------------------
    def __init__(self):
        self.__plugin_path = None


    #--------------------------------------------------------------------------
    def _update_plugin_path(self):
        """
        Updates the plugin path using the current configuration.
        Called automatically by the plugin bootstrap routine.

        .. warning: Internally used by GoLismero, do not call!
        """

        # Despite what the docs say, what this actually does is
        # clear the cache, so the next time the path is requested
        # it's calculated. That way we don't spend time doing stuff
        # that may not even be needed later.
        self.__plugin_path = None


    #--------------------------------------------------------------------------
    @property
    def plugin_path(self):
        """
        :returns: Path to the current plugin's private data files.
        :rtype: str
        """

        # Return the cached value.
        if self.__plugin_path is not None:
            return self.__plugin_path

        # Try to use the location of the plugin module file as the plugin path.
        plugin_path = path.abspath(Config.plugin_info.plugin_module)
        if path.isdir(plugin_path):
            plugin_path = path.join(plugin_path, "__init__.py")
        if not plugin_path.endswith(".py"):
            plugin_path += ".py"
        plugin_path = path.split(plugin_path)[0]

        # If that fails for some reason,
        # use the location of the config file instead.
        if not path.exists(plugin_path):
            plugin_path = path.abspath(Config.plugin_info.plugin_descriptor)
            plugin_path = path.split(plugin_path)[0]

            # If that fails too, log the error and use the tmp folder.
            if not path.exists(plugin_path):
                name = Config.plugin_info.plugin_class
                if not name:
                    name = Config.plugin_info.display_name
                msg = "[%s] Cannot determine the plugin's path!"
                Logger.log_error(msg % name)
                plugin_path = tempfile.gettempdir()

        # Cache the plugin path.
        self.__plugin_path = plugin_path

        # Return the plugin path.
        return self.__plugin_path


    #--------------------------------------------------------------------------
    def __sanitize(self, pathname):
        """
        Makes sure the given pathname lies within the plugin folder.
        Also makes it an absolute pathname.

        .. warning: Internally used by GoLismero, do not call!
        """

        # Absolute pathnames are not allowed.
        if path.isabs(pathname):
            msg = "Absolute pathnames are not allowed: %r"
            raise ValueError(msg % pathname)

        # Turn the pathname into a local pathname within the plugin folder.
        pathname = path.join(self.plugin_path, pathname)
        pathname = path.abspath(pathname)
        if not pathname.startswith(self.plugin_path):
            msg = "Pathname may not be outside the plugin folder: %r"
            raise ValueError(msg % self.plugin_path)

        # Return the sanitized pathname.
        return pathname


    #--------------------------------------------------------------------------
    def open_tmp_file(self):
        """
        Open a new temporary file. Temporary files have random names and are
        automatically deleted after they're closed.

        :returns: A tuple containing the open file and its pathname.
        :rtype: (file, str)
        """
        fd = tempfile.NamedTemporaryFile()
        return fd, fd.name


    #--------------------------------------------------------------------------
    def open(self, filename, mode = "rb"):
        """
        Open a local file in the plugin's folder.

        This method can be used by plugins that contain additional files and
        resources besides they .py with the source code.

        :param filename: Name of the file to open.
        :type filename: str

        :param mode: Open mode. Same flags as in Python's built-in open().
        :type mode: str

        :returns: File object.
        :rtype: file
        """

        # Sanitize the filename.
        filename = self.__sanitize(filename)

        # Open the file and return the file object.
        return open(filename, mode)


    #--------------------------------------------------------------------------
    def exists(self, filename):
        """
        Determine if the given file exists within the plugin folder.

        :param filename: Name of the file to test.
        :type filename: str

        :returns: True if the file exists, False otherwise.
        :rtype: bool
        """
        if filename is None:
            return False
        if not filename:
            return False

        # Sanitize the filename.
        filename = self.__sanitize(filename)

        # Test the filename.
        return path.exists(filename)


    #--------------------------------------------------------------------------
    def isfile(self, filename):
        """
        Determine if the given filename points to an existing file
        within the plugin folder.

        :param filename: Name of the file to test.
        :type filename: str

        :returns: True if the file exists,
                  False if it doesn't or is not a file.
        :rtype: bool
        """

        # Sanitize the filename.
        filename = self.__sanitize(filename)

        # Test the filename.
        return path.isfile(filename)


    #--------------------------------------------------------------------------
    def isdir(self, filename):
        """
        Determine if the given filename points to an existing subfolder
        of the plugin folder.

        :param filename: Name of the folder to test.
        :type filename: str

        :returns: True if the folder exists,
                  False if it doesn't or is not a folder.
        :rtype: bool
        """

        # Sanitize the filename.
        filename = self.__sanitize(filename)

        # Test the filename.
        return path.isdir(filename)


    #--------------------------------------------------------------------------
    def samefile(self, f1, f2):
        """
        Determine if the two given filenames point to the same file
        within the plugin folder.

        :param f1: Name of the first file to test.
        :type f1: str

        :param f2: Name of the second file to test.
        :type f2: str

        :returns: True if the files are the same, False otherwise.
        :rtype: bool
        """

        # Sanitize the filenames.
        f1 = self.__sanitize(f1)
        f2 = self.__sanitize(f2)

        # Test the filenames.
        return path.samefile(f1, f2)


    #--------------------------------------------------------------------------
    def listdir(self, folder = "."):
        """
        List all files and folders within the plugin folder.

        :param folder: Optional subfolder name.
                       Defaults to the plugin folder itself.
        :type folder: str

        :returns: List of file and folder names.
        :rtype: list(str)
        """

        # Sanitize the folder.
        folder = self.__sanitize(folder)

        # List the folder contents and return them.
        return listdir(folder)


    #--------------------------------------------------------------------------
    def walk(self, folder = "."):
        """
        Recursively list all files and folders within the plugin folder.

        Works exactly like the standard os.walk() function.

        :param folder: Optional subfolder name.
                       Defaults to the plugin folder itself.
        :type folder: str

        :returns: Iterator of tuples containing the base path,
                  and the file and folder names.
        :rtype: iter
        """

        # Sanitize the folder.
        folder = self.__sanitize(folder)

        # List the folder contents and yield them,
        # fixing the base path to make it relative.
        p = len(self.plugin_path)
        if not self.plugin_path.endswith(path.sep):
            p += 1
        for basepath, directories, files in walk(folder):
            basepath = basepath[p:]
            yield basepath, directories, files


#------------------------------------------------------------------------------

# Instance the singleton.
LocalFile = _LocalFile()

# Export the singleton's methods as bare functions.
export_methods_as_functions(LocalFile, __name__)
