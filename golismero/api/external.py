#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
External tools API.

Use this module to run external tools and grab their output.
This makes an easy way to integrate GoLismero with any command line tools.
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

    # Run an external tool.
    "run_external_tool",

    # Temporary file utility functions.
    "tempfile",

    # Executable file utility functions.
    "is_executable",
    "get_interpreter",
    "find_binary_in_path",

    # Cygwin utility functions.
    "is_cygwin_binary",
    "get_cygwin_binary",
    "find_cygwin_binary_in_path",
    "win_to_cygwin_path",
    "cygwin_to_win_path",
]

import contextlib
import re
import os
import os.path
import ntpath
import subprocess
import stat
import shlex
import sys

from tempfile import NamedTemporaryFile

# Needed on non-Windows platforms to prevent a syntax error.
try:
    WindowsError
except NameError:
    class WindowsError(OSError): pass


#------------------------------------------------------------------------------
class ExternalToolError(RuntimeError):
    """
    An error occurred when running an external tool.
    """

    def __init__(self, msg, errcode):
        super(ExternalToolError, self).__init__(self, msg)
        self.errcode = errcode


#------------------------------------------------------------------------------
def run_external_tool(command, args = None, env = None, cwd = None,
                      callback = None):
    """
    Run an external tool and optionally fetch the output.

    Standard output and standard error are combined into a single stream.
    Newline characters are always '\\n' in all platforms.

    .. warning: SECURITY WARNING: Be *extremely* careful when passing
                data coming from the target servers to this function.
                Failure to properly validate the data may result in
                complete compromise of your machine! See:
                https://www.owasp.org/index.php/Command_Injection

    Example::
        >>> def callback(line):
        ...    print line
        ...
        >>> run_external_tool("uname", callback=callback)
        Linux

    :param command: Command to execute.
    :type command: str

    :param args: Arguments to be passed to the command.
    :type args: list(str)

    :param env: Environment variables to be passed to the command.
    :type env: dict(str -> str)

    :param cwd: Current directory while running the tool.
        This is useful for tools that require you to be standing on a specific
        directory when running them.
    :type cwd: str | None

    :param callback: Optional callback function. If given, it will be called
        once for each line of text printed by the external tool. The trailing
        newline character of each line is removed.
    :type callback: callable

    :returns: Return code from the external tool.
    :rtype: int

    :raises ExternalToolError: An error occurred when running an external tool.
    """

    # We put a large and nasty security warning here mostly to scare the noobs,
    # because subprocess is generally safe when you don't run in "shell" mode
    # nor invoke bash directly - i.e. when you know what the hell you're doing.
    #
    # Still, especially on Windows, some external programs are really stupid
    # when it comes to parsing their own command line, so caveat emptor.

    # Validate the callback argument.
    if callback is not None and not callable(callback):
        raise TypeError("Expected function, got %r instead" % type(callback))

    # An empty string in 'cwd' breaks Popen, so we need to convert it to None.
    if not cwd:
        cwd = None

    # Make a copy of the command line arguments.
    if not args:
        args = []
    else:
        args = list(args)
        if not command:
            command = args[0]
            del args[0]
        elif args and args[0] == command:
            del args[0]
    if not command:
        raise ValueError("Bad arguments for run_external_tool()")

    # Check if the command is executable.
    if not is_executable(command):

        # Check if the command is a script.
        try:
            interpreter = get_interpreter(command)
        except IOError:
            interpreter = None
        if interpreter:

            # Prepend the interpreter to the command line.
            command = interpreter[0]
            args = interpreter[1:] + args

        # If it's not a script...
        else:

            # Find the target in the path.
            binary_list = find_binary_in_path(command)
            if not binary_list:
                raise IOError("File not found: %r" % command)

            # On Windows, prefer Cygwin binaries over native binaries.
            # Otherwise, just pick the first one in the PATH.
            if os.path.sep == "\\":
                binary = get_cygwin_binary(binary_list)
                if binary:
                    command = binary
                else:
                    command = binary_list[0]
            else:
                command = binary_list[0]

    # Prepend the binary to the command line.
    args.insert(0, command)

    # Turn off DOS path warnings for Cygwin.
    if os.path.sep == "\\":
        if env is None:
            env = os.environ.copy()
        else:
            env = env.copy()
        cygwin = env.get("CYGWIN", "")
        if "nodosfilewarning" not in cygwin:
            if cygwin:
                cygwin += " "
            cygwin += "nodosfilewarning"
        env["CYGWIN"] = cygwin

    # If the user doesn't want the output,
    # just run the process and wait for completion.
    if callback is None:
        return subprocess.check_call(args,
            executable = command,
                   cwd = cwd,
                   env = env,
                 shell = False)

    proc = None
    try:

        # Spawn the process.
        try:
            proc = subprocess.Popen(args,
                        executable = command,
                               cwd = cwd,
                               env = env,
                            stdout = subprocess.PIPE,
                            stderr = subprocess.STDOUT,
                universal_newlines = True,
                           bufsize = 0,
                             shell = False,
            )

        # On error raise ExternalToolError.
        except OSError, e:
            msg = str(e)
            if isinstance(e, WindowsError):
                if "%1" in msg:
                    msg = msg.replace("%1", command)
                raise ExternalToolError(msg, e.winerror)
            raise ExternalToolError(msg, e.errno)

        # Read each line of output and send it to the callback function.
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if line.endswith("\n"):
                line = line[:-1]
            callback(line)

    finally:

        # Make sure the spawned process is dead.
        if proc is not None and proc.poll() is None:
            proc.terminate()

    # Return the exit code.
    return proc.returncode


#------------------------------------------------------------------------------
def is_executable(binary):
    """
    Tests if the given file exists and is executable.

    :param binary: Path to the binary.
    :type binary: str

    :returns: True if the file exists and is executable, False otherwise.
    :rtype: bool
    """
    return os.path.isfile(binary) and (
        (os.path.sep == "\\" and binary.lower().endswith(".exe")) or
        (os.path.sep == "/" and
         os.stat(binary)[stat.ST_MODE] & stat.S_IXUSR != 0)
    )


#------------------------------------------------------------------------------

# Default interpreter for each script file extension.
DEFAULT_INTERPRETER = {

    ".lua":  ["lua"],
    ".php":  ["php", "-f"],
    ".pl":   ["perl"],
    ".rb":   ["ruby"],
    ".sh":   ["sh", "-c"],
    ".tcl":  ["tcl"],

    ".py":   ["python"],
    ".pyc":  ["python"],
    ".pyo":  ["python"],
    ".pyw":  ["python"],

    ".js":   ["WScript.exe"],
    ".jse":  ["WScript.exe"],
    ".pls":  ["WScript.exe"],
    ".phps": ["WScript.exe"],
    ".pys":  ["WScript.exe"],
    ".rbs":  ["WScript.exe"],
    ".tcls": ["WScript.exe"],
    ".vbs":  ["WScript.exe"],
    ".vbe":  ["WScript.exe"],
    ".wsf":  ["WScript.exe"],
}


#------------------------------------------------------------------------------
def get_interpreter(script):
    """
    Get the correct interpreter for the given script.

    :param script: Path to the script file.
    :type script: str

    :returns: Command line arguments to replace the script with.
        Normally this will be the path to the interpreter followed
        by the path to the script, but not always.
    :rtype: list(str)
    :raises IOError: An error occurred, the file was not a script, or the
        interpreter was not found.
    """

    # Get the file extension.
    ext = os.path.splitext(script)[1].lower()

    # On Windows...
    if os.path.sep == "\\":

        # EXE files are executable.
        if ext == ".exe":
            binary_list = find_binary_in_path(script)
            if binary_list:
                cygwin = get_cygwin_binary(binary_list)
                if cygwin:
                    return [ cygwin ]
                return [ binary_list[0] ]
            return [ script ]

        # Batch files use cmd.exe.
        if ext in (".bat", ".cmd"):
            return [ os.environ["COMSPEC"], "/C", script ]

    # On Unix, the script may be marked as executable.
    elif is_executable(script):
        return [ script ]

    # Get the name of the default interpreter for each extension.
    interpreter = DEFAULT_INTERPRETER.get(ext, None)
    if interpreter:
        interpreter = list(interpreter) # must be a copy!

        # Add the .exe extension on Windows.
        if os.path.sep == "\\" and not interpreter[0].endswith(".exe"):
            interpreter[0] += ".exe"

        # Look for the interpreter binary on the PATH.
        binary_list = find_binary_in_path(interpreter[0])
        if binary_list:
            cygwin = get_cygwin_binary(binary_list)
            if cygwin:
                interpreter[0] = cygwin
            else:
                interpreter[0] = binary_list[0]

        # Add the script and return it.
        interpreter.append(script)
        return interpreter

    # Try getting the interpreter from the first line of code.
    # This works for scripts that follow the shebang convention.
    # See: https://en.wikipedia.org/wiki/Shebang_(Unix)
    with open(script, "rb") as f:
        signature = f.read(128)
    signature = signature.strip()
    if signature and signature[:1] == "#!":
        signature = signature[1:].split("\n", 1)[0]
        signature = signature.strip()
        args = shlex.split(signature)
        if args:

            # If it exists and is executable, use it.
            if is_executable(args[0]):
                args.append(script)
                return args

            # Try to guess which interpreter it is.
            for ext, interpreter in DEFAULT_INTERPRETER.iteritems():
                regex = interpreter[0]
                regex = "".join((c if c.isalnum() else "\\"+c) for c in regex)
                regex = "\\b%s\\b" % regex
                if re.search(regex, args[0]):
                    return interpreter + [script] # must be a copy!

            # Broader search, matches stuff like python2, ruby1.9, etc.
            for ext, interpreter in DEFAULT_INTERPRETER.iteritems():
                regex = interpreter[0]
                if regex.isalpha():
                    regex = "\\b%s[0-9\\.]*\\b" % regex
                    if re.search(regex, args[0]):
                        return interpreter + [script] # must be a copy!

    # No valid interpreter was found.
    raise IOError("Interpreter not found for script: %s" % script)


#------------------------------------------------------------------------------
def find_binary_in_path(binary):
    """
    Find the given binary in the current environment PATH.

    :param path: Path to the binary.
    :type path: str

    :returns: List of full paths to the binary.
        If not found, the list will be empty.
    :rtype: list(str)
    """

    # Get the filename.
    binary = os.path.split(binary)[1]

    # Get the possible locations from the PATH environment variable.
    locations = os.environ.get("PATH", "").split(os.path.pathsep)

    # On Windows...
    if sys.platform in ("win32", "cygwin"):

        # Append the system folders.
        comspec = os.environ.get("ComSpec", "C:\\Windows\\System32\\cmd.exe")
        comspec = os.path.split(comspec)[0]
        system_root = os.environ.get("SystemRoot", "C:\\Windows")
        system_32 = os.path.join(system_root, "System32")
        system_64 = os.path.join(system_root, "SysWOW64")
        if comspec not in locations: locations.append(comspec)
        if system_root not in locations: locations.append(system_root)
        if system_32 not in locations: locations.append(system_32)
        if system_64 not in locations: locations.append(system_64)

        # Append the ".exe" extension to the binary if missing.
        if os.path.splitext(binary)[1] == "":
            binary += ".exe"

    # Look for the file in the PATH.
    found = []
    for candidate in locations:
        if candidate:
            candidate = os.path.abspath(candidate)
            candidate = os.path.join(candidate, binary)
            if is_executable(candidate):
                found.append(candidate)

    # On Windows, remove duplicates caused by case differences.
    if sys.platform in ("win32", "cygwin"):
        upper = [x.upper() for x in found]
        found = [x for i, x in enumerate(found) if x.upper() not in upper[:i]]

    # Return all instances found.
    return found


#------------------------------------------------------------------------------
def is_cygwin_binary(path):
    """
    Detects if the given binary is located in the Cygwin /bin directory.

    :param path: Windows path to the binary.
    :type path: str

    :returns: True if the binary belongs to Cygwin, False for native binaries.
    :rtype: bool
    """
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        path = os.path.split(path)[0]
    path = os.path.join(path, "cygwin1.dll")
    return os.path.exists(path)


#------------------------------------------------------------------------------
def get_cygwin_binary(binary_list):
    """
    Take the list of binaries returned by find_binary_in_path() and grab the
    one that belongs to Cygwin.

    This is useful for commands or scripts that work different/better on Cygwin
    than the native version (for example the "find" command).

    :param binary_list: List of paths to the binaries to test.
    :type binary_list: str(list)

    :returns: Path to the Cygwin binary, or None if not found.
    :type: str | None
    """
    for binary in binary_list:
        if is_cygwin_binary(binary):
            return binary


#------------------------------------------------------------------------------
def find_cygwin_binary_in_path(binary):
    """
    Find the given binary in the current environment PATH,
    but only if it's the Cygwin version.

    This is useful for commands or scripts that work different/better on Cygwin
    than the native version (for example the "find" command).

    :param path: Path to the binary.
    :type path: str

    :returns: Path to the Cygwin binary, or None if not found.
    :type: str | None
    """
    return get_cygwin_binary( find_binary_in_path(binary) )


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


#------------------------------------------------------------------------------
@contextlib.contextmanager
def tempfile(*args, **kwargs):
    """
    Context manager that creates a temporary file.
    The file is deleted when leaving the context.

    Example::
        >>> with tempfile(prefix="tmp", suffix=".bat") as filename:
        ...     with open(filename, "w") as fd:
        ...         fd.write("@echo off\necho Hello World!\n")
        ...     print run_external_tool("cmd.exe", ["/C", filename])
        ...
        ('Hello World!', 0)

    The arguments are exactly the same used by the standard NamedTemporaryFile
    class (from the tempfile module).
    """

    # On Windows we can't open a temporary file twice (although it's
    # actually Python who won't let us). Note that there is no exploitable
    # race condition here, because on Windows you can only create
    # filesystem links from an Administrator account.
    if sys.platform in ("win32", "cygwin"):
        kwargs["delete"] = False
        output_file = NamedTemporaryFile(*args, **kwargs)
        output = output_file.name
        output_file.close()
        yield output
        os.unlink(output_file.name)

    # On POSIX we can do things more elegantly.
    # It also prevents a race condition vulnerability, although if you're
    # running a Python script from root you kinda deserve to get pwned.
    else:
        with NamedTemporaryFile(suffix = ".xml") as output_file:
            yield output_file.name
