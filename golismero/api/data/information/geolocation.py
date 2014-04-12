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

from . import Fingerprint
from .. import identity, merge
from ...text.text_utils import to_utf8


#------------------------------------------------------------------------------
class Geolocation(Fingerprint):
    """
    Geolocation data.
    """


    #--------------------------------------------------------------------------
    def __init__(self, latitude, longitude,
                 country_code = None, country_name = None,
                 region_code = None, region_name = None,
                 city = None, zipcode = None,
                 metro_code = None, area_code = None,
                 street_addr = None, accuracy = None):
        """
        :param latitude: Latitude.
        :type latitude: float

        :param longitude: Longitude.
        :type longitude: float

        :param country_code: Country code (for example: "ES" for Spain).
        :type country_code: str | None

        :param country_name: Country name.
        :type country_name: str | None

        :param region_code:
            Region code ("Region" means "State" in the USA, "County" in the
            UK, "Province/Territory" in Canada, "Region" in Italy, etc).
        :type region_code: str | None

        :param region_name: Region name.
        :type region_name: str | None

        :param city: City name.
        :type city: str | None

        :param zipcode: Zipcode (postal code).
        :type zipcode: str | None

        :param metro_code: Metropolitan area (DMA) code.
        :type metro_code: str | None

        :param area_code: Area code.
        :type area_code: str | None

        :param street_addr: Street address.
        :type street_addr: str | None

        :param accuracy: Accuracy in meters.
        :type accuracy: float | None
        """

        # Validate the data types.
        try:
            latitude = float(latitude)
        except Exception:
            raise TypeError(
                "Expected float, got %r instead" % type(latitude))
        try:
            longitude = float(longitude)
        except Exception:
            raise TypeError(
                "Expected float, got %r instead" % type(longitude))
        country_code = to_utf8(country_code)
        country_name = to_utf8(country_name)
        region_code  = to_utf8(region_code)
        region_name  = to_utf8(region_name)
        city         = to_utf8(city)
        zipcode      = to_utf8(zipcode)
        metro_code   = to_utf8(metro_code)
        area_code    = to_utf8(area_code)
        street_addr  = to_utf8(street_addr)
        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except TypeError:
                raise TypeError(
                    "Expected float, got %r instead" % type(accuracy))
            if accuracy < 0.0:
                raise ValueError(
                    "Accuracy cannot be a negative distance: %r" % accuracy)
        if country_code is not None and type(country_code) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(country_code))
        if country_name is not None and type(country_name) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(country_name))
        if region_code is not None and type(region_code) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(region_code))
        if region_name is not None and type(region_name) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(region_name))
        if city is not None and type(city) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(city))
        if zipcode is not None and type(zipcode) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(zipcode))
        if metro_code is not None and type(metro_code) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(metro_code))
        if area_code is not None and type(area_code) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(area_code))
        if street_addr is not None and type(street_addr) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(street_addr))

        # Store the properties.
        self.__latitude     = latitude
        self.__longitude    = longitude
        self.__accuracy     = accuracy
        self.__country_code = country_code or None
        self.__country_name = country_name or None
        self.__region_code  = region_code or None
        self.__region_name  = region_name or None
        self.__city         = city or None
        self.__zipcode      = zipcode or None
        self.__metro_code   = metro_code or None
        self.__area_code    = area_code or None
        self.__street_addr  = street_addr or None

        # Parent constructor.
        super(Geolocation, self).__init__()


    #--------------------------------------------------------------------------
    def __str__(self):

        # Simplified view of the geographic location.
        coords = "(%f, %f)" % (self.latitude, self.longitude)
        if self.accuracy:
            coords += " [~%dm]" % self.accuracy
        where = ""
        if self.street_addr:
            where = self.street_addr
        else:
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


    #--------------------------------------------------------------------------
    def __repr__(self):

        # Print out all the details.
        return (
            "<%s latitude=%f, longitude=%f, country_code=%r,"
            " country_name=%r, region_code=%r, region_name=%r,"
            " city=%r, zipcode=%r, metro_code=%r, area_code=%r,"
            " street_addr=%r, accuracy=%s>"
            % (self.__class__.__name__,
            self.latitude, self.longitude, self.country_code,
            self.country_name, self.region_code, self.region_name,
            self.city, self.zipcode, self.metro_code, self.area_code,
            self.street_addr, self.accuracy)
        )


    #--------------------------------------------------------------------------
    @identity
    def latitude(self):
        """
        :returns: Latitude.
        :rtype: float
        """
        return self.__latitude


    #--------------------------------------------------------------------------
    @identity
    def longitude(self):
        """
        :returns: Longitude.
        :rtype: float
        """
        return self.__longitude


    #--------------------------------------------------------------------------
    @merge
    def country_code(self):
        """
        :returns: Country code (for example: "ES" for Spain).
        :rtype: str | None
        """
        return self.__country_code


    #--------------------------------------------------------------------------
    @country_code.setter
    def country_code(self, country_code):
        """
        :param country_code: Country code (for example: "ES" for Spain).
        :type country_code: str
        """
        if country_code is not None:
            country_code = to_utf8(country_code)
            if type(country_code) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(country_code))
        self.__country_code = country_code


    #--------------------------------------------------------------------------
    @merge
    def country_name(self):
        """
        :returns: Country name.
        :rtype: str | None
        """
        return self.__country_name


    #--------------------------------------------------------------------------
    @country_name.setter
    def country_name(self, country_name):
        """
        :param country_name: Country name.
        :type country_name: str
        """
        if country_name is not None:
            country_name = to_utf8(country_name)
            if type(country_name) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(country_name))
        self.__country_name = country_name


    #--------------------------------------------------------------------------
    @merge
    def region_code(self):
        """
        :returns: Region code.
        :rtype: str | None
        """
        return self.__region_code


    #--------------------------------------------------------------------------
    @region_code.setter
    def region_code(self, region_code):
        """
        :param region_code: Region code.
        :type region_code: str
        """
        if region_code is not None:
            region_code = to_utf8(region_code)
            if type(region_code) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(region_code))
        self.__region_code = region_code


    #--------------------------------------------------------------------------
    @merge
    def region_name(self):
        """
        :returns: Region name.
        :rtype: str | None
        """
        return self.__region_name


    #--------------------------------------------------------------------------
    @region_name.setter
    def region_name(self, region_name):
        """
        :param region_name: Region name.
        :type region_name: str
        """
        if region_name is not None:
            region_name = to_utf8(region_name)
            if type(region_name) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(region_name))
        self.__region_name = region_name


    #--------------------------------------------------------------------------
    @merge
    def city(self):
        """
        :returns: City name.
        :rtype: str | None
        """
        return self.__city


    #--------------------------------------------------------------------------
    @city.setter
    def city(self, city):
        """
        :param city: City name.
        :type city: str
        """
        if city is not None:
            city = to_utf8(city)
            if type(city) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(city))
        self.__city = city


    #--------------------------------------------------------------------------
    @merge
    def zipcode(self):
        """
        :returns: Zipcode (postal code).
        :rtype: str | None
        """
        return self.__zipcode


    #--------------------------------------------------------------------------
    @zipcode.setter
    def zipcode(self, zipcode):
        """
        :param zipcode: Zipcode (postal code).
        :type zipcode: str
        """
        if zipcode is not None:
            zipcode = to_utf8(zipcode)
            if type(zipcode) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(zipcode))
        self.__zipcode = zipcode


    #--------------------------------------------------------------------------
    @merge
    def metro_code(self):
        """
        :returns: Metropolitan area code.
        :rtype: str | None
        """
        return self.__metro_code


    #--------------------------------------------------------------------------
    @metro_code.setter
    def metro_code(self, metro_code):
        """
        :param metro_code: Metropolitan area code.
        :type metro_code: str
        """
        if metro_code is not None:
            metro_code = to_utf8(metro_code)
            if type(metro_code) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(metro_code))
        self.__metro_code = metro_code


    #--------------------------------------------------------------------------
    @merge
    def area_code(self):
        """
        :returns: Area code.
        :rtype: str | None
        """
        return self.__area_code


    #--------------------------------------------------------------------------
    @area_code.setter
    def area_code(self, area_code):
        """
        :param area_code: Area name.
        :type area_code: str
        """
        if area_code is not None:
            area_code = to_utf8(area_code)
            if type(area_code) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(area_code))
        self.__area_code = area_code


    #--------------------------------------------------------------------------
    @merge
    def street_addr(self):
        """
        :returns: Street address.
        :rtype: str | None
        """
        return self.__street_addr


    #--------------------------------------------------------------------------
    @street_addr.setter
    def street_addr(self, street_addr):
        """
        :param street_addr: Street address.
        :type street_addr: str
        """
        if street_addr is not None:
            street_addr = to_utf8(street_addr)
            if type(street_addr) is not str:
                raise TypeError(
                    "Expected string, got %r instead" % type(street_addr))
        self.__street_addr = street_addr


    #--------------------------------------------------------------------------
    @merge
    def accuracy(self):
        """
        :returns: Street address.
        :rtype: str | None
        """
        return self.__accuracy


    #--------------------------------------------------------------------------
    @accuracy.setter
    def accuracy(self, accuracy):
        """
        :param accuracy: Accuracy in meters.
        :type accuracy: float
        """
        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except TypeError:
                raise TypeError(
                    "Expected float, got %r instead" % type(accuracy))
            if accuracy < 0.0:
                raise ValueError(
                    "Accuracy cannot be a negative distance: %r" % accuracy)
        self.__accuracy = accuracy
