#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Common constants, classes and functions used across GoLismero.
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

__all__ = [

    # Dynamically loaded modules, picks the fastest one available.
    "pickle", "random",

    # Helper functions.
    "get_user_settings_folder", "get_default_config_file",
    "get_profiles_folder", "get_profile", "get_available_profiles",

    # Helper classes and decorators.
    "Singleton", "decorator",

    # Configuration objects.
    "OrchestratorConfig", "AuditConfig"
]

# Load the fast C version of pickle,
# if not available use the pure-Python version.
try:
    import cPickle as pickle
except ImportError:
    import pickle

# Lazy import of the JSON codec.
json_decode = None
json_encode = None

# Import @decorator from the decorator module, if available.
# Otherwise define a simple but crude replacement.
try:
    from decorator import decorator
except ImportError:
    import functools
    def decorator(w):
        """
        The decorator module was not found. You can install it from:
        http://pypi.python.org/pypi/decorator/
        """
        def d(fn):
            @functools.wraps(fn)
            def x(*args, **kwargs):
                return w(fn, *args, **kwargs)
            return x
        return d

# Other imports.
from ConfigParser import RawConfigParser
from keyword import iskeyword
from os import path

import os
import random
import urlparse


#------------------------------------------------------------------------------
_user_settings_folder = None
def get_user_settings_folder():
    """
    Get the current user's GoLismero settings folder.

    This folder will be used to store the various caches
    and the user-defined plugins.

    :returns: GoLismero settings folder.
    :rtype: str
    """

    # TODO: on Windows, use the roaming data folder instead.

    # Return the cached value if available.
    global _user_settings_folder
    if _user_settings_folder:
        return _user_settings_folder

    # Get the user's home folder.
    home = os.getenv("HOME")              # Unix
    if not home:
        home = os.getenv("USERPROFILE")   # Windows

        # If all else fails, use the current directory.
        if not home:
            home = os.getcwd()

    # Get the user settings folder.
    folder = path.join(home, ".golismero")

    # Make sure it ends with a slash.
    if not folder.endswith(path.sep):
        folder += path.sep

    # Make sure it exists.
    try:
        os.makedirs(folder)
    except Exception:
        pass

    # Cache the folder.
    _user_settings_folder = folder

    # Return the folder.
    return folder


#------------------------------------------------------------------------------
def get_default_config_file():
    """
    :returns: Pathname of the default configuration file, or None if it doesn't exist.
    :rtype: str | None
    """
    config_file = path.join(get_user_settings_folder(), "golismero.conf")
    if not path.isfile(config_file):
        config_file = path.split(path.abspath(__file__))[0]
        config_file = path.join(config_file, "..", "golismero.conf")
        config_file = path.abspath(config_file)
        if not path.isfile(config_file):
            if path.sep != "\\" and path.isfile("/etc/golismero.conf"):
                config_file = "/etc/golismero.conf"
            else:
                config_file = None
    return config_file


#------------------------------------------------------------------------------
_wordlists_folder = None
def get_wordlists_folder():
    """
    :returns: Pathname of the wordlists folder.
    :rtype: str
    """
    global _wordlists_folder
    if not _wordlists_folder:
        pathname = path.split(path.abspath(__file__))[0]
        if pathname:
            pathname = path.join(pathname, "..")
        else:
            pathname = get_user_settings_folder()
        pathname = path.abspath(pathname)
        _wordlists_folder = path.join(pathname, "wordlist")
    return _wordlists_folder


#------------------------------------------------------------------------------
_profiles_folder = None
def get_profiles_folder():
    """
    :returns: Pathname of the profiles folder.
    :rtype: str
    """
    global _profiles_folder
    if not _profiles_folder:
        pathname = path.split(path.abspath(__file__))[0]
        if pathname:
            pathname = path.join(pathname, "..")
        else:
            pathname = get_user_settings_folder()
        pathname = path.abspath(pathname)
        _profiles_folder = path.join(pathname, "profiles")
    return _profiles_folder


#------------------------------------------------------------------------------
def get_profile(name):
    """
    Get the profile configuration file for the requested profile name.

    :param name: Name of the profile.
    :type name: str

    :returns: Pathname of the profile configuration file.
    :rtype: str

    :raises ValueError: The name was invalid, or the profile was not found.
    """

    # Trivial case.
    if not name:
        raise ValueError("No profile name given")

    # Get the profiles folder.
    profiles = get_profiles_folder()

    # Get the filename for the requested profile.
    filename = path.abspath(path.join(profiles, name + ".profile"))

    # Check if it's outside the profiles folder or it doesn't exist.
    if not profiles.endswith(path.sep):
        profiles += path.sep
    if not filename.startswith(profiles) or not path.isfile(filename):
        raise ValueError("Profile not found: %r" % name)

    # Return the filename.
    return filename


#------------------------------------------------------------------------------
def get_available_profiles():
    """
    :returns: Available profiles.
    :rtype: set(str)
    """
    profiles_folder = get_profiles_folder()
    if not profiles_folder or not path.isdir(profiles_folder):
        return set()
    return {
        name[:-4]
        for name in os.listdir(profiles_folder)
        if name.endswith(".profile")
    }


#------------------------------------------------------------------------------
class Singleton (object):
    """
    Implementation of the Singleton pattern.
    """

    # Variable where we keep the instance.
    _instance = None

    def __new__(cls):

        # If the singleton has already been instanced, return it.
        if cls._instance is not None:
            return cls._instance

        # Create the singleton's instance.
        cls._instance = super(Singleton, cls).__new__(cls)

        # Call the constructor.
        cls.__init__(cls._instance)

        # Delete the constructor so it won't be called again.
        cls._instance.__init__ = object.__init__
        cls.__init__ = object.__init__

        # Return the instance.
        return cls._instance


#------------------------------------------------------------------------------
class Configuration (object):
    """
    Generic configuration class.
    """

    #--------------------------------------------------------------------------
    # The logic in configuration classes is always:
    # - Checking options without fixing them is done in check_params().
    # - Sanitizing (fixing) options is done in parsers or in property setters.
    # - For each source, there's a "from_*" method. They add to the
    #   current options rather than overwriting them completely.
    #   This allows options to be read from multiple sources.

    #--------------------------------------------------------------------------
    # Here's where subclasses define the options.
    #
    # It's a dictionary of tuples of the following format:
    #
    #   name: ( parser, default )
    #
    # Where "name" is the option name, "parser" is an optional
    # callback to parse the input values, and "default" is an
    # optional default value.
    #
    # If no parser is given, the values are preserved when set.
    #
    # Example:
    #    class MySettings(Configuration):
    #        _settings_  = {
    #            "verbose": (int, 0), # A complete definition.
    #            "output_file": str,  # Omitting the default value (None is used).
    #            "data": None,        # Omitting the parser too.
    #        }
    #
    _settings_ = {}


    #--------------------------------------------------------------------------
    # Some helper parsers.

    @staticmethod
    def string(x):
        return str(x) if x is not None else None

    @staticmethod
    def integer(x):
        if type(x) in (int, long):
            return x
        return int(x, 0) if x else 0

    @staticmethod
    def integer_or_none(x):
        if x is None or (hasattr(x, "lower") and x in ("", "none", "inf", "infinite")):
            return None
        return Configuration.integer(x)

    @staticmethod
    def comma_separated_list(x):
        if not x:
            return []
        if isinstance(x, str):
            return [t.strip() for t in x.split(",")]
        if isinstance(x, unicode):
            return [t.strip() for t in x.split(u",")]
        return list(x)

    @staticmethod
    def boolean(x):
        if not x:
            return False
        if x is True:
            return x
        if hasattr(x, "lower"):
            return {
                "enabled": True,        # True
                "enable": True,
                "true": True,
                "yes": True,
                "y": True,
                "1": True,
                "disabled": False,      # False
                "disable": False,
                "false": False,
                "no": False,
                "f": False,
                "0": False,
            }.get(x.lower(), bool(x))
        return bool(x)

    @staticmethod
    def trinary(x):
        if x in (None, True, False):
            return x
        if not hasattr(x, "lower"):
            raise ValueError("Trinary values only accept True, False and None")
        try:
            return {
                "enabled": True,        # True
                "enable": True,
                "true": True,
                "yes": True,
                "y": True,
                "1": True,
                "disabled": False,      # False
                "disable": False,
                "false": False,
                "no": False,
                "f": False,
                "0": False,
                "default": None,        # None
                "def": None,
                "none": None,
                "maybe": None,
                "?": None,
                "-1": None,
            }[x.lower()]
        except KeyError:
            raise ValueError("Unknown value: %r" % x)


    #--------------------------------------------------------------------------
    def __init__(self):
        history = set()
        for name, definition in self._settings_.iteritems():
            if name in history:
                raise SyntaxError("Duplicated option name: %r" % name)
            history.add(name)
            if type(definition) not in (tuple, list):
                definition = (definition, None)
            self.__init_option(name, *definition)


    #--------------------------------------------------------------------------
    def __init_option(self, name, parser = None, default = None):
        if name.endswith("_") or not name.replace("_", "").isalnum():
            msg = "Option name %r is not a valid Python identifier"
            raise SyntaxError(msg % name)
        if iskeyword(name):
            msg = "Option name %r is a Python reserved keyword"
            raise SyntaxError(msg % name)
        if name.startswith("__"):
            msg = "Option name %r is a private Python identifier"
            raise SyntaxError(msg % name)
        if name.startswith("_"):
            msg = "Option name %r is a protected Python identifier"
            raise SyntaxError(msg % name)
        if parser is not None and not callable(parser):
            msg = "Option parser cannot be of type %s"
            raise SyntaxError(msg % type(parser))
        setattr(self, name, default)


    #--------------------------------------------------------------------------
    def __setattr__(self, name, value):
        if not name.startswith("_"):
            definition = self._settings_.get(name, (None, None))
            if type(definition) not in (tuple, list):
                definition = (definition, None)
            parser = definition[0]
            if parser is not None:
                value = parser(value)
        object.__setattr__(self, name, value)


    #--------------------------------------------------------------------------
    def check_params(self):
        """
        Check if parameters are valid. Raises an exception otherwise.

        This method only checks the validity of the arguments, it won't modify them.

        :raises ValueError: The parameters are incorrect.
        """
        return


    #--------------------------------------------------------------------------
    def from_dictionary(self, args):
        """
        Get the settings from a Python dictionary.

        :param args: Settings.
        :type args: dict(str -> \\*)
        """
        for name, value in args.iteritems():
            if name in self._settings_:
                setattr(self, name, value)


    #--------------------------------------------------------------------------
    def from_object(self, args):
        """
        Get the settings from the attributes of a Python object.

        :param args: Python object, for example the command line arguments parsed by argparse.
        :type args: object
        """

        # Builds a dictionary with the object's public attributes.
        args = { k : getattr(args, k) for k in dir(args) if not k.startswith("_") }

        # Remove all attributes whose values are None.
        args = { k:v for k,v in args.iteritems() if v is not None }

        # Extract the settings from the dictionary.
        self.from_dictionary(args)


    #--------------------------------------------------------------------------
    def from_json(self, json_raw_data):
        """
        Get the settings from a JSON encoded dictionary.

        :param json_raw_data: JSON raw data.
        :type json_raw_data: str
        """

        # Lazy import of the JSON decoder function.
        global json_decode
        if json_decode is None:
            try:
                # The fastest JSON parser available for Python.
                from cjson import decode as json_decode
            except ImportError:
                try:
                    # Faster than the built-in module, usually found.
                    from simplejson import loads as json_decode
                except ImportError:
                    # Built-in module since Python 2.6, very very slow!
                    from json import loads as json_decode

        # Converts the JSON data into a dictionary.
        args = json_decode(json_raw_data)
        if not isinstance(args, dict):
            raise TypeError("Invalid JSON data")

        # Extract the settings from the dictionary.
        self.from_dictionary(args)


    #--------------------------------------------------------------------------
    def from_config_file(self, config_file, allow_profile = False):
        """
        Get the settings from a configuration file.

        :param config_file: Configuration file.
        :type config_file: str

        :param allow_profile: True to allow reading the profile name
            from the config file, False to forbid it. Global config
            files should allow setting a default profile, but profile
            config files should not, as it wouldn't make sense.
        """
        parser = RawConfigParser()
        parser.read(config_file)
        options = { k:v for k,v in parser.items("golismero") if v }
        if "profile" in options:
            if allow_profile:
                self.profile = options["profile"]
                self.profile_file = get_profile(self.profile)
            else:
                del options["profile"]
        self.from_dictionary(options)


    #--------------------------------------------------------------------------
    def to_dictionary(self):
        """
        Copy the settings to a Python dictionary.

        :returns: Dictionary that maps the setting names to their values.
        :rtype: dict(str -> \\*)
        """
        result = {}
        for name, definition in self._settings_.iteritems():
            default = None
            if type(definition) in (tuple, list) and len(definition) > 1:
                default = definition[1]
            value = getattr(self, name, default)
            result[name] = value
        return result


    #--------------------------------------------------------------------------
    def to_json(self):
        """
        Copy the settings to a JSON encoded dictionary.

        :retruns: Settings as a JSON encoded dictionary.
        :rtype: str
        """

        # Lazy import of the JSON encoder function.
        global json_encode
        if json_encode is None:
            try:
                # The fastest JSON parser available for Python.
                from cjson import encode as json_encode
            except ImportError:
                try:
                    # Faster than the built-in module, usually found.
                    from simplejson import dumps as json_encode
                except ImportError:
                    # Built-in module since Python 2.6, very very slow!
                    from json import dumps as json_encode

        # Extract the settings to a dictionary and encode it with JSON.
        return json_encode( self.to_dictionary() )


#------------------------------------------------------------------------------
class OrchestratorConfig (Configuration):
    """
    Orchestator configuration object.
    """


    #--------------------------------------------------------------------------
    # The options definitions, they will be read from the config file:
    #
    _settings_ = {

        #
        # Main options
        #

        # UI mode
        "ui_mode": (str, "console"),

        # Verbosity level
        "verbose": (Configuration.integer, 2),

        # Colorize console?
        "colorize": (Configuration.boolean, True),

        #
        # Plugin options
        #

        # Enabled plugins
        "enable_plugins": (Configuration.comma_separated_list, ["all"]),

        # Disabled plugins
        "disable_plugins": (Configuration.comma_separated_list, []),

        # Plugins folder
        "plugins_folder": Configuration.string,

        # Maximum number of processes to execute plugins
        "max_process": (Configuration.integer, 4 if path.sep == "\\" else 20),

        #
        # Network options
        #

        # Maximum number of connections per host
        "max_connections": (Configuration.integer, 20),

        # Use persistent cache?
        "use_cache_db": (Configuration.boolean, True),
    }


    #--------------------------------------------------------------------------
    # Options that are only set in runtime, not loaded from the config file.

    # Configuration files.
    config_file  = get_default_config_file()
    profile      = None
    profile_file = None

    # Plugin arguments.
    plugin_args  = dict()   # plugin_name -> key -> value


    #--------------------------------------------------------------------------
    def check_params(self):

        # Validate the network connections limit.
        if self.max_connections < 1:
            raise ValueError("Number of connections must be greater than 0, got %i." % self.max_connections)

        # Validate the number of concurrent processes.
        if self.max_process < 0:
            raise ValueError("Number of processes cannot be a negative number, got %i." % self.max_process)

        # Validate the list of plugins.
        if not self.enable_plugins:
            raise ValueError("No plugins selected for execution.")
        if set(self.enable_plugins).intersection(self.disable_plugins):
            raise ValueError("Conflicting plugins selection, aborting execution.")


#------------------------------------------------------------------------------
class AuditConfig (Configuration):
    """
    Audit configuration object.
    """


    #--------------------------------------------------------------------------
    # The options definitions, they will be read from the config file:
    #
    _settings_ = {

        #
        # Main options
        #

        # Targets
        "targets": (Configuration.comma_separated_list, []),

        #
        # Report options
        #

        # Output files
        "reports": (Configuration.comma_separated_list, []),

        # Only display resources with associated vulnerabilities
        "only_vulns": (Configuration.boolean, False),

        #
        # Audit options
        #

        # Audit name
        "audit_name": Configuration.string,

        # Audit database
        "audit_db": (None, "memory://"),

        # Input files
        "imports": (Configuration.comma_separated_list, []),

        #
        # Plugins options
        #

        # Enabled plugins
        "enable_plugins": (Configuration.comma_separated_list, ["all"]),

        # Disabled plugins
        "disable_plugins": (Configuration.comma_separated_list, []),

        #
        # Networks options
        #

        # Include subdomains?
        "include_subdomains": (Configuration.boolean, True),

        # Subdomains as regular expression
        "subdomain_regex": Configuration.string,

        # Depth level for spider
        "depth": (Configuration.integer_or_none, 0),
        # Limits
        "max_links" : (Configuration.integer, 0), # 0 -> infinite

        # Follow redirects
        "follow_redirects": (Configuration.boolean, True),

        # Follow a redirection on the target URL itself, regardless of "follow_redirects"
        "follow_first_redirect": (Configuration.boolean, True),

        # Proxy options
        "proxy_addr": Configuration.string,
        "proxy_user": Configuration.string,
        "proxy_pass": Configuration.string,

        # Cookie
        "cookie": Configuration.string,
    }


    #--------------------------------------------------------------------------
    # Options that are only set in runtime, not loaded from the config file.

    # Start and stop time for the audit.
    # These values are filled on runtime.
    start_time   = None
    stop_time    = None

    # Configuration files.
    config_file  = get_default_config_file()
    profile      = None
    profile_file = None

    # Plugin arguments.
    plugin_args  = None   # list of (plugin_name, key, value)


    #--------------------------------------------------------------------------

    @property
    def targets(self):
        return self._targets

    @targets.setter
    def targets(self, targets):
        # Always append, never overwrite.
        # Fix target URLs if the scheme part is missing.
        self._targets = getattr(self, "_targets", [])
        if targets:
            self._targets.extend(
                (x if (x.startswith("http://") or x.startswith("https://"))
                   else "http://" + x)
                for x in targets)


    #--------------------------------------------------------------------------

    @property
    def imports(self):
        return self._imports

    @imports.setter
    def imports(self, imports):
        # Always append, never overwrite.
        self._imports = getattr(self, "_imports", [])
        if imports:
            self._imports.extend( (str(x) if x else None) for x in imports )


    #--------------------------------------------------------------------------

    @property
    def reports(self):
        return self._reports

    @reports.setter
    def reports(self, reports):
        # Always append, never overwrite.
        self._reports = getattr(self, "_reports", [])
        if reports:
            self._reports.extend( (str(x) if x else None) for x in reports )


    #--------------------------------------------------------------------------

    @property
    def audit_db(self):
        return self._audit_db

    @audit_db.setter
    def audit_db(self, audit_db):
        if not audit_db:
            audit_db = "memory://"
        elif not "://" in audit_db:
            audit_db = "sqlite://" + audit_db
        urlparse.urlparse(audit_db)  # check validity of URL syntax
        self._audit_db = audit_db


    #--------------------------------------------------------------------------

    @property
    def cookie(self):
        return self._cookie

    @cookie.setter
    def cookie(self, cookie):
        if cookie:
            # Parse the cookies argument.
            try:
                # Prepare cookie.
                m_cookie = cookie.replace(" ", "").replace("=", ":")
                # Remove 'Cookie:' start, if exits.
                m_cookie = m_cookie[len("Cookie:"):] if m_cookie.startswith("Cookie:") else m_cookie
                # Split.
                m_cookie = m_cookie.split(";")
                # Parse.
                self.cookie = { c.split(":")[0]:c.split(":")[1] for c in m_cookie}
            except ValueError:
                raise ValueError("Invalid cookie format specified. Use this format: 'Key=value; key=value'.")
        else:
            cookie = None
        self._cookie = cookie


    #--------------------------------------------------------------------------
    def check_params(self):

        # Validate the list of targets.
        if not self.targets:
            raise ValueError("No targets selected for execution.")

        # Validate the list of plugins.
        if not self.enable_plugins:
            raise ValueError("No plugins selected for execution.")
        if set(self.enable_plugins).intersection(self.disable_plugins):
            raise ValueError("Conflicting plugins selection, aborting execution.")

        # Validate the regular expresion.
        if self.subdomain_regex:
            import re

            try:
                re.compile(self.subdomain_regex)
            except re.error, e:
                raise ValueError("Regular expression not valid: %s." % str(e))

        # Validate the recursion depth.
        if self.depth is not None and self.depth < 0:
            raise ValueError("Spidering depth can't be negative: %r" % self.depth)
