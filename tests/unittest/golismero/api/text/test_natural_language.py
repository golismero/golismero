#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from golismero.api.text.natural_language import get_words, \
    calculate_language_scores, detect_language, number_to_words


#--------------------------------------------------------------------------
# Get words test
#--------------------------------------------------------------------------
class TestGetWords:

    #----------------------------------------------------------------------
    def test_types_param1(self):
        pytest.raises(TypeError, get_words, None)
        pytest.raises(TypeError, get_words, 0)
        pytest.raises(TypeError, get_words, [])
        pytest.raises(TypeError, get_words, dict())

    #----------------------------------------------------------------------
    def test_types_param2(self):
        pytest.raises(TypeError, get_words, "hello world", [])
        pytest.raises(TypeError, get_words, "hello world", "0")
        pytest.raises(ValueError, get_words, "hello world", -1)

    #----------------------------------------------------------------------
    def test_types_param3(self):
        pytest.raises(TypeError, get_words, "hello world", None, [])
        pytest.raises(TypeError, get_words, "hello world", None, "0")
        pytest.raises(ValueError, get_words, "hello world", None, -1)

    #----------------------------------------------------------------------
    def test_empty_input(self):
        assert get_words("") == set([])

    #----------------------------------------------------------------------
    def test_normal_input(self):
        assert get_words("hello") == set(["hello"])
        assert get_words("hello world") == set(["hello", "world"])

    #----------------------------------------------------------------------
    def test_input_with_params(self):
        assert get_words("hello world", 6) == set([])
        assert get_words("hello world bye", 4) == set(["hello", "world"])
        assert get_words("hello world bye goooodbye", 4, 6) == set(["hello", "world"])


#--------------------------------------------------------------------------
# Calculate Language Scores test
#--------------------------------------------------------------------------
class TestCalculateLanguageScores:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, calculate_language_scores, None)
        pytest.raises(TypeError, calculate_language_scores, 0)
        pytest.raises(TypeError, calculate_language_scores, [])
        pytest.raises(TypeError, calculate_language_scores, dict())

    #----------------------------------------------------------------------
    def test_empty_input(self):
        assert calculate_language_scores("") == {}

    #----------------------------------------------------------------------
    def test_input(self):
        # With a short sentence
        results = {'swedish': 0, 'danish': 0, 'hungarian': 0, 'finnish': 0, 'portuguese': 0, 'german': 0, 'dutch': 0,
                   'french': 0, 'spanish': 0, 'norwegian': 0, 'english': 0, 'russian': 0, 'turkish': 0, 'italian': 0}
        assert calculate_language_scores("Hello world") == results

        # With more info
        results['english'] = 3
        assert calculate_language_scores("Hello world, how are you?") == results


#--------------------------------------------------------------------------
# Detect Language test
#--------------------------------------------------------------------------
class TestDetectLanguage:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, detect_language, None)
        pytest.raises(TypeError, detect_language, 0)
        pytest.raises(TypeError, detect_language, [])
        pytest.raises(TypeError, detect_language, dict())

    #----------------------------------------------------------------------
    def test_empty_input(self):
        assert detect_language("") == "unknown"

    #----------------------------------------------------------------------
    def test_input(self):

        assert detect_language("Hello world, how are you?") == "english"
        assert detect_language("Hola mundo que tal estás, yo bien gracias. Todo bien?") == "spanish"
        assert detect_language("Hola mundo que tal estas?") == "portuguese"

        # Unknown lang
        assert detect_language("asdfasdfasdf") == "unknown"


#--------------------------------------------------------------------------
# Number to words test
#--------------------------------------------------------------------------
class TestNumberToWords:

    #----------------------------------------------------------------------
    def test_types(self):
        pytest.raises(TypeError, number_to_words, None)
        pytest.raises(TypeError, number_to_words, "")
        pytest.raises(TypeError, number_to_words, [])
        pytest.raises(TypeError, number_to_words, dict())

    #----------------------------------------------------------------------
    def test_empty_input_param1(self):
        pytest.raises(TypeError, number_to_words, None)

    #----------------------------------------------------------------------
    def test_empty_input_param2(self):
        pytest.raises(TypeError, number_to_words, 2, None)

    #----------------------------------------------------------------------
    def test_empty_input_param3(self):
        pytest.raises(TypeError, number_to_words, 2, "en", None)

    #----------------------------------------------------------------------
    def test_empty_input_invalid_locale_or_num_type(self):
        pytest.raises(ValueError, number_to_words, 2, "aaa")

        assert number_to_words(2, "en", "aaaa") == u"two"

    #----------------------------------------------------------------------
    def test_input(self):
        assert number_to_words(89) == u'eighty-nine'
        assert number_to_words(89, "es") == u'ochenta y nueve'
        assert number_to_words(89, "es", num_type="ordinal") == u'ochenta y nueve'
        pytest.raises(ValueError, number_to_words, -89, "es", num_type="ordinal")



