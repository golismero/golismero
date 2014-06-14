#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Image file.
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

__all__ = ["Image"]

from .binary import Binary
from .geolocation import Geolocation

from StringIO import StringIO
from warnings import warn

# Lazy import.
PIL_Image = None
PIL_TAGS  = None


#------------------------------------------------------------------------------
class Image(Binary):
    """
    Image file.
    """


    #--------------------------------------------------------------------------
    def __init__(self, data, content_type):
        if type(content_type) is not str:
            raise TypeError(
                "Expected string, got %r instead" % type(content_type))
        if not content_type.startswith("image/"):
            raise ValueError("Not an image type: %s" % content_type)
        super(Image, self).__init__(data, content_type)


    #--------------------------------------------------------------------------
    def to_pil(self):
        """
        Load this image using PIL (Python Image Library).

        :returns: PIL Image object.
        :rtype: PIL.Image.Image
        """

        # Lazy import.
        global PIL_Image
        if PIL_Image is None:
            from PIL import Image as PIL_Image

        # Load into PIL.
        fd = StringIO(self.raw_data)
        img = PIL_Image.open(fd)
        return img


    #--------------------------------------------------------------------------
    @classmethod
    def from_pil(cls, img):
        """
        Create an Image object from a PIL image.

        :param img: PIL Image object.
        :type img: PIL.Image.Image

        :returns: Image object.
        :rtype: Image
        """
        fmt = img.format
        if not fmt:
            fmt = "raw"
        fmt = fmt.strip().lower()
        fd = StringIO()
        img.save(fd)
        return cls(fd.getvalue(), "image/" + fmt)


    #--------------------------------------------------------------------------
    def get_exif(self):
        """
        Get EXIF tags for JPEG images. Fails for non-JPEG images.

        :returns: EXIF tags.
        :rtype: dict(str -> str)

        :raise ValueError: Not a JPEG image.
        """

        # Check that it's really an image.
        if self.mime_subtype != "jpeg":
            raise ValueError("Not a JPEG image")

        # Lazy import.
        global PIL_TAGS
        if PIL_TAGS is None:
            from PIL.ExifTags import TAGS as PIL_TAGS

        # Load in PIL.
        img = self.to_pil()

        # Extract the EXIF tags.
        exif = {}
        try:
            info = img.tag.tags
        except AttributeError:
            info = img._getexif()
        if info:
            for tag, value in info.items():
                decoded = PIL_TAGS.get(tag, tag)
                exif[decoded] = value

        # Return the EXIF tags.
        return exif


    #--------------------------------------------------------------------------
    @property
    def discovered(self):
        if self.mime_subtype == "jpeg":
            exif = self.get_exif()
            if "GPSInfo" in exif:
                try:
                    info = exif["GPSInfo"]
                    t_lat_d, t_lat_m, t_lat_s = info[2]   # GPSLatitude
                    t_lon_d, t_lon_m, t_lon_s = info[4]   # GPSLongitude
                    lat_d = float(t_lat_d[0]) / float(t_lat_d[1])
                    lat_m = float(t_lat_m[0]) / float(t_lat_m[1])
                    lat_s = float(t_lat_s[0]) / float(t_lat_s[1])
                    lon_d = float(t_lon_d[0]) / float(t_lon_d[1])
                    lon_m = float(t_lon_m[0]) / float(t_lon_m[1])
                    lon_s = float(t_lon_s[0]) / float(t_lon_s[1])
                    lat = lat_d + (lat_m / 60.0) + (lat_s / 3600)
                    lon = lon_d + (lon_m / 60.0) + (lon_s / 3600)
                    lat_ref = info.get(1, "N")            # GPSLatitudeRef
                    lon_ref = info.get(3, "E")            # GPSLongitudeRef
                    lat_ref = str(lat_ref).strip()[0].upper()
                    lon_ref = str(lon_ref).strip()[0].upper()
                    if lat_ref == "S":
                        lat = -lat
                    if lon_ref == "W":
                        lon = -lon
                    geoloc = Geolocation(
                        latitude  = lat,
                        longitude = lon,
                    )
                    geoloc.add_link(self)
                    return [geoloc]
                except Exception, e:
                    warn(str(e), RuntimeWarning)
        return []
