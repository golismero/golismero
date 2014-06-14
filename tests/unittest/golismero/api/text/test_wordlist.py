#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import pytest

from golismero.api.text.wordlist import WordListLoader, WordlistNotFound, _AbstractWordlist, WList, WDict
from golismero.api.localfile import LocalFile


#----------------------------------------------------------------------
# Aux functions
#----------------------------------------------------------------------
W_DIR = "plugin_tmp_dir"
W_NAME = "test_wordlist.txt"
W_PATH = os.path.join(W_DIR, W_NAME)


#----------------------------------------------------------------------
def _create_plugin_info():
    """Creates plugin folders and files"""
    # Create folder and wordlist file
    try:
        os.mkdir(W_DIR)
        open(W_PATH, "w").write("hello world  \t\n  \tbye world \n bye bye\n # see u!   ")
    except os.error:
        pass


#----------------------------------------------------------------------
def _create_plugin_info_dict():
    """Creates plugin folders and files"""
    # Create folder and wordlist file
    try:
        os.mkdir(W_DIR)
        open(W_PATH, "w").write("hello world#key11, key12, key13\t\n  \tbye world#key21,key22 \nbye bye#key31,32")
    except os.error:
        pass


#----------------------------------------------------------------------
def _destroy_plugin_info():
    """Destroy plugin folders and files"""
    try:
        os.remove(W_PATH)
        os.rmdir(W_DIR)
    except os.error:
        pass


#----------------------------------------------------------------------
@pytest.fixture
def simulate_wordlist():
    """Generates a list as word list does"""
    return set((x for x in ["hello world  \t\n", "  \tbye world \n", " bye bye\n", " # see u!   "]))


#----------------------------------------------------------------------
@pytest.fixture
def simulate_wordlist_without_carry():
    """Generates a list as word list does"""
    return set((x for x in ["hello world", "bye world", "bye bye"]))


#----------------------------------------------------------------------
@pytest.fixture
def simulate_wordlist_for_dict():
    """Generates a list as word list does"""
    return set((x for x in ["hello world#key11, key12, key13", "bye world#key21,key22", "bye bye#key31,32"]))


#--------------------------------------------------------------------------
# WordListLoader test
#--------------------------------------------------------------------------
class TestWordListLoader:

    #----------------------------------------------------------------------
    # ___load_wordlists_types Tests
    #----------------------------------------------------------------------
    def test__load_wordlists_types(self):
        pytest.raises(TypeError, WordListLoader._WordListLoader__load_wordlists, -1)
        pytest.raises(TypeError, WordListLoader._WordListLoader__load_wordlists, [])
        pytest.raises(TypeError, WordListLoader._WordListLoader__load_wordlists, dict())

    #----------------------------------------------------------------------
    def test__load_wordlists_not_exits(self):
        pytest.raises(ValueError, WordListLoader._WordListLoader__load_wordlists, "aaaaa")

    #----------------------------------------------------------------------
    def test__load_wordlists_input(self):
        # Reload wordlist
        WordListLoader._WordListLoader__load_wordlists("../../wordlist")

        # Check
        assert len(WordListLoader._WordListLoader__store) != 0

    #----------------------------------------------------------------------
    # __get_wordlist_descriptor Tests
    #----------------------------------------------------------------------
    def test__get_wordlist_descriptor_types(self):
        pytest.raises(TypeError, WordListLoader._WordListLoader__get_wordlist_descriptor, -1)
        pytest.raises(TypeError, WordListLoader._WordListLoader__get_wordlist_descriptor, [])
        pytest.raises(TypeError, WordListLoader._WordListLoader__get_wordlist_descriptor, dict())

    #----------------------------------------------------------------------
    def test__get_wordlist_descriptor_empty_input(self):
        pytest.raises(ValueError, WordListLoader._WordListLoader__get_wordlist_descriptor, "")

    #----------------------------------------------------------------------
    def test__get_wordlist_descriptor_not_exits_abs_path(self):
        LocalFile._LocalFile__plugin_path = os.getcwd()
        pytest.raises(WordlistNotFound, WordListLoader._WordListLoader__get_wordlist_descriptor, "aaaaa")

    #----------------------------------------------------------------------
    def test__get_wordlist_descriptor_exits_abs_path(self):
        # Config plugin
        LocalFile._LocalFile__plugin_path = os.getcwd()

        _create_plugin_info()

        try:
            wordlist_file = WordListLoader._WordListLoader__get_wordlist_descriptor(W_PATH)

            # Checks if wordlist is file
            wordlist_file == open(W_PATH, "rU")

            # Checks if wordlist is non file
            pytest.raises(WordlistNotFound, WordListLoader._WordListLoader__get_wordlist_descriptor, W_DIR)
        finally:
            _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test__get_wordlist_descriptor_exits_in_plugin_path(self):
        # Config plugin
        LocalFile._LocalFile__plugin_path = os.path.abspath(W_DIR)

        _create_plugin_info()

        try:
            wordlist_file = WordListLoader._WordListLoader__get_wordlist_descriptor(W_PATH)

            # Checks if wordlist is file
            wordlist_file == wordlist_file == open(W_PATH, "rU")

            # Checks if wordlist is non file
            pytest.raises(WordlistNotFound, WordListLoader._WordListLoader__get_wordlist_descriptor, "plugin_tmp_dir")
        finally:
            _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test__get_wordlist_with_word_wordlist(self):
        LocalFile._LocalFile__plugin_path = os.getcwd()
        pytest.raises(ValueError, WordListLoader._WordListLoader__get_wordlist_descriptor, "wordlist")

    #----------------------------------------------------------------------
    def test_file_permissions(self):
        _create_plugin_info()

        os.chmod(W_PATH, 0244)

        pytest.raises(IOError, WordListLoader._WordListLoader__get_wordlist_descriptor, W_PATH)

        _destroy_plugin_info()

    #--------------------------------------------------------------------------
    # all_wordlist property test
    #----------------------------------------------------------------------
    def test_all_wordlist_property(self):
        # Set Config plugin
        LocalFile._LocalFile__plugin_path = os.path.abspath(W_DIR)

        # Create plugin wordlists
        _create_plugin_info()

        # Clean and configure new store
        WordListLoader._WordListLoader__store = {}
        WordListLoader._WordListLoader__load_wordlists(W_DIR)

        try:
            assert WordListLoader.all_wordlists == ["test_wordlist.txt"]
        finally:
            _destroy_plugin_info()


#--------------------------------------------------------------------------
# Raw2list in Abstract test
#--------------------------------------------------------------------------
class Concrete(_AbstractWordlist):
    def get_first(self, word, init=0):
        pass

    def search(self, word, low_pos=0, high_pos=None):
        pass

    def search_mutations(self, word, rules):
        pass

    def clone(self):
        pass

    def get_rfirst(self, word, init=0):
        pass


#--------------------------------------------------------------------------
class TestRaw2List:
    #----------------------------------------------------------------------
    def setup_class(self):
        """Comment"""
        self.o = Concrete()
        self.func = self.o._raw_to_list

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, self.func, None)
        pytest.raises(TypeError, self.func, 0)
        pytest.raises(TypeError, self.func, "")

    #----------------------------------------------------------------------
    def test_empty_input(self):
        assert self.func([]) == []

    #----------------------------------------------------------------------
    def test_empty_wrong_input(self):
        assert self.func([1, 2, "a"]) == ["1", "2", "a"]
        assert self.func([1, "ñ", "a"]) == ["1", "\xc3\xb1", "a"]
        assert self.func([1.1, "b", "a"]) == ["1.1", "b", "a"]
        assert self.func([[], "c", "a"]) == ["c", "a"]

    #----------------------------------------------------------------------
    def test_input(self):
        # Normal
        assert self.func(["hello", "world"]) == ["hello", "world"]
        # With trailer
        assert self.func(["hello    ", "    world"]) == ["hello", "world"]
        # With special chars
        assert self.func(["hello    \n   ", " \t \r  world"]) == ["hello", "world"]


#--------------------------------------------------------------------------
# Raw wordlist test
#--------------------------------------------------------------------------
class TestWordListsAsRaw:

    #----------------------------------------------------------------------
    def setup_class(self):
        """Comment"""
        self.func = WordListLoader.get_wordlist_as_raw

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, self.func, None)
        pytest.raises(TypeError, self.func, 0)
        pytest.raises(TypeError, self.func, [])
        pytest.raises(TypeError, self.func, dict())

    #----------------------------------------------------------------------
    def test_empty_input(self):
        pytest.raises(ValueError, self.func, "")

    #----------------------------------------------------------------------
    def test_input(self, simulate_wordlist):
        _create_plugin_info()

        # Check for types
        assert type(self.func(W_NAME)) == type(file(W_PATH))

        # Check for values in generators
        s1 = set(self.func(W_PATH).readlines())

        assert s1.difference(simulate_wordlist) == set([])

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_empty_non_exits(self):
        pytest.raises(WordlistNotFound, self.func, "asdfasdf")

    #----------------------------------------------------------------------
    def test_file_permissions(self):
        _create_plugin_info()

        os.chmod(W_PATH, 0244)

        pytest.raises(IOError, self.func, W_PATH)

        _destroy_plugin_info()


#--------------------------------------------------------------------------
# Raw wordlist test
#--------------------------------------------------------------------------
class TestWordListsAsList:

    #----------------------------------------------------------------------
    def setup_class(self):
        self.func = WordListLoader.get_wordlist_as_list

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, self.func, None)
        pytest.raises(TypeError, self.func, 0)
        pytest.raises(TypeError, self.func, [])
        pytest.raises(TypeError, self.func, dict())
        pytest.raises(TypeError, WList, None)

    #----------------------------------------------------------------------
    def test_empty_input(self):
        pytest.raises(ValueError, self.func, "")

    #----------------------------------------------------------------------
    def test_empty_non_exits(self):
        pytest.raises(WordlistNotFound, self.func, "asdfasdf")

    #----------------------------------------------------------------------
    def test_file_permissions(self):
        _create_plugin_info()

        os.chmod(W_PATH, 0244)

        pytest.raises(IOError, self.func, W_PATH)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_return_type(self):
        _create_plugin_info()

        # Check for types
        assert isinstance(self.func(W_PATH), WList)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_normal_list_behavior(self, simulate_wordlist_without_carry):
        _create_plugin_info()

        s1 = set(self.func(W_PATH))

        assert s1.difference(simulate_wordlist_without_carry) == set([])

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # Common list operations
    #----------------------------------------------------------------------
    def test_common_list_operations(self):
        _create_plugin_info()

        # Test each function with a different list to test the creation of
        # wordlist when it is called
        r1 = self.func(W_PATH)

        # Check len
        assert len(r1) == 3

        r2 = self.func(W_PATH)
        # Check getitem
        assert r2[0] == "hello world"

        # Check setitem
        r3 = self.func(W_PATH)
        assert "hello world" in r3

        # Check cmp
        r4 = self.func(W_PATH)
        pytest.raises(TypeError, r4.__cmp__, None)
        assert r4 == r3

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # Search operation
    #----------------------------------------------------------------------
    def test_search_operation_types(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        pytest.raises(TypeError, r.search, 0)
        pytest.raises(TypeError, r.search, "aa", None)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_search_operation_not_found(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search aprox
        pytest.raises(ValueError, r.search, "world")

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_search_operation_inputs(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search not found

        # Exact search exact
        assert r.search("bye world") == [1]

        # Search aprox
        assert r.search("bye", exact_search=False) == [1, 2]
        assert r.search("world", exact_search=False) == [0, 1]

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # get_first operation
    #----------------------------------------------------------------------
    def test_get_first_operation_types_and_limits(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # First value
        pytest.raises(TypeError, r.get_first, 0)

        # Second value
        pytest.raises(TypeError, r.get_first, "Word", None)
        pytest.raises(TypeError, r.get_first, "Word", "")
        pytest.raises(ValueError, r.get_first, "Word", -1)
        pytest.raises(ValueError, r.get_first, "Word", 1000)

        # Third value
        pytest.raises(TypeError, r.get_first, "Word", 0, None)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_first_operation_not_found(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search aprox
        pytest.raises(ValueError, r.get_first, "world")

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_first_operation_inputs(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search exact
        assert r.get_first("bye world") == 1

        # Search aprox
        assert r.get_first("world", exact_search=False) == 0

        # Search in init 1 slot
        assert r.get_first("world", init=1, exact_search=False) == 1

    #----------------------------------------------------------------------
    # get_rfirst operation
    #----------------------------------------------------------------------
    def test_get_rfirst_operation_types_and_limits(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # First value
        pytest.raises(TypeError, r.get_rfirst, 0)

        # Second value
        pytest.raises(TypeError, r.get_rfirst, "Word", None)
        pytest.raises(TypeError, r.get_rfirst, "Word", "")
        pytest.raises(ValueError, r.get_rfirst, "Word", -1)
        pytest.raises(ValueError, r.get_rfirst, "Word", 1000)

        # Third value
        pytest.raises(TypeError, r.get_rfirst, "Word", 0, None)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_rfirst_operation_not_found(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search aprox
        pytest.raises(ValueError, r.get_rfirst, "world")

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_rfirst_operation_inputs(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        # Search exact
        assert r.get_rfirst("bye world") == 1

        # Search aprox
        assert r.get_rfirst("bye", exact_search=False) == 2

        # Search in init 1 slot
        assert r.get_rfirst("world", init=1, exact_search=False) == 1

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # clone operation
    #----------------------------------------------------------------------
    def test_get_clone_operation_result_types(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        assert isinstance(r.clone(), WList)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_clone_verify_result(self):
        _create_plugin_info()

        # Basic cmp
        l1 = self.func(W_PATH)
        l_clone = l1.clone()

        assert l1 == l_clone

        # Modify list value
        l_clone._WList__wordlist.append("aaa")
        assert l1 != l_clone

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # Pop operation
    #----------------------------------------------------------------------
    def test_get_pop_operation_check_length(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        assert len(r) == 3

        r.pop()

        assert len(r) == 2

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_get_pop_operation_check_iter(self):
        _create_plugin_info()

        r = self.func(W_PATH)

        r.pop()
        r.pop()
        r.pop()
        pytest.raises(IndexError, r.pop)

        _destroy_plugin_info()


#--------------------------------------------------------------------------
# WDict test
#--------------------------------------------------------------------------
class TestWDict:

    #----------------------------------------------------------------------
    def setup_class(self):
        self.func = WordListLoader.get_wordlist_as_dict

    #----------------------------------------------------------------------
    def test_types(self):
        _create_plugin_info_dict()

        pytest.raises(TypeError, self.func, None)
        pytest.raises(TypeError, self.func, 0)
        pytest.raises(TypeError, self.func, [])
        pytest.raises(TypeError, self.func, dict())
        pytest.raises(TypeError, WDict, None)
        pytest.raises(TypeError, WDict, file(W_PATH), None)
        pytest.raises(TypeError, WDict, file(W_PATH), "##", None)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_empty_input(self):
        pytest.raises(ValueError, self.func, "")

    #----------------------------------------------------------------------
    def test_empty_non_exits(self):
        pytest.raises(WordlistNotFound, self.func, "asdfasdf")

    #----------------------------------------------------------------------
    def test_file_permissions(self):
        _create_plugin_info_dict()

        os.chmod(W_PATH, 0244)

        pytest.raises(IOError, self.func, W_PATH)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_return_type(self):
        _create_plugin_info_dict()

        # Check for types
        assert isinstance(self.func(W_PATH), WDict)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # Common dict operations
    #----------------------------------------------------------------------
    def test_normal_list_behavior_without_smart_load(self):
        _create_plugin_info_dict()

        wd = self.func(W_PATH, separator="#")

        # Keys
        s1 = set(["hello world", "bye world", "bye bye"])
        assert set(wd.keys()).difference(s1) == set([])

        # Check values
        assert wd["hello world"] == "key11, key12, key13"

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_normal_list_behavior_witho_smart_load(self):
        _create_plugin_info_dict()

        wd = self.func(W_PATH, separator="#", smart_load=True)

        # Keys
        s1 = set(["hello world", "bye world", "bye bye"])
        assert set(wd.keys()).difference(s1) == set([])

        # Check values
        assert wd["hello world"] == ["key11", "key12", "key13"]

        # Len
        assert len(wd) == 3

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    # search dict operations
    #----------------------------------------------------------------------
    def test_search_types(self):
        _create_plugin_info_dict()

        r = self.func(W_PATH, separator="#")

        pytest.raises(TypeError, r.search_in_values, None)

        _destroy_plugin_info()

    #----------------------------------------------------------------------
    def test_search_in_values(self):
        _create_plugin_info_dict()

        # Without smart load
        r = self.func(W_PATH, separator="#")
        matched = {'hello world': [("key11, key12, key13", 0.35)]}

        assert r.search_in_values("key1") == matched

        # With smart load
        r2 = self.func(W_PATH, separator="#", smart_load=True)
        matched_smart_load = {'hello world': [("key11", 0.89), ("key12", 0.89), ("key13", 0.89)]}

        assert r2.search_in_values("key1") == matched_smart_load

        _destroy_plugin_info()
