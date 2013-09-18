#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Text diff/match analyzer API.
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

__all__ = ["get_diff_ratio", "MatchingAnalyzer"]

from difflib import SequenceMatcher


#------------------------------------------------------------------------------
def get_diff_ratio(text1, text2):
    """
    Compare two texts and return a floating point value between 0 and 1 with
    the difference ratio, with 0 being absolutely different and 1 being
    absolutely equal - the more similar the two texts are, the closer the ratio
    will be to 1.

    :param text1: First text to compare.
    :type text1: str

    :param text2: Second text to compare.
    :type text2: str

    :returns: Floating point value between 0 and 1.
    :rtype: float
    """

    # Solve some trivial type errors (like using None).
    if not text1:
        text1 = ""
    if not text2:
        text2 = ""

    # Check for type errors we can't fix.
    if not isinstance(text1, basestring):
        raise TypeError("Expected string, got %r instead" % type(text1))
    if not isinstance(text2, basestring):
        raise TypeError("Expected string, got %r instead" % type(text2))

    # Trivial case, the two texts are identical.
    if text1 == text2:
        return 1.0

    # Use the difflib sequence matcher to calculate the ratio.
    m = SequenceMatcher(a=text1, b=text2)
    return m.ratio()


#------------------------------------------------------------------------------
class MatchingAnalyzerElement(object):
    """
    Match element of the :ref:`MatchingAnalyzer`.

    :ivar text: Text.
    :type text: str

    :ivar ratio: Difference ratio against the base text.
    :type ratio: float
    """


    #--------------------------------------------------------------------------
    def __init__(self, text, ratio, attrs):
        """
        :param text: Text.
        :type text: str

        :param ratio: Difference ratio against the base text.
        :type ratio: float

        :param attrs: Custom attributes dictionary.
        :type attrs: dict(str -> *)
        """
        self.text    = text
        self.ratio   = ratio
        self.__attrs = attrs


    #--------------------------------------------------------------------------
    def __getattr__(self, name):
        return self.__attrs[name]


#------------------------------------------------------------------------------
class MatchingAnalyzer(object):
    """
    Text matching analyzer.

    Compares any number of texts from a base text and generates
    an iterator with those that are sufficiently different.
    """


    #--------------------------------------------------------------------------
    def __init__(self, base_text, min_ratio = 0.52, min_deviation = 1.15):
        """
        :param base_text: Base text to be used for comparisons.
        :type base_text: str

        :param min_ratio: Minimum diff ratio to consider two texts as different.
        :type min_ratio: float

        :param min_deviation: Minimum deviation from the average to consider
            texts to be unique.
        :type min_deviation: float
        """
        if not base_text:
            raise ValueError("Base text cannot be empty")
        if not isinstance(base_text, basestring):
            raise TypeError("Expected string , got %r instead" % type(base_text))
        if not isinstance(min_ratio, float):
            raise TypeError("Expected float, got %r instead" % type(min_ratio))
        if not isinstance(min_deviation, float):
            raise TypeError("Expected float, got %r instead" % type(min_deviation))

        self.__base_text      = base_text
        self.__min_ratio      = min_ratio
        self.__min_deviation  = min_deviation

        self.__matches        = []
        self.__unique_strings = None
        self.__average_ratio  = None


    #--------------------------------------------------------------------------
    @property
    def base_text(self):
        """
        :returns: Base text to be used for comparisons.
        :rtype: str
        """
        return self.__base_text


    #--------------------------------------------------------------------------
    @property
    def min_ratio(self):
        """
        :returns: Minimum diff ratio to consider two texts as different.
        :rtype: float
        """
        return self.__min_ratio


    #--------------------------------------------------------------------------
    @property
    def min_deviation(self):
        """
        :returns: Minimum deviation from the average to consider
            texts to be unique.
        :rtype: float
        """
        return self.__min_deviation


    #--------------------------------------------------------------------------
    def analyze(self, text, **kwargs):
        """
        If the matching level of text var is sufficient similar
        to the base_text, then, store the text, and anything vars as
        \\*\\*kargs associated with this text.

        :param text: Text to compare with the base text.
        :type text: str

        :returns: True if the text is accepted as equal, False otherwise.
        :rtype: bool
        """

        # Ignore empty text.
        if text:

            # Calculate the diff ratio.
            ratio = get_diff_ratio(self.__base_text, text)

            # If it's lower than our boundary...
            if ratio < self.__min_ratio:

                # Invalidate the caches.
                self.__clear_caches()

                # Save the results.
                match = MatchingAnalyzerElement(text, ratio, kwargs)
                self.__matches.append(match)

                # Text accepted.
                return True

        # Text rejected.
        return False


    #--------------------------------------------------------------------------
    def __clear_caches(self):
        self.__average_ratio  = None
        self.__unique_strings = None


    #--------------------------------------------------------------------------
    @property
    def average_ratio(self):
        """
        :returns: Average diff ratio.
        :rtype: float
        """

        # If the cache is empty, calculate.
        if self.__average_ratio is None:
            if self.__matches:
                ratios = sum(match.ratio for match in self.__matches)
                count  = len(self.__matches)
                self.__average_ratio = float(ratios) / float(count)
            else:
                self.__average_ratio = 0.0

        # Return the cached value.
        return self.__average_ratio


    #--------------------------------------------------------------------------
    @property
    def unique_texts(self):
        """
        :returns: List of unique texts.
        :rtype: list(str)
        """

        # If the cache is empty, calculate.
        if self.__unique_strings is None:
            self.__calculate_unique_texts()

        # Return results from the cache.
        return list(self.__unique_strings)


    #--------------------------------------------------------------------------
    def __calculate_unique_texts(self):

        # Empty results list.
        self.__unique_strings = []

        # Get the average deviation.
        average = self.average_ratio

        # Skip if the ratio is 0.
        if not average:

            # Optimization.
            append    = self.__unique_strings.append
            deviation = self.__min_deviation

            # For each match element...
            for match in self.__matches:

                # Get the ratio and calculate the max deviation.
                ratio    = match.ratio
                deviated = ratio * deviation

                # Skip matches under the max deviation.
                if not (ratio < average < deviated):

                    # Append the result.
                    append(match)
