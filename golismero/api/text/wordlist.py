#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wordlist API.
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

__all__ = ["WordListLoader"]

from os import walk
from os.path import join, sep, abspath
from golismero.api.text.matching_analyzer import get_diff_ratio
from golismero.api.file import FileManager
import bisect
import re
import copy

from ..logger import Logger
from ...common import Singleton, get_wordlists_folder


#------------------------------------------------------------------------------
class _WordListLoader(Singleton):
    """
    Wordlist API.
    """


    #----------------------------------------------------------------------
    def __init__(self):

        # Store
        self.__store = {} # Pair with: (name, path)

        # Initial load
        self.__load_wordlists( get_wordlists_folder() )


    #----------------------------------------------------------------------
    def __resolve_wordlist_name(self, wordlist):
        """
        Looking for the world list name in the internal database and, if it's fails,
        looking in the plugin directory.

        :param wordlist: wordlist name
        :type wordlist: str

        :return: a file descriptor.
        :rtype: open()
        """
        if not wordlist:
            raise ValueError("Wordlist name can't be an empty value")
        if not isinstance(wordlist, basestring):
            raise TypeError("Expected 'str' got '%s'." % type(wordlist))

        m_return = None

        try:
            m_return = open(self.__store[wordlist], "rU")
        except KeyError: # Wordlist is not in the internal database
            # Exits the file
            if not FileManager.exists(wordlist):
                raise IOError("Wordlist file '%s' does not exist." % wordlist)
            if not FileManager.isfile(wordlist):
                raise TypeError("Wordlist '%s' is not a file." % wordlist)

            m_return = FileManager.open(wordlist, "rU")

        return m_return


    #----------------------------------------------------------------------
    def __load_wordlists(self, currentDir):
        """
        Find and load wordlists from the specified directory.

        .. warning: Private method, do not call!

        :param currentDir: Directory to look for wordlists.
        :type currentDir: str
        """

        # Make sure the directory name is absolute and ends with a slash.
        currentDir = abspath(currentDir)
        if not currentDir.endswith(sep):
            currentDir += sep

        # Iterate the directory recursively.
        for (dirpath, _, filenames) in walk(currentDir):

            # Make sure the directory name is absolute.
            dirpath = abspath(dirpath)

            # Look for text files, skipping README files and disabled lists.
            for fname in filenames:
                if not fname.startswith("_") and fname.lower() != "readme.txt":

                    # Map the relative filename to the absolute filename,
                    # replacing \ for / on Windows.
                    target = join(dirpath, fname)
                    key = target[len(currentDir):]
                    if sep != "/":
                        key = key.replace(sep, "/")
                    self.__store[key] = target


    #----------------------------------------------------------------------
    @property
    def all_wordlists(self):
        """
        :returns: Names of all the wordlists.
        :rtype: list
        """
        return self.__store.keys()


    #----------------------------------------------------------------------
    def get_wordlist(self, wordlist_name):
        """
        :param wordlist_name: Name of the requested wordlist.
        :type wordlist_name: str

        :returns: Iterator for the selected wordlist.
        :rtype: iter(str)
        """

        return SimpleWordList(self.__resolve_wordlist_name(wordlist_name))


    #----------------------------------------------------------------------
    def get_advanced_wordlist_as_dict(self, wordlist, separator=";", smart_load=False):
        """
        Get an AdvancedDicWordlist.


        :param wordlist_name: Name of the requested advanced wordlist.
        :type wordlist_name: str

        :param separator: value used to split the lines
        :type separator: str

        :param inteligence_load: Indicates if the wordlist must detect if the line has values that can be converted in a list.
        :type inteligence_load: bool

        :returns: Advanced wordlist object.
        :rtype: AdvancedDicWordlist
        """

        return AdvancedDicWordlist(self.__resolve_wordlist_name(wordlist), smart_load, separator)


    #----------------------------------------------------------------------
    def get_advanced_wordlist_as_list(self, wordlist_name):
        """
        Get an AdvancedListWordlist.

        :param wordlist_name: Name of the requested advanced wordlist.
        :type wordlist_name: str

        :returns: AdvancedListWordlist.
        :rtype: AdvancedListWordlist
        """

        return AdvancedListWordlist(self.__resolve_wordlist_name(wordlist_name))


#------------------------------------------------------------------------------
def SimpleWordList(wordlist):
    """
    Load a wordlist from a file and iterate its words.

    :param wordlist: a file descriptor of the wordlist.
    :type wordllist: open()
    """

    try:
        for line in wordlist:
            line = line.strip()
            if line and not line.startswith("#"):
                yield line

    except IOError, e:
        Logger.log_error("Error opening wordlist. Error: %s " % str(e))


#------------------------------------------------------------------------------
class AbstractWordlist(object):
    """
    Base class for advanced wordlists.
    """


    #----------------------------------------------------------------------
    def binary_search(self, word, low_pos=0, high_pos=None):
        """
        Makes a binary search in the list and return the position of the word.

        Raises a ValueError exception if no coincidence found.

        low_pos and high_pos specifies the range between the function will search.

        :param word: The word to find.
        :type word: str

        :param low_pos: initial postion to the function starts searching.
        :type low_pos: Int

        :param high_pos: End postion to the function starts searching.
        :type high_pos: Int|None

        :return: Get the position fo the first search value.
        :rtype: Int

        :raises: ValueError
        """
        raise NotImplementedError()


    #----------------------------------------------------------------------
    def get_first(self, word, init=0):
        """
        Get first coincidence, starting at begining. Raises a ValueError exception
        if no coincidence found.

        :param init: initial postion to the function starts searching.
        :type init: Int

        :return: Value of the first element found.
        :rtype: str

        :raises: ValueError
        """
        raise NotImplementedError()


    #----------------------------------------------------------------------
    def get_rfirst(self, word, init=0):
        """
        Get first coincidence, starting from the end. Raises a ValueError exception
        if no coincidence found.

        :param init: initial postion to the function starts searching.
        :type init: Int

        :return: Value of the first element found, stating at the end.
        :rtype: str

        :raises: ValueError
        """
        raise NotImplementedError()


    #----------------------------------------------------------------------
    def search_mutations(self, word, rules):
        raise NotImplementedError()


    #----------------------------------------------------------------------
    def clone(self):
        """
        This method makes a clone of the object.

        :return: A copy of this object.
        """
        raise NotImplementedError()


#------------------------------------------------------------------------------
class AdvancedListWordlist(AbstractWordlist):
    """
    Advanced wordlist that loads a wordlist as a list. This wordlist behaves
    as a list.

    Example:

        >>> from golismero.api.text.wordlist import AdvancedListWordlist
        >>> a = AdvancedListWordlist("./wordlist/golismero/no_spiderable_urls.txt")
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


    #----------------------------------------------------------------------
    def __init__(self, wordlist):
        """
        :param wordlist: a file descriptor of the wordlist.
        :type wordllist: open()
        """

        if not wordlist:
            raise ValueError("Got empty wordlist")

        try:
            self.__wordlist = list( SimpleWordList(wordlist) )
        except IOError, e:
            raise IOError("Error when trying to open wordlist: %s" + str(e))


    #----------------------------------------------------------------------
    def __getitem__(self, i):
        return self.__wordlist[i]


    #----------------------------------------------------------------------
    def __setitem__(self, i, v):
        self.__wordlist[i] = v


    #----------------------------------------------------------------------
    def __contains__(self, i):
        return i in self.__wordlist


    #----------------------------------------------------------------------
    def __iter__(self):
        return self.__wordlist.__iter__()


    #----------------------------------------------------------------------
    def __len__(self):
        return len(self.__wordlist)


    #----------------------------------------------------------------------
    def binary_search(self, word, low_pos=0, high_pos=None):
        i = bisect.bisect_left(self.__wordlist, word, lo=low_pos, hi=high_pos if high_pos else len(high_pos))

        if i != len(self.__wordlist) and self.__wordlist[i] == word:
            return i

        raise ValueError()


    #----------------------------------------------------------------------
    def get_first(self, word, init=0):
        """
        Get first coincidence, starting at begining.
        """
        i = bisect.bisect_left(self.__wordlist, word, lo=init)

        if i:
            return i

        raise ValueError()


    #----------------------------------------------------------------------
    def get_rfirst(self, word, init=0):
        """
        Get first coincidence, starting at begining.
        """
        i = bisect.bisect_right(self.__wordlist, word, lo=init)

        if i:
            return i

        raise ValueError()


    #----------------------------------------------------------------------
    def clone(self):
        m_temp = copy.copy(self)
        m_temp.__wordlist = copy.copy(self.__wordlist)

        return m_temp


    #----------------------------------------------------------------------
    def pop(self):
        return self.__wordlist.pop()


#------------------------------------------------------------------------------
class AdvancedDicWordlist(object):
    """
    Advanced wordlist that loads a wordlist with a separator character as a dict, like:

    word list 1; sencond value of wordlist

    These line load as => {'word list 1':'sencond value of wordlist'}.
    """


    #----------------------------------------------------------------------
    def __init__(self, wordlist, smart_load=False, separator = ";"):
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
        >>> w = AdvancedDicWordlist("wordlist.txt")
        >>> w.matches_by_keys("one")
        {'one': [' value1', ' value3']}


        If you set to True the param 'smart_load', the AdvancedDicWordlist will try to detect if the values
        at the right of 'separator', found by the split, can be pooled as a list an put the values in it.

        Example:

        >>> f=open("wordlist.txt", "rU")
        >>> f.readlines()
        ['one; value1 value2, value3, value4 "value 5"', 'two; value6', 'one; value7']
        >>> w = AdvancedDicWordlist("wordlist.txt", smart_load=True)
        >>> w.matches_by_keys("one")
        {'one': ['value1', 'value2', 'value3', 'value4', 'value 5', 'value7']}


        :param wordlist: a file descriptor of the wordlist.
        :type wordllist: open()

        :param separator: value used to split the lines
        :type separator: str

        :param smart_load: Indicates if the wordlist must detect if the line has values that can be converted in a list.
        :type smart_load: bool
        """

        if not wordlist:
            raise ValueError("Empty wordlist got")
        if not separator:
            raise ValueError("Empty separator got")

        m_tmp_wordlist = None
        try:
            m_tmp_wordlist = wordlist.readlines()
        except IOError, e:
            raise IOError("Error when trying to open wordlist. Error: %s" % str(e))

        self.__wordlist = {}
        m_reg           = re.compile(r"([#A-Za-z\d]+|[\'\"][\w\d\s]+[\'\"])")
        for k in m_tmp_wordlist:
            v = k.replace("\n","").replace("\r","").split(separator,1)

            if len(v) < 2:
                continue

            if smart_load:
                m_values = [i.group(0).strip().replace("'","").replace("\"","") for i in m_reg.finditer(v[1])]

                try:
                    self.__wordlist[v[0]].extend(m_values)
                except KeyError:
                    self.__wordlist[v[0]] = []
                    self.__wordlist[v[0]].extend(m_values)
            else:
                try:
                    self.__wordlist[v[0]].append(v[1])
                except KeyError:
                    self.__wordlist[v[0]] = []
                    self.__wordlist[v[0]].append(v[1])


    #----------------------------------------------------------------------
    def matches_by_keys(self, word):
        """
        Search a word passed as parameter in the keys's wordlist and return a list of lists with
        matches found.

        :param word: word to search.
        :type word: str.

        :return: a list with matches.
        :rtype: dict(KEY, list(VALUES))
        """

        if not word:
            return {}

        word = str(word)

        return { i:v for i, v in self.__wordlist.iteritems() if word == i}


    #----------------------------------------------------------------------
    def matches_by_key_with_level(self, word):
        """
        Search a word passed as parameter in keys's wordlist and return a list of dicts with
        matches and level of correspondence.

        The matching level is a value between 0-1.

        :param word: word to search.
        :type word: str.

        :return: a list with matches and correpondences.
        :rtype: list(list(KEY, VALUE, LEVEL))
        """

        if not word:
            return [[]]

        word = str(word)

        m_return        = set()
        m_return_append = m_return.add
        for i, v in self.__wordlist.iteritems():
            if word in i:
                continue

            m_return_append((i, v, get_diff_ratio(word, i)))

        return m_return


    #----------------------------------------------------------------------
    def matches_by_value(self, word, debug = False):
        """
        Search a word passed as parameter in the values of wordlist and return a list of lists with
        matches found.

        :param word: word to search.
        :type word: str.

        :return: a list with matches.
        :rtype: dict(KEY, list(VALUES))
        """

        if not word:
            return {}

        word = str(word)

        m_return = {}

        for k, v in self.__wordlist.iteritems():
            if word not in v:
                continue

            for l in v:
                if word == l:
                    try:
                        m_return[k].add(l)
                    except KeyError:
                        m_return[k] = set()
                        m_return[k].add(l)

        return m_return


    #----------------------------------------------------------------------
    def matches_by_value_with_level(self, word):
        """
        Search a word passed as parameter in values of wordlist and return a list of dicts with
        matches and level of correspondence.

        The matching level is a value between 0-1.

        :param word: word to search.
        :type word: str.

        :return: a list with matches and correpondences.
        :rtype: list(list(KEY, VALUE, LEVEL))
        """

        if not word:
            return []

        word = str(word)

        m_return        = set()
        m_return_append = m_return.add
        for v in self.__wordlist.itervalues():
            if word not in v:
                continue

            for l in v:
                if word == l:
                    m_return_append((l, v, get_diff_ratio(word, l)))

        return m_return


    #----------------------------------------------------------------------
    def __getitem__(self, i):
        return self.__wordlist[i]


    #----------------------------------------------------------------------
    def __setitem__(self, i, v):
        if not isinstance(v, list):
            raise ValueError("Excepted list type. Got '%s'" % type(v))

        self.__wordlist[i] = v


    #----------------------------------------------------------------------
    def __contains__(self, i):
        return i in self.__wordlist


    #----------------------------------------------------------------------
    def iteritems(self):
        return self.__wordlist.iteritems()


    #----------------------------------------------------------------------
    def __iter__(self):
        return self.__wordlist.__iter__


    #----------------------------------------------------------------------
    def __len__(self):
        return len(self.__wordlist)


    #----------------------------------------------------------------------
    def itervalues(self):
        return self.__wordlist.itervalues()


    #----------------------------------------------------------------------
    def iterkeys(self):
        return self.__wordlist.iterkeys()


    #----------------------------------------------------------------------
    def clone(self):
        m_temp = copy.copy(self)
        m_temp.__wordlist = copy.copy(self.__wordlist)

        return m_temp


#--------------------------------------------------------------------------
# Singleton.
WordListLoader = _WordListLoader()
