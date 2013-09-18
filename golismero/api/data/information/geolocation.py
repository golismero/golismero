#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Geolocation data.
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

__all__ = ["Geolocation"]

from . import Information
from .. import identity, merge


#------------------------------------------------------------------------------
class Geolocation(Information):
    """
    Geolocation data.
    """

    information_type = Information.INFORMATION_GEOLOCATION


    #----------------------------------------------------------------------
    def __init__(self, latitude, longitude,
                 country_code = None, country_name = None,
                 region_code = None, region_name = None,
                 city = None, zipcode = None,
                 metro_code = None, areacode = None):
        """
        :param latitude: Latitude.
        :type latitude: float

        :param longitude: Longitude.
        :type longitude: float

        :param country_code: Country code (for example: "ES" for Spain).
        :type country_code: str

        :param country_name: Country name.
        :type country_name: str

        :param region_code: Region code.
        :type region_code: str

        :param region_name: Region name.
        :type region_name: str

        :param city: City name.
        :type city: str

        :param zipcode: Zipcode (postal code).
        :type zipcode: str

        :param metro_code: Metropolitan area code.
        :type metro_code: str

        :param areacode: Area code.
        :type areacode: str
        """

        # Validate the data types.
        try:
            latitude = float(latitude)
        except Exception:
            raise TypeError("Expected float, got %r instead" % type(latitude))
        try:
            longitude = float(longitude)
        except Exception:
            raise TypeError("Expected float, got %r instead" % type(longitude))
        if type(country_code) is not str:
            raise TypeError("Expected string, got %r instead" % type(country_code))
        if type(country_name) is not str:
            raise TypeError("Expected string, got %r instead" % type(country_name))
        if type(region_code) is not str:
            raise TypeError("Expected string, got %r instead" % type(region_code))
        if type(region_name) is not str:
            raise TypeError("Expected string, got %r instead" % type(region_name))
        if type(city) is not str:
            raise TypeError("Expected string, got %r instead" % type(city))
        if type(zipcode) is not str:
            raise TypeError("Expected string, got %r instead" % type(zipcode))
        if type(metro_code) is not str:
            raise TypeError("Expected string, got %r instead" % type(metro_code))
        if type(areacode) is not str:
            raise TypeError("Expected string, got %r instead" % type(areacode))

        # Store the properties.
        self.__latitude     = latitude
        self.__longitude    = longitude
        self.__country_code = country_code
        self.__country_name = country_name
        self.__region_code  = region_code
        self.__region_name  = region_name
        self.__city         = city
        self.__zipcode      = zipcode
        self.__metro_code   = metro_code
        self.__areacode     = areacode

        # Parent constructor.
        super(Geolocation, self).__init__()


    #----------------------------------------------------------------------
    def __str__(self):

        # Simplified view of the geographic location.
        coords = "(%f, %f)" % (self.latitude, self.longitude)
        where = ""
        if self.country_name:
            where = self.country_name
        elif self.country_code:
            where = self.country_code
        if self.region_name:
            if where:
                where = "%s, %s" % (self.region_name, where)
            else:
                where = self.region_name
        elif self.region_code:
            if where:
                where = "%s, %s" % (self.region_code, where)
            else:
                where = self.region_code
        if self.city:
            if where:
                where = "%s, %s" % (self.city, where)
            else:
                where = self.city
        if where:
            where = "%s %s" % (where, coords)
        else:
            where = coords
        return where


    #----------------------------------------------------------------------
    def __repr__(self):

        # Print out all the details.
        return (
            "<%s latitude=%f, longitude=%f, country_code=%s,"
            " country_name=%s, region_code=%s, region_name=%s,"
            " city=%s, zipcode=%s, metro_code=%s, areacode=%s>"
            % (self.__class__.__name__,
            self.latitude, self.longitude, self.country_code,
            self.country_name, self.region_code, self.region_name,
            self.city, self.zipcode, self.metro_code, self.areacode)
        )


    #----------------------------------------------------------------------
    @identity
    def latitude(self):
        """
        :returns: Latitude.
        :rtype: float
        """
        return self.__latitude


    #----------------------------------------------------------------------
    @identity
    def longitude(self):
        """
        :returns: Longitude.
        :rtype: float
        """
        return self.__longitude


    #----------------------------------------------------------------------
    @merge
    def country_code(self):
        """
        :returns: Country code (for example: "ES" for Spain).
        :rtype: str
        """
        return self.__country_code


    #----------------------------------------------------------------------
    @country_code.setter
    def country_code(self, country_code):
        """
        :param country_code: Country code (for example: "ES" for Spain).
        :type country_code: str
        """
        self.__country_code = country_code


    #----------------------------------------------------------------------
    @merge
    def country_name(self):
        """
        :returns: Country name.
        :rtype: str
        """
        return self.__country_name


    #----------------------------------------------------------------------
    @country_name.setter
    def country_name(self, country_name):
        """
        :param country_name: Country name.
        :type country_name: str
        """
        self.__country_name = country_name


    #----------------------------------------------------------------------
    @merge
    def region_code(self):
        """
        :returns: Region code.
        :rtype: str
        """
        return self.__region_code


    #----------------------------------------------------------------------
    @region_code.setter
    def region_code(self, region_code):
        """
        :param region_code: Region code.
        :type region_code: str
        """
        self.__region_code = region_code


    #----------------------------------------------------------------------
    @merge
    def region_name(self):
        """
        :returns: Region name.
        :rtype: str
        """
        return self.__region_name


    #----------------------------------------------------------------------
    @region_name.setter
    def region_name(self, region_name):
        """
        :param region_name: Region name.
        :type region_name: str
        """
        self.__region_name = region_name


    #----------------------------------------------------------------------
    @merge
    def city(self):
        """
        :returns: City name.
        :rtype: str
        """
        return self.__city


    #----------------------------------------------------------------------
    @city.setter
    def city(self, city):
        """
        :param city: City name.
        :type city: str
        """
        self.__city = city


    #----------------------------------------------------------------------
    @merge
    def zipcode(self):
        """
        :returns: Zipcode (postal code).
        :rtype: str
        """
        return self.__zipcode


    #----------------------------------------------------------------------
    @zipcode.setter
    def zipcode(self, zipcode):
        """
        :param zipcode: Zipcode (postal code).
        :type zipcode: str
        """
        self.__zipcode = zipcode


    #----------------------------------------------------------------------
    @merge
    def metro_code(self):
        """
        :returns: Metropolitan area code.
        :rtype: str
        """
        return self.__metro_code


    #----------------------------------------------------------------------
    @metro_code.setter
    def metro_code(self, metro_code):
        """
        :param metro_code: Metropolitan area code.
        :type metro_code: str
        """
        self.__metro_code = metro_code


    #----------------------------------------------------------------------
    @merge
    def areacode(self):
        """
        :returns: Area code.
        :rtype: str
        """
        return self.__areacode


    #----------------------------------------------------------------------
    @areacode.setter
    def areacode(self, areacode):
        """
        :param areacode: Area name.
        :type areacode: str
        """
        self.__areacode = areacode
