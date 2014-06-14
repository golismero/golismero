#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from golismero.api.text.text_utils import \
    char_count, line_count, word_count, generate_random_string, \
    uncamelcase, hexdump, to_utf8, split_first


#--------------------------------------------------------------------------
# Char count tests
#--------------------------------------------------------------------------
class TestCharCount:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, char_count, None)
        pytest.raises(TypeError, char_count, 0)
        pytest.raises(TypeError, char_count, [])
        pytest.raises(TypeError, char_count, dict())

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert char_count("") == 0

    #----------------------------------------------------------------------
    def test_chars(self):
        assert char_count("hello") == 5
        assert char_count("hello   world") == 10


#--------------------------------------------------------------------------
# Line count test
#--------------------------------------------------------------------------
class TestLineCount:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, line_count, None)
        pytest.raises(TypeError, line_count, 0)
        pytest.raises(TypeError, line_count, [])
        pytest.raises(TypeError, line_count, dict())

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert line_count("") == 1

    #----------------------------------------------------------------------
    def test_chars(self):
        assert line_count("hello\nword") == 2


#--------------------------------------------------------------------------
# Word count test
#--------------------------------------------------------------------------
class TestWordCount:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, word_count, None)
        pytest.raises(TypeError, word_count, 0)
        pytest.raises(TypeError, word_count, [])
        pytest.raises(TypeError, word_count, dict())

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert word_count("") == 0

    #----------------------------------------------------------------------
    def test_chars(self):
        assert word_count("hello\nworld\t\n") == 2


#--------------------------------------------------------------------------
# Generate Random String test
#--------------------------------------------------------------------------
class TestGenerateRadomString:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, generate_random_string, None)
        pytest.raises(TypeError, generate_random_string, "a")
        pytest.raises(TypeError, generate_random_string, [])
        pytest.raises(TypeError, generate_random_string, dict())

    #----------------------------------------------------------------------
    def test_negative(self):
        assert len(generate_random_string(-4)) == 0

    #----------------------------------------------------------------------
    def test_input(self):
        assert len(generate_random_string(40)) == 40


#--------------------------------------------------------------------------
# UnCamelCase test
#--------------------------------------------------------------------------
class TestUnCamelCase:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, uncamelcase, None)
        pytest.raises(TypeError, uncamelcase, 0)
        pytest.raises(TypeError, uncamelcase, [])
        pytest.raises(TypeError, uncamelcase, dict())

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert uncamelcase("") == ""

    #----------------------------------------------------------------------
    def test_input(self):
        assert uncamelcase("lowercase") == "lowercase"
        assert uncamelcase("Class") == "Class"
        assert uncamelcase("MyClass") == "My Class"
        assert uncamelcase("PDFClass") == "PDF Class"
        assert uncamelcase("99bottles") == "99bottles"
        assert uncamelcase("99Bottles") == "99 Bottles"
        assert uncamelcase("BFG9000") == "BFG 9000"


#--------------------------------------------------------------------------
# Hexdump test
#--------------------------------------------------------------------------
class TestHexDump:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, hexdump, None)
        pytest.raises(TypeError, hexdump, 0)
        pytest.raises(TypeError, hexdump, dict())

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert hexdump("") == ""

    #----------------------------------------------------------------------
    def test_input(self):
        assert hexdump("A") == "41                              -                                 A\n"
        assert hexdump("ÑaB") == "c3 91 61 42                     -                                 ..aB\n"


#--------------------------------------------------------------------------
# To UTF-8 test
#--------------------------------------------------------------------------
def test_empty_input():
    assert to_utf8(u"ÑAAA".encode("UTF-16")) == "\xff\xfe\xd1\x00A\x00A\x00A\x00"
    assert to_utf8(u"ÑAAA".encode("UTF-8")) == "\xc3\x91AAA"
    assert to_utf8(u"ÑAAA".encode("iso-8859-15")) == "\xd1AAA"
    assert to_utf8(u"ÑAAA".encode("iso-8859-1")) == "\xd1AAA"
    assert to_utf8(u"ÑAAA".encode("latin1")) == "\xd1AAA"
    assert to_utf8(0) == 0
    assert to_utf8(None) is None
    assert to_utf8([]) == []
    assert to_utf8(bin(0101)) == '0b1000001'


#--------------------------------------------------------------------------
# Split_first test
#--------------------------------------------------------------------------
class TestSplitFirst:

    #----------------------------------------------------------------------
    def test_types_param_1(self):
        pytest.raises(TypeError, split_first, None, None)
        pytest.raises(TypeError, split_first, 0, None)
        pytest.raises(TypeError, split_first, [], None)
        pytest.raises(TypeError, split_first, dict(), None)

    #----------------------------------------------------------------------
    def test_types_param_2(self):
        pytest.raises(TypeError, split_first, "", None)
        pytest.raises(TypeError, split_first, "", None)
        pytest.raises(TypeError, split_first, "", None)
        pytest.raises(TypeError, split_first, "", None)

    #----------------------------------------------------------------------
    def test_empty_imput(self):
        assert split_first("", "") == ("", "", None)

    #----------------------------------------------------------------------
    def test_input(self):
        assert split_first("hello//world", "?/") == ("hello", "/world", "/")
        assert split_first("hello??/world", "?/") == ("hello", "?/world", "?")
        assert split_first("hello world", "?/") == ("hello world", "", None)

