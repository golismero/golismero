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
    "pickle", "random", "json_encode", "json_decode",

    # Helper functions.
    "get_user_settings_folder", "get_default_config_file",
    "get_default_user_config_file", "get_default_plugins_folder",
    "get_data_folder", "get_wordlists_folder",
    "get_install_folder", "get_tools_folder",
    "get_profiles_folder", "get_profile", "get_available_profiles",

    # Helper classes and decorators.
    "Singleton", "decorator", "export_methods_as_functions",
    "EmptyNewStyleClass",

    # Configuration objects.
    "OrchestratorConfig", "AuditConfig"
]

# Load the fast C version of pickle,
# if not available use the pure-Python version.
try:
    import cPickle as pickle
except ImportError:
    import pickle

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

try:
    # The fastest JSON parser available for Python.
    from cjson import decode as json_decode
    from cjson import encode as json_encode
except ImportError:
    try:
        # Faster than the built-in module, usually found.
        from simplejson import loads as json_decode
        from simplejson import dumps as json_encode
    except ImportError:
        # Built-in module since Python 2.6, very very slow!
        from json import loads as json_decode
        from json import dumps as json_encode

# Other imports.
from netaddr import IPNetwork
from ConfigParser import RawConfigParser
from keyword import iskeyword
from os import path

import os
import random  #noqa
import sys

# Remove the docstrings. This prevents errors when generating the API docs.
try:
    json_encode.__doc__ = ""
except Exception:
    _orig_json_encode = json_encode
    def json_encode(*args, **kwargs):
        return _orig_json_encode(*args, **kwargs)
try:
    json_decode.__doc__ = ""
except Exception:
    _orig_json_decode = json_decode
    def json_decode(*args, **kwargs):
        return _orig_json_decode(*args, **kwargs)


#------------------------------------------------------------------------------
# Helper class for instance creation without calling __init__().
class EmptyNewStyleClass (object):
    pass


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
    :returns:
        Pathname of the default configuration file,
        or None if it doesn't exist.
    :rtype: str | None
    """
    config_file = path.split(path.abspath(__file__))[0]
    config_file = path.join(config_file, "..", "golismero.conf")
    config_file = path.abspath(config_file)
    if not path.isfile(config_file):
        if path.sep == "/" and path.isfile("/etc/golismero.conf"):
            config_file = "/etc/golismero.conf"
        else:
            config_file = None
    return config_file


#------------------------------------------------------------------------------
def get_default_user_config_file():
    """
    :returns:
        Pathname of the default per-user configuration file,
        or None if it doesn't exist.
    :rtype: str | None
    """
    config_file = path.join(get_user_settings_folder(), "user.conf")
    if not path.isfile(config_file):
        config_file = path.split(path.abspath(__file__))[0]
        config_file = path.join(config_file, "..", "user.conf")
        config_file = path.abspath(config_file)
        if not path.isfile(config_file):
            config_file = None
    return config_file


#------------------------------------------------------------------------------
_install_folder = None
def get_install_folder():
    """
    :returns: Pathname of the install folder.
    :rtype: str
    """
    global _install_folder
    if not _install_folder:
        pathname = path.split(path.abspath(__file__))[0]
        pathname = path.join(pathname, "..")
        pathname = path.abspath(pathname)
        _install_folder = pathname
    return _install_folder


#------------------------------------------------------------------------------
def get_tools_folder():
    """
    :returns: Pathname of the bundled tools folder.
    :rtype: str
    """
    return path.join(get_install_folder(), "tools")


#------------------------------------------------------------------------------
def get_wordlists_folder():
    """
    :returns: Pathname of the wordlists folder.
    :rtype: str
    """
    return path.join(get_install_folder(), "wordlist")


#------------------------------------------------------------------------------
def get_data_folder():
    """
    :returns: Pathname of the data folder.
    :rtype: str
    """
    return path.join(get_install_folder(), "data")


#------------------------------------------------------------------------------
def get_default_plugins_folder():
    """
    :returns: Default location for the plugins folder.
    :rtype: str
    """
    return path.join(get_install_folder(), "plugins")


#------------------------------------------------------------------------------
def get_profiles_folder():
    """
    :returns: Pathname of the profiles folder.
    :rtype: str
    """
    return path.join(get_install_folder(), "profiles")


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
        path.splitext(name)[0]
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
def export_methods_as_functions(singleton, module):
    """
    Export all methods from a Singleton instance as bare functions of a module.

    :param singleton: Singleton instance to export.
    :type singleton: Singleton

    :param module: Target module name.
        This would typically be \\_\\_name\\_\\_.
    :type module: str

    :raises KeyError: No module with that name is loaded.
    """
    # TODO: maybe take the module name as input instead,
    # and pull everything else from sys.modules.
    clazz = singleton.__class__
    module_obj = sys.modules[module]
    try:
        exports = module_obj.__all__
    except AttributeError:
        exports = module_obj.__all__ = []
    for name in dir(clazz):
        if name[0] != "_":
            unbound = getattr(clazz, name)
            if callable(unbound) and not isinstance(unbound, property):
                bound = getattr(singleton, name)
                setattr(module_obj, name, bound)
                if name not in exports:
                    exports.append(name)


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
    #      _settings_  = {
    #         "verbose": (int, 0), # A complete definition.
    #         "output_file": str,  # Omitting the default value (None is used).
    #         "data": None,        # Omitting the parser too.
    #      }
    #
    _settings_ = dict()

    # This is a set of properties that may not be loaded from a config file.
    # They will still be loaded from objects, dictionaries, JSON, etc.
    _forbidden_ = set()


    #--------------------------------------------------------------------------
    # Some helper parsers.

    @staticmethod
    def string(x):
        if x is None:
            return None
        if isinstance(x, unicode):
            return x.encode("UTF-8")
        return str(x)

    @staticmethod
    def integer(x):
        if type(x) in (int, long):
            return x
        return int(x, 0) if x else 0

    @staticmethod
    def integer_or_none(x):
        if x is None or (hasattr(x, "lower") and
                                 x.lower() in ("", "none", "inf", "infinite")):
            return None
        return Configuration.integer(x)

    @staticmethod
    def float(x):
        return float(x) if x else 0.0

    @staticmethod
    def comma_separated_list(x):
        if not x:
            return []
        if isinstance(x, str):
            return [t.strip() for t in x.split(",")]
        if isinstance(x, unicode):
            return [t.strip().encode("UTF-8") for t in x.split(u",")]
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
            raise ValueError(
                "Trinary values only accept True, False and None")
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

        This method only checks the validity of the arguments,
        it won't modify them.

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

        :param args:
            Python object,
            for example the command line arguments parsed by argparse.
        :type args: object
        """

        # Builds a dictionary with the object's public attributes.
        args = {
            k : getattr(args, k)
            for k in dir(args) if not k.startswith("_")
        }

        # Remove all attributes whose values are None.
        args = { k:v for k,v in args.iteritems() if v is not None }

        # Extract the settings from the dictionary.
        if args:
            self.from_dictionary(args)


    #--------------------------------------------------------------------------
    def from_json(self, json_raw_data):
        """
        Get the settings from a JSON encoded dictionary.

        :param json_raw_data: JSON raw data.
        :type json_raw_data: str
        """

        # Converts the JSON data into a dictionary.
        args = json_decode(json_raw_data)
        if not isinstance(args, dict):
            raise TypeError("Invalid JSON data")

        # Extract the settings from the dictionary.
        if args:
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
        if parser.has_section("golismero"):
            options = { k:v for k,v in parser.items("golismero") if v }
            if "profile" in options:
                if allow_profile:
                    self.profile = options["profile"]
                    self.profile_file = get_profile(self.profile)
                else:
                    del options["profile"]
            for k in self._forbidden_:
                if k in options:
                    del options[k]
            if options:
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

        :returns: Settings as a JSON encoded dictionary.
        :rtype: str
        """

        # Extract the settings to a dictionary and encode it with JSON.
        return json_encode( self.to_dictionary() )


#------------------------------------------------------------------------------
class OrchestratorConfig (Configuration):
    """
    Orchestrator configuration object.
    """


    #--------------------------------------------------------------------------
    # The options definitions, they will be read from the config file:
    #
    _forbidden_ = set((  # except for these:
        "config_file", "user_config_file",
        "profile_file", "plugin_args", "ui_mode",
    ))
    _settings_ = {

        #
        # Main options.
        #

        # UI mode.
        "ui_mode": (str, "console"),

        # Verbosity level.
        "verbose": (Configuration.integer, 3),

        # Colorize console?
        "color": (Configuration.boolean, False),

        #
        # Plugin options.
        #

        # Enabled plugins.
        "enable_plugins": (Configuration.comma_separated_list, ["all"]),

        # Disabled plugins.
        "disable_plugins": (Configuration.comma_separated_list, []),

        # Plugins folder.
        "plugins_folder": Configuration.string,

        # Maximum number plugins to execute concurrently.
        "max_concurrent": (Configuration.integer,
                           4 if path.sep == "\\" else 20),

        #
        # Network options.
        #

        # Maximum number of connections per host.
        "max_connections": (Configuration.integer, 20),

        # Use persistent cache?
        "use_cache_db": (Configuration.boolean, True),

        # When run as a service.
        "listen_address": Configuration.string,
        "listen_port": Configuration.integer,
        "server_push": Configuration.string,
    }


    #--------------------------------------------------------------------------
    # Options that are only set in runtime, not loaded from the config file.

    # Configuration files.
    config_file      = get_default_config_file()
    user_config_file = get_default_user_config_file()

    # Profile.
    profile      = None
    profile_file = None

    # Plugin arguments.
    plugin_args  = dict()   # plugin_id -> key -> value


    #--------------------------------------------------------------------------

    @staticmethod
    def _load_profile(self, args):
        if "profile" in args:
            self.profile = args["profile"]
            if isinstance(self.profile, unicode):
                self.profile = self.profile.encode("UTF-8")
            self.profile_file = get_profile(self.profile)

    @staticmethod
    def _load_plugin_args(self, args):
        if "plugin_args" in args:
            plugin_args = {}
            for (plugin_id, target_args) in args["plugin_args"].iteritems():
                if isinstance(plugin_id, unicode):
                    plugin_id = plugin_id.encode("UTF-8")
                if not plugin_id in plugin_args:
                    plugin_args[plugin_id] = {}
                for (key, value) in target_args.iteritems():
                    if isinstance(key, unicode):
                        key = key.encode("UTF-8")
                    if isinstance(value, unicode):
                        value = value.encode("UTF-8")
                    plugin_args[plugin_id][key] = value
            self.plugin_args = plugin_args

    def from_dictionary(self, args):
        # Security note: do not copy config filenames!
        # See the _forbidden_ property.
        super(OrchestratorConfig, self).from_dictionary(args)
        self._load_profile(self, args)      # "self" is twice on purpose!
        self._load_plugin_args(self, args)  # don't change it or it breaks

    def to_dictionary(self):
        result = super(OrchestratorConfig, self).to_dictionary()
        result["config_file"]      = self.config_file
        result["user_config_file"] = self.user_config_file
        result["profile"]          = self.profile
        result["profile_file"]     = self.profile_file
        result["plugin_args"]      = self.plugin_args
        return result


    #--------------------------------------------------------------------------
    def check_params(self):

        # Validate the network connections limit.
        if self.max_connections < 1:
            raise ValueError(
                "Number of connections must be greater than 0,"
                " got %i." % self.max_connections)

        # Validate the number of concurrent processes.
        if self.max_concurrent < 0:
            raise ValueError(
                "Number of processes cannot be a negative number,"
                " got %i." % self.max_concurrent)

        # Validate the list of plugins.
        if not self.enable_plugins:
            raise ValueError("No plugins selected for execution.")
        if set(self.enable_plugins).intersection(self.disable_plugins):
            raise ValueError(
                "Conflicting plugins selection, aborting execution.")


#------------------------------------------------------------------------------
class AuditConfig (Configuration):
    """
    Audit configuration object.
    """


    #--------------------------------------------------------------------------
    # The options definitions, they will be read from the config file:
    #
    _forbidden = set(( # except for these:
        "config_file", "user_config_file", "profile_file", "plugin_args",
        "plugin_load_overrides", "command",
    ))
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

        # Only display vulnerabilities
        "only_vulns": (Configuration.trinary, None),

        #
        # Audit options
        #

        # Audit name
        "audit_name": Configuration.string,

        # Audit database
        "audit_db": (None, ":memory:"),

        # Input files
        "imports": (Configuration.comma_separated_list, []),

        #
        # Plugin options
        #

        # Enabled plugins
        "enable_plugins": (Configuration.comma_separated_list, ["all"]),

        # Disabled plugins
        "disable_plugins": (Configuration.comma_separated_list, []),

        # Plugin execution timeout
        "plugin_timeout": (Configuration.float, 3600.0),

        #
        # Network options
        #

        # Include subdomains?
        "include_subdomains": (Configuration.boolean, True),

        # Include parent folders?
        "allow_parent": (Configuration.boolean, True),

        # Depth level for spider
        "depth": (Configuration.integer_or_none, 1),

        # Limits
        "max_links" : (Configuration.integer, 0), # 0 -> infinite

        # Follow redirects
        "follow_redirects": (Configuration.boolean, True),

        # Follow a redirection on the target URL itself,
        # regardless of "follow_redirects"
        "follow_first_redirect": (Configuration.boolean, True),

        # Proxy options
        "proxy_addr": Configuration.string,
        "proxy_port": Configuration.integer,
        "proxy_user": Configuration.string,
        "proxy_pass": Configuration.string,

        # Cookie
        "cookie": Configuration.string,

        # User Agent
        "user_agent": Configuration.string,
    }


    #--------------------------------------------------------------------------
    # Options that are only set in runtime, not loaded from the config file.

    # Configuration files.
    config_file      = get_default_config_file()
    user_config_file = get_default_user_config_file()

    # Profiles.
    profile      = None
    profile_file = None

    # Plugin arguments.
    plugin_args = None   # list of (plugin_id, key, value)

    # Plugin load overrides.
    plugin_load_overrides = None

    # Command to run.
    command = "SCAN"


    #--------------------------------------------------------------------------
    def from_dictionary(self, args):

        # Security note: do not copy config filenames!
        # See the _forbidden_ property.
        super(AuditConfig, self).from_dictionary(args)
        OrchestratorConfig._load_profile(self, args) # not a filename
        OrchestratorConfig._load_plugin_args(self, args)

        # Load the "command" property.
        if "command" in args:
            self.command = args["command"]
            if isinstance(self.command, unicode):
                self.command = self.command.encode("UTF-8")

        # Load the "plugin_load_overrides" property.
        if "plugin_load_overrides" in args:
            if not self.plugin_load_overrides:
                self.plugin_load_overrides = []
            for (val, plugin_id) in args["plugin_load_overrides"]:
                self.plugin_load_overrides.append((bool(val), str(plugin_id)))


    #--------------------------------------------------------------------------
    def to_dictionary(self):
        result = super(AuditConfig, self).to_dictionary()
        result["config_file"]           = self.config_file
        result["user_config_file"]      = self.user_config_file
        result["profile"]               = self.profile
        result["profile_file"]          = self.profile_file
        result["plugin_args"]           = self.plugin_args
        result["command"]               = self.command
        result["plugin_load_overrides"] = self.plugin_load_overrides
        return result


    #--------------------------------------------------------------------------

    @property
    def targets(self):
        return self._targets

    @targets.setter
    def targets(self, targets):
        # Always append, never overwrite.
        # Fix target URLs if the scheme part is missing.

        # Make sure self._targets contains a list.
        self._targets = getattr(self, "_targets", [])

        # Ignore the trivial case.
        if not targets:
            return

        # Strip whitespace.
        targets = [
            x.strip()
            for x in targets
            if x not in self._targets
        ]

        # Remove duplicates.
        targets = [
            x
            for x in set(targets)
            if x not in self._targets
        ]

        # Encode all Unicode strings as UTF-8.
        targets = [
            x.encode("UTF-8") if isinstance(x, unicode) else str(x)
            for x in targets
            if x not in self._targets
        ]

        # Detect network ranges, like 30.30.30.0/24, and get all IPs on it.
        parsed_targets = []
        for host in targets:

            # Try to parse the address as a network range.
            try:
                tmp_target = IPNetwork(host)
            except:
                parsed_targets.append(host)
                continue

            # If it's a range, iterate it and get all IP addresses.
            # If it's a single IP address, just add it.
            if tmp_target.size != 1:
                parsed_targets.extend(
                    str(x) for x in tmp_target.iter_hosts()
                )
            else:
                parsed_targets.append( str(tmp_target.ip) )

        # Add the new targets.
        self._targets.extend(parsed_targets)

    @targets.deleter
    def targets(self):
        self._targets = []


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
        if (
            not audit_db or not audit_db.strip() or
            audit_db.strip().lower() == ":auto:"
        ):
            audit_db = ":auto:"
        elif audit_db.strip().lower() == ":memory:":
            audit_db = ":memory:"
        self._audit_db = audit_db


    #--------------------------------------------------------------------------

    @property
    def user_agent(self):
        return self._user_agent

    @user_agent.setter
    def user_agent(self, user_agent):
        if user_agent:
            if isinstance(user_agent, unicode):
                user_agent = user_agent.encode("UTF-8")
            self._user_agent = user_agent
        else:
            self._user_agent = None


    #--------------------------------------------------------------------------

    @property
    def cookie(self):
        return self._cookie

    @cookie.setter
    def cookie(self, cookie):
        if cookie:
            # Parse the cookies argument.
            try:
                if isinstance(cookie, unicode):
                    cookie = cookie.encode("UTF-8")
                # Prepare cookie.
                cookie = cookie.replace(" ", "").replace("=", ":")
                # Remove 'Cookie:' start, if exits.
                if cookie.startswith("Cookie:"):
                    cookie = cookie[len("Cookie:"):]
                # Split.
                cookie = cookie.split(";")
                # Parse.
                cookie = { c.split(":")[0]:c.split(":")[1] for c in cookie}
            except ValueError:
                raise ValueError(
                    "Invalid cookie format specified."
                    " Use this format: 'Key=value; key=value'.")
        else:
            cookie = None
        self._cookie = cookie


    #--------------------------------------------------------------------------

    @property
    def proxy_addr(self):
        return self._proxy_addr

    @proxy_addr.setter
    def proxy_addr(self, proxy_addr):
        if proxy_addr:
            proxy_addr = proxy_addr.strip()
            if isinstance(proxy_addr, unicode):
                proxy_addr = proxy_addr.encode("UTF-8")
            if ":" in proxy_addr:
                proxy_addr, proxy_port = proxy_addr.split(":", 1)
                proxy_addr = proxy_addr.strip()
                proxy_port = proxy_port.strip()
                self.proxy_port = proxy_port
            self._proxy_addr = proxy_addr
        else:
            self._proxy_addr = None


    #--------------------------------------------------------------------------

    @property
    def proxy_port(self):
        return self._proxy_port

    @proxy_port.setter
    def proxy_port(self, proxy_port):
        if proxy_port:
            self._proxy_port = int(proxy_port)
            if self._proxy_port < 1 or self._proxy_port > 65534:
                raise ValueError(
                    "Invalid proxy port number: %d" % self._proxy_port)
        else:
            self._proxy_port = None


    #--------------------------------------------------------------------------
    def check_params(self):

        # Validate the list of plugins.
        if not self.enable_plugins:
            raise ValueError(
                "No plugins selected for execution.")
        if set(self.enable_plugins).intersection(self.disable_plugins):
            raise ValueError(
                "Conflicting plugins selection, aborting execution.")

        # Validate the recursion depth.
        if self.depth is not None and self.depth < 0:
            raise ValueError(
                "Spidering depth can't be negative: %r" % self.depth)
        if self.depth is not None and self.depth == 0:
            raise ValueError(
                "Spidering depth can't be zero (nothing would be done!)")


    #--------------------------------------------------------------------------
    def is_new_audit(self):
        """
        Determine if this is a brand new audit.

        :returns: True if this is a new audit, False if it's an old audit.
        :rtype: bool
        """

        # Memory databases are always new audits.
        if (
            not self.audit_db or not self.audit_db.strip() or
            self.audit_db.strip().lower() == ":memory:"
        ):
            self.audit_db = ":memory:"
            return True

        # SQLite databases are new audits if the file doesn't exist.
        # If we have no filename, use the audit name.
        # If we don't have that either it's a new audit.
        filename = self.audit_db
        if not filename:
            filename = self.audit_name + ".db"
            if not filename:
                return True
        return not path.exists(filename)
