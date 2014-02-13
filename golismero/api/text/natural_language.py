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
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: http://golismero-project.com
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
    "get_words", "detect_language", "calculate_language_scores",
    "number_to_words",
]

from nltk import wordpunct_tokenize
from nltk.corpus import stopwords


#------------------------------------------------------------------------------
def get_words(text, min_length = None, max_length = None):
    """
    Parse the given text as natural language and extract words from it.
    Optionally filter the words by minimum and/or maximum length.

    :param text: Text to parse.
    :type text: str

    :param min_length: Minimum length required. Use None for no limit.
    :type min_length: int | None

    :param min_length: Maximum length allowed. Use None for no limit.
    :type min_length: int | None

    :return: Set of unique words extracted from the text.
    :rtype: set(str)
    """

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
    """

    # Split the text into separate tokens, using natural language punctuation signs.
    words = {word.lower() for word in wordpunct_tokenize(text)}

    # Return the number of stopwords found per language.
    return {
        len( words.intersection( stopwords.words(language) ) )
        for language in stopwords.fileids()
    }


#------------------------------------------------------------------------------
def detect_language(text):
    """
    Calculate the probability of given text to be written in different
    languages and return the highest scoring one.

    Example:
        >>> text= "Hello my name is Golismero and I'm a function"
        >>> detect_language(text)
        'english'
        >>> text_spanish= "Hola mi nombre es Golismero y soy una funcion"
        >>> detect_language(text)
        'spanish'

    :param text: Text to analyze.
    :type text: str

    :return: Detected language.
    :rtype: str
    """
    scores = calculate_language_scores(text)
    return max(scores, key=scores.get)


#------------------------------------------------------------------------------
def number_to_words(n, locale = "EN", num_type = "cardinal"):
    """
    Convert an integer numeric value into natural language text.

    :param n: Number to convert.
    :type n: int

    :param locale:
        Language to convert to. Currently supported values:
         - "DE"
         - "EN"
         - "EN_GB"
         - "ES"
         - "FR"
    :type locale: str

    :param num_type:
        Type of number. Must be one of the following values:
         - "cardinal"
         - "ordinal"
         - "currency"
         - "year"

    :returns: Natural language text.
    :rtype: str

    :raise ValueError: Language or number type not supported.
    """
    try:
        module = "num2word_" + locale
        n2wmod = __import__(module)
        n2w = n2wmod.n2w(n)
        method = "to_" + num_type
        return getattr(n2w, method)()
    except ImportError:
        raise ValueError("Language not supported: %s" % locale)
    except AttributeError:
        raise ValueError("Number type not supported: %s" % num_type)
