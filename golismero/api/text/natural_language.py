#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Natural language API.

.. info:
   Acknowledgments go to `z0mbiehunt3r <https://twitter.com/z0mbiehunt3r>`_ for his ideas and help.
   `Check out his blog <http://blog.alejandronolla.com/2013/05/15/detecting-text-language-with-python-and-nltk/>`_
   to know where this module originally came from!
"""

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
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


__all__ = [
    "get_words", "detect_language", "calculate_language_scores",
    "number_to_words",
]

from nltk import wordpunct_tokenize
from nltk.corpus import stopwords, words

from num2words import num2words


#------------------------------------------------------------------------------
def get_words(text, min_length = None, max_length = None):
    """
    Parse the given text as natural language and extract words from it.
    Optionally filter the words by minimum and/or maximum length.

    :param text: Text to parse.
    :type text: str

    :param min_length: Minimum length required by each token. Use None for no limit.
    :type min_length: int | None

    :param min_length: Maximum length allowed by each token. Use None for no limit.
    :type min_length: int | None

    :return: Set of unique words extracted from the text.
    :rtype: set(str)

    :raises: TypeError, ValueError
    """
    if min_length is not None:
        if not isinstance(min_length, int):
            raise TypeError("Expected int, got '%s' instead" % type(min_length))
        elif min_length < 0:
            raise ValueError("Min length must be greater than 0, got %s." % min_length)

    if max_length is not None:
        if not isinstance(max_length, int):
            raise TypeError("Expected int, got '%s' instead" % type(min_length))
        elif max_length < 0:
            raise ValueError("Min length must be greater than 0, got %s" % max_length)

    # Split the text into separate tokens, using natural language
    # punctuation signs. Then filter out by min/max length, and tokens
    # that aren't strictly alphabetic. Finally, convert the words to
    # lowercase form.
    return {
        word.lower() for word in wordpunct_tokenize(text) if
        (
            word.isalpha() and
            (min_length is None or len(word) >= min_length) and
            (max_length is None or len(word) <= max_length)
        )
    }


#------------------------------------------------------------------------------
def calculate_language_scores(text):
    """
    Calculate probability of given text to be written in several languages and
    return a dictionary that looks like {'french': 2, 'spanish': 4, 'english': 0}.

    :param text: Text to analyze.
    :type text: str

    :return: Dictionary with languages and unique stopwords seen in analyzed text.
    :rtype: dict(str -> int)

    :raises: TypeError
    """
    if not isinstance(text, basestring):
        raise TypeError("Expected basestring, got '%s' instead" % type(text))
    if not text:
        return {}

    languages_ratios = {}

    # Split the text into separate tokens, using natural language punctuation signs.
    tokens = wordpunct_tokenize(text)
    tokenized_words = [word.lower() for word in tokens]

    for language in stopwords.fileids():
        stopwords_set = set(stopwords.words(language))
        words_set = set(tokenized_words)
        common_elements = words_set.intersection(stopwords_set)
        languages_ratios[language] = len(common_elements)  # language "score"

    return languages_ratios


#------------------------------------------------------------------------------
def detect_language(text):
    """
    Calculate the probability of given text to be written in different
    languages and return the highest scoring one. 'unknown' if language not
    recognized.

    Example:
        >>> text= "Hello my name is Golismero and I'm a function"
        >>> detect_language(text)
        'english'
        >>> text_spanish= "Hola mi nombre es Golismero y soy una funcion"
        >>> detect_language(text)
        'spanish'
        >>> text= ""
        >>> detect_language(text)
        'unknown'

    :param text: Text to analyze.
    :type text: str

    :return: Detected language.
    :rtype: str

    :raises: TypeError
    """
    if not isinstance(text, basestring):
        raise TypeError("Expected basestring, got '%s' instead" % type(text))
    if not text:
        return "unknown"

    scores = calculate_language_scores(text)
    max_score = max(scores, key=scores.get)

    # Check if max score it's really valid results
    if scores[max_score] == 0:
        return "unknown"
    else:
        return max_score


#------------------------------------------------------------------------------
def number_to_words(n, locale="en", num_type="cardinal"):
    """
    Convert an integer numeric value into natural language text.

    :param n: Number to convert.
    :type n: int

    :param locale:
        Language to convert to. Currently supported values:
         - "de"
         - "en"
         - "en_gb"
         - "es"
         - "fr"
         - "lt"
    :type locale: str

    :param num_type:
        Type of number. Must be one of the following values:
         - "cardinal"
         - "ordinal"

    :returns: Natural language text.
    :rtype: str

    :raises: TypeError, ValueError
    """
    if not isinstance(n, int):
        raise TypeError("Expected int, got '%s' instead" % type(n))
    if not isinstance(locale, basestring):
        raise TypeError("Expected basestring, got '%s' instead" % type(locale))
    if not isinstance(num_type, basestring):
        raise TypeError("Expected basestring, got '%s' instead" % type(num_type))
    if num_type == "ordinal" and n < 0:
        raise ValueError("Can't get ordinal value from negative number")

    if num_type == "ordinal":
        try:
            return num2words(n, ordinal=True, lang=locale.lower())
        except NotImplementedError:
            raise ValueError("Language or num_type are not valid.")
    elif num_type == "cardinal":
        try:
            return num2words(n, ordinal=False, lang=locale.lower())
        except NotImplementedError:
            raise ValueError("Language or num_type are not valid.")
    else:
        return num2words(n, ordinal=False, lang="en")