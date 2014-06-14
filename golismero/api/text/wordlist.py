#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wordlist API.
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

__all__ = ["WordListLoader", "WordlistNotFound"]

import re
import copy

from os import walk
from itertools import tee
from abc import ABCMeta, abstractproperty
from os.path import join, sep, abspath, exists, isfile

from golismero.api.localfile import LocalFile
from .matching_analyzer import get_diff_ratio
from ...common import Singleton, get_wordlists_folder


#------------------------------------------------------------------------------
class WordlistNotFound(Exception):
    """Exception when wordlist not found"""


#------------------------------------------------------------------------------
class _WordListLoader(Singleton):
    """
    Wordlist API.
    """

    #--------------------------------------------------------------------------
    def __init__(self):

        # Store
        self.__store = {}  # Pair with: (name, path)

        # Initial load
        self.__load_wordlists(get_wordlists_folder())

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------
    def __get_wordlist_descriptor(self, wordlist):
        """
        Looking for the world list in this order:
        1 - In the internal database and.
        2 - Looking in the plugin directory
        3 - Looking the wordlist in the file system.

        If Wordlist not found, raise WordlistNotFound exception.

        :param wordlist: wordlist name
        :type wordlist: basestring

        :return: a file descriptor.
        :rtype: open()

        :raises: WordlistNotFound, TypeError, ValueError, IOError
        """
        if not isinstance(wordlist, basestring):
            raise TypeError("Expected 'str' got '%s'." % type(wordlist))

        # For avoid user errors, library accept also, wordlists starting as:
        # wordlist/....
        if wordlist.startswith("wordlist"):
            wordlist = "/".join(wordlist.split("/")[1:])

        if not wordlist:
            raise ValueError("Wordlist name can't be an empty value")

        try:
            return open(self.__store[wordlist], "rU")
        except KeyError:  # Wordlist is not in the internal database

            # Can open from plugin wordlists?
            internal = True
            try:
                if LocalFile.exists(wordlist):
                    if not LocalFile.isfile(wordlist):
                        internal = False

                    return LocalFile.open(wordlist, "rU")
                else:
                    internal = False
            except ValueError:
                internal = False

            if not internal:
                # Looking the wordlist in the file system, assuming that the
                # wordlist name is an absolute path.
                if exists(wordlist):
                    if not isfile(wordlist):
                        raise WordlistNotFound("Wordlist '%s' is not a file." % wordlist)

                    return open(wordlist, "rU")
                else:
                    raise WordlistNotFound("Wordlist file '%s' does not exist." % wordlist)

    #--------------------------------------------------------------------------
    def __load_wordlists(self, current_dir):
        """
        Find and load wordlists from the specified directory.

        .. warning: Private method, do not call!

        :param current_dir: Directory to look for wordlists.
        :type current_dir: str

        :raises: TypeError, ValueError
        """
        if not isinstance(current_dir, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(current_dir))

        # Make sure the directory name is absolute and ends with a slash.
        current_dir = abspath(current_dir)
        if not current_dir.endswith(sep):
            current_dir += sep

        if not exists(current_dir):
            raise ValueError("Path directory for wordlist '%s' not exits" % current_dir)

        # Iterate the directory recursively.
        for (dirpath, _, filenames) in walk(current_dir):

            # Make sure the directory name is absolute.
            dirpath = abspath(dirpath)

            # Look for text files, skipping README files and disabled lists.
            for fname in filenames:
                if not fname.startswith("_") and fname.lower() != "readme.txt":

                    # Map the relative filename to the absolute filename,
                    # replacing \ for / on Windows.
                    target = join(dirpath, fname)
                    key = target[len(current_dir):]
                    if sep != "/":
                        key = key.replace(sep, "/")
                    self.__store[key] = target


    #--------------------------------------------------------------------------
    # Property
    #--------------------------------------------------------------------------
    @property
    def all_wordlists(self):
        """
        :returns: Names of all the wordlists.
        :rtype: list
        """
        return self.__store.keys()

    #--------------------------------------------------------------------------
    # Public methods
    #--------------------------------------------------------------------------
    def get_wordlist_as_raw(self, wordlist_name):
        """
        Get a wordlist file handler.

        >>> values = ["hello", "world", "  this has spaces  ", "# A comment"]
        >>> open("my_wordlist.txt", "w").writelines(values)
        >>> w_file = WordListLoader.get_wordlist_as_raw("my_wordlist.txt")
        >>> for line in w_file.readlines():
            print line,
        hello
        world
          this has spaces
        # A comment

        :param wordlist_name: Name of the requested wordlist.
        :type wordlist_name: basestring

        :returns: file description.
        :rtype: file

        :raises: TypeError, ValueError, WordlistNotFound, IOError
        """
        if not isinstance(wordlist_name, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(wordlist_name))
        if not wordlist_name:
            ValueError("Expected wordlist name, got None instead")

        return self.__get_wordlist_descriptor(wordlist_name)

    #--------------------------------------------------------------------------
    def get_wordlist_as_dict(self, wordlist_name, separator=";", smart_load=False):
        """
        Get a wordlist as a dict, with some search operations.

        Load a wordlist file, with their lines splited by some char, an load left str as a key, and right as a value.

        >>> values = ["hello", "world", "  this has spaces  ", "# A comment"]
        >>> open("my_wordlist.txt", "w").writelines(values)
        >>> w = WordListLoader.get_wordlist_as_l("my_wordlist.txt")
        >>> for line in w:
            print line,
        hello
        world
        this has spaces
        A comment
        >>>


        :param wordlist_name: Wordlist name.
        :type wordlist_name: str

        :param separator: value used to split the lines
        :type separator: str

        :param smart_load: Indicates if the wordlist must detect if the line has values that can be converted in a list.
        :type smart_load: bool

        :returns: Advanced wordlist object.
        :rtype: WDict
        """

        return WDict(self.__get_wordlist_descriptor(wordlist_name), separator, smart_load)

    #--------------------------------------------------------------------------
    def get_wordlist_as_list(self, wordlist_name):
        """
        Get a wordlist as a list, with some search operations.

        Also apply these filter to each line:
        - Filter commented lines (starting with '#')
        - Remove end chars: line return '\n', tabs '\t' or carry line.
        - Remove start and end spaces.

        >>> values = ["hello", "world", "  this has spaces  ", "# A comment", "word"]
        >>> open("my_wordlist.txt", "w").writelines(values)
        >>> w = WordListLoader.get_wordlist_as_list("my_wordlist.txt")
        >>> for line in w:
            print line,
        hello
        world
        this has spaces
        A comment
        >>> w.se

        :param wordlist_name: Wordlist name.
        :type wordlist_name: str

        :returns: WList.
        :rtype: WList
        """

        return WList(self.__get_wordlist_descriptor(wordlist_name))


#----------------------------------------------------------------------
def _simple_iterator(wordlist_handler):
    """
    Simple iterator function.

    ..note:

    This function is outside of get_wordlist_as_raw because generators functions can't raise common
    exceptions os return values for wrong inputs.

    :param wordlist_handler: path to wordlist
    :type wordlist_handler: str

    :raises: WordlistNotFound
    """
    try:
        for line in wordlist_handler:
            yield line
    except IOError, e:
        raise WordlistNotFound("Error opening wordlist. Error: %s " % str(e))


#------------------------------------------------------------------------------
class _AbstractWordlist(object):
    """
    Abstract class for advanced wordlists.
    """
    __metaclass__ = ABCMeta

    #--------------------------------------------------------------------------
    @abstractproperty
    def search(self, word, exact_search=True):
        """
        Makes a search in the list and return the position of the word.

        Raises a ValueError exception if no coincidence found.

        :param word: The word to find.
        :type word: str

        :param exact_search: indicates if search will find exact word or some that contain this word.
        :type exact_search: bool

        :raises: ValueError, TypeError
        """

    #--------------------------------------------------------------------------
    @abstractproperty
    def get_first(self, word, init=0, exact_search=True):
        """
        Get the index of first coincidence or 'word', starting at init value.

        Raises a ValueError exception if no coincidence found.

        :param init: initial position to the function starts searching.
        :type init: Int

        :param exact_search: indicates if search will find exact word or some that contain this word.
        :type exact_search: bool

        :return: index of the first element found.
        :rtype: int

        :raises: ValueError
        """

    #--------------------------------------------------------------------------
    @abstractproperty
    def get_rfirst(self, word, init=0, exact_search=True):
        """
        Get first coincidence, starting from the end. Raises a ValueError exception
        if no coincidence found.

        :param init: initial position to the function starts searching. Position start at the end of list.
        :type init: int

        :param exact_search: indicates if search will find exact word or some that contain this word.
        :type exact_search: bool

        :return: Value of the first element found, stating at the end.
        :rtype: str

        :raises: ValueError
        """

    #--------------------------------------------------------------------------
    # @abstractproperty
    # def search_mutations(self, word, rules):  # TODO
    #     """"""

    #--------------------------------------------------------------------------
    @abstractproperty
    def clone(self):
        """
        This method makes a clone of the object.

        :return: A copy of this object.
        """

    #----------------------------------------------------------------------
    def _raw_to_list(self, input_iterable):
        """
        Transform iterable input text into a list, without line breaks or any other special character.

        :param input_iterable: Input iterable info.
        :type input_iterable: file

        :return: generated list.
        :rtype: list(str)

        :raises: ValueError, TypeError
        """
        if input_iterable is None:
            raise TypeError("None is not iterable")
        if not hasattr(input_iterable, "__iter__"):
            raise TypeError("Object not iterable")

        results = []
        results_append = results.append
        for i in input_iterable:
            if not isinstance(i, basestring):
                try:
                    # Only numbers
                    float(i)
                    i = str(i)
                except TypeError:
                    continue

            # Remove line breaks and special chars
            v = i.replace("\n", "").replace("\t", "").replace("\r", "").strip()

            if v.startswith("#"):
                continue

            results_append(v)

        return results


#------------------------------------------------------------------------------
class WList(_AbstractWordlist):
    """
    Advanced wordlist that loads a wordlist as a read only list. This wordlist behaves
    as a list, removing break lines, carry returns and commented lines.

    Example:

        >>> from golismero.api.text.wordlist import WList
        >>> a = WList("./wordlist/golismero/no_spiderable_urls.txt")
        >>> "exit" in a
        True
        >>> for p in a:
        ...   print p
        ...
        logout
        logoff
        exit
        sigout
        signout
        delete
        remove

    This wordlist allow to do some operations with wordlists:
    - Search matches of a word in the wordlist.
    - Binary search in wordlist.
    - Get first coincidence, start at begining or end of list.
    - Search matches of wordlist with mutations.
    """

    #--------------------------------------------------------------------------
    def __init__(self, wordlist):
        """
        :param wordlist: a file descriptor of the wordlist.
        :type wordlist: file
        """
        if not isinstance(wordlist, file):
            raise TypeError("Expected file, got '%s' instead" % type(wordlist))

        #
        # To avoid to overload the memory, this class behaves like a generator until
        # any list method will called, like: len, getitem, contain...
        #
        # So it creates a copy of generator and it will use it to generate a common
        # list. Thus, it save memory and only use it if will needed.
        #
        self.__wordlist_iter, self.__wordlist_backup = tee(_simple_iterator(wordlist))
        self.__wordlist = None

    #--------------------------------------------------------------------------
    def __getitem__(self, i):
        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)
        return self.__wordlist[i]

    #--------------------------------------------------------------------------
    def __contains__(self, i):
        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)
        return i in self.__wordlist

    #--------------------------------------------------------------------------
    def __iter__(self):
        #return self.__wordlist.__iter__()
        for x in self.__wordlist_iter:
            r = x.replace("\n", "").replace("\t", "").replace("\r", "").strip()
            if r.startswith("#"):
                continue

            yield r

    #--------------------------------------------------------------------------
    def __len__(self):
        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)
        return len(self.__wordlist)

    #----------------------------------------------------------------------
    def __cmp__(self, other):
        if not isinstance(other, WList):
            raise TypeError("Expected other, got '%s' instead" % type(WList))

        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        s1 = set(self.__wordlist)
        s2 = set(other)

        result = s1.difference(s2)

        return -1 if result else 0

    #--------------------------------------------------------------------------
    # Operations
    #--------------------------------------------------------------------------
    def search(self, word, exact_search=True):
        """
        :return: a list of matches indexes
        :rtype: list(int)
        """
        if not isinstance(word, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(word))
        if not isinstance(exact_search, bool):
            raise TypeError("Expected bool, got '%s' instead" % type(exact_search))

        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        if exact_search:
            f = lambda x, b: x == b
        else:
            f = lambda x, b: x in b

        results = []
        results_append = results.append
        for i, x in enumerate(self.__wordlist):
            if f(word, x):
                results_append(i)

        if results:
            return results

        raise ValueError()

    #--------------------------------------------------------------------------
    def get_first(self, word, init=0, exact_search=True):
        if not isinstance(word, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(word))
        if not isinstance(exact_search, bool):
            raise TypeError("Expected bool, got '%s' instead" % type(exact_search))
        if not isinstance(init, int):
            raise TypeError("Expected int, got '%s' instead" % type(init))
        if init < 0:
            raise ValueError("Init value can't be lower than 0")

        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        if init > len(self.__wordlist):
            raise ValueError("Init word can't be greater than wordlist len")

        if exact_search:
            f = lambda x, b: x == b
        else:
            f = lambda x, b: x in b

        for i, x in enumerate(self.__wordlist[init:]):
            if f(word, x):
                return i + init

        raise ValueError()

    #--------------------------------------------------------------------------
    def get_rfirst(self, word, init=0, exact_search=True):
        if not isinstance(word, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(word))
        if not isinstance(exact_search, bool):
            raise TypeError("Expected bool, got '%s' instead" % type(exact_search))
        if not isinstance(init, int):
            raise TypeError("Expected int, got '%s' instead" % type(init))
        if init < 0:
            raise ValueError("Init value can't be lower than 0")

        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        if init > len(self.__wordlist):
            raise ValueError("Init word can't be greater than wordlist len")

        if exact_search:
            f = lambda x, b: x == b
        else:
            f = lambda x, b: x in b

        for i in xrange(len(self.__wordlist)):
            x = self.__wordlist[-i - init]
            if f(word, x):
                return len(self.__wordlist) - i - init

        raise ValueError()

    #--------------------------------------------------------------------------
    def clone(self):
        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        m_temp = copy.copy(self)

        return m_temp

    #--------------------------------------------------------------------------
    def pop(self):
        if self.__wordlist is None:
            self.__wordlist = self._raw_to_list(self.__wordlist_backup)

        return self.__wordlist.pop()


#------------------------------------------------------------------------------
class WDict(dict):
    """
    Advanced wordlist that loads a wordlist with a separator character as a dict, like:

    word list 1; second value of wordlist

    These line load as => {'word list 1':'second value of wordlist'}.
    """

    #--------------------------------------------------------------------------
    def __init__(self, wordlist, separator=";", smart_load=False):
        """
        Load a word list and conver it in a dict. The method used for the conversion
        are:

        Read line to line the file and split it using separatod specified as parameter. Then
        use the left value as key, and the right will be used as value of dict.

        .. note:
           If the file has repeated values for keys names, the values will be joined in the same
           key.

        Example:

        >>> f=open("wordlist.txt", "rU")
        >>> f.readlines()
        ['one; value1', 'two; value2', 'one; value3']
        >>> w = WDict("wordlist.txt")
        >>> w.matches_by_keys("one")
        {'one': [' value1', ' value3']}


        If you set to True the param 'smart_load', the WDict will try to detect if the values
        at the right of 'separator', found by the split, can be pooled as a list an put the values in it.

        Example:

        >>> f=open("wordlist.txt", "rU")
        >>> f.readlines()
        ['one; value1 value2, value3, value4 "value 5"', 'two; value6', 'one; value7']
        >>> w = WDict("wordlist.txt", smart_load=True)
        >>> w.matches_by_keys("one")
        {'one': ['value1', 'value2', 'value3', 'value4', 'value 5', 'value7']}


        :param wordlist: a file descriptor of the wordlist.
        :type wordlist: open()

        :param separator: value used to split the lines
        :type separator: str

        :param smart_load: Indicates if the wordlist must detect if the line has values that can be converted in a list.
        :type smart_load: bool
        """
        if not isinstance(wordlist, file):
            raise TypeError("Expected file, got '%s' instead" % type(wordlist))
        if not isinstance(smart_load, bool):
            raise TypeError("Expected bool, got '%s' instead" % type(smart_load))
        if not isinstance(separator, basestring):
            raise TypeError("Expected basestring, got '%s' instead" % type(separator))
        super(WDict, self).__init__()

        self.smart_load = smart_load
        regex = re.compile(r"([#A-Za-z\d]+|[\'\"][\w\d\s]+[\'\"])")

        for k in WList(wordlist):
            v = k.split(separator, 1)

            if len(v) < 2:
                continue

            dict_key = v[0]

            if smart_load:
                dict_values = [i.group(0).strip().replace("'", "").replace("\"", "")
                               for i in regex.finditer(v[1])
                               if i is not None]

                try:
                    self[dict_key].extend(dict_values)
                except KeyError:
                    self[dict_key] = []
                    self[dict_key].extend(dict_values)
            else:
                self[dict_key] = v[1]

    #--------------------------------------------------------------------------
    def search_in_values(self, word):
        """
        Search a word passed as parameter in keys's values and return dict with the matched keys and
        level of correspondence.

        The matching level is a value between 0-1.

        >>> info = ["hello world#key11, key12, key13", "bye world#key21,key22", "bye bye#key31,32"]
        >>> open("mywordlist.txt", "w").writelines(info)
        >>> w=WDict(file("mywordlist.txt"), separator="#", smart_load=True)
        >>> print w.search_in_values("key1")
        {"hello world" : [("key11", 0.89), ("key12", 0.89), ("key13", 0.89)]}
        >>> w=WDict(file("mywordlist.txt"), separator="#")
        >>> print w.search_in_values("key1")
        {"hello world" : [("key11, key12, key13", 0.35)]}

        :param word: word to search.
        :type word: str.

        :return: a list with matches and correpondences.
        :rtype: { KEY: list(INDEX, LEVEL)}
        """
        if not isinstance(word, str):
            raise TypeError("Expected basestring, got '%s' instead" % type(word))

        results = {}
        for v in self.iterkeys():
            match_tuple = []

            # Smart load enabled?
            if self.smart_load:
                match_tuple = [(x, round(get_diff_ratio(word, x), 2)) for x in self[v] if word in x]
            else:
                if word in self[v]:
                    match_tuple = [(self[v], round(get_diff_ratio(word, self[v]), 2))]

            # Append results
            if match_tuple:
                results[v] = match_tuple

        return results


#------------------------------------------------------------------------------
# Singleton.
WordListLoader = _WordListLoader()
