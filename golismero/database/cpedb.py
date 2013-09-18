#!/usr/bin/env python

"""
NIST CPE dictionary.
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

# Adapted from:
# https://github.com/MarioVilas/network_tools/blob/master/cpe.py

__all__ = ["CPEDB"]

import re

from time import gmtime, asctime
from os import unlink
from os.path import exists, getctime, join
from threading import RLock
from urllib import quote, unquote
from urllib2 import urlopen, Request, HTTPError  # TODO use requests instead!

import shutil
import sqlite3

try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

from .common import BaseDB, transactional
from ..api.data.vulnerability.vuln_utils import get_cpe_version, parse_cpe
from ..api.logger import Logger
from ..api.net.web_utils import parse_url
from ..common import get_user_settings_folder
from ..messaging.codes import MessageCode
from ..managers.rpcmanager import implementor


#------------------------------------------------------------------------------
# RPC implementors.

@implementor(MessageCode.MSG_RPC_CPE_GET_TITLE)
def rpc_cpe_get_title(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cpedb.get_title(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_CPE_RESOLVE)
def rpc_cpe_resolve(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cpedb.resolve(*args, **kwargs)

@implementor(MessageCode.MSG_RPC_CPE_SEARCH)
def rpc_cpe_search(orchestrator, audit_name, *args, **kwargs):
    return orchestrator.cpedb.search(*args, **kwargs)


#------------------------------------------------------------------------------
class CPEDB(BaseDB):
    """
    Translates between CPE 2.2 and CPE 2.3 names, and looks up user-friendly
    software names from CPE names and visceversa.

    The official CPE dictionary is converted to SQLite format from the
    original XML file mantained by NIST: https://nvd.nist.gov/cpe.cfm
    """

    DB_FILE      = "official-cpe-dictionary_v2.3.db"
    CPE_XML_FILE = "official-cpe-dictionary_v2.3.xml"
    CPE_URL_BASE = "http://static.nvd.nist.gov/feeds/xml/cpe/dictionary/"

    SCHEMA = \
    """
    PRAGMA foreign_keys = ON;
    PRAGMA auto_vacuum = NONE;

    ---------------------
    -- File timestamps --
    ---------------------

    CREATE TABLE IF NOT EXISTS `files` (
        `filename` STRING NOT NULL UNIQUE ON CONFLICT REPLACE,
        `last_modified` INTEGER NOT NULL,
        `last_modified_string` STRING NOT NULL
    );

    ---------
    -- CPE --
    ---------

    CREATE TABLE IF NOT EXISTS `cpe` (
        `rowid` INTEGER PRIMARY KEY,
        `name23` STRING NOT NULL UNIQUE,
        `name22` STRING NOT NULL,
        `title` STRING,
        `deprecated` INTEGER(1),
        `part` STRING NOT NULL DEFAULT '*',
        `vendor` STRING NOT NULL DEFAULT '*',
        `product` STRING NOT NULL DEFAULT '*',
        `version` STRING NOT NULL DEFAULT '*',
        `update` STRING NOT NULL DEFAULT '*',
        `edition` STRING NOT NULL DEFAULT '*',
        `language` STRING NOT NULL DEFAULT '*',
        `sw_edition` STRING NOT NULL DEFAULT '*',
        `target_sw` STRING NOT NULL DEFAULT '*',
        `target_hw` STRING NOT NULL DEFAULT '*',
        `other` STRING NOT NULL DEFAULT '*'
    );
    CREATE INDEX IF NOT EXISTS `cpe_name22` ON `cpe`(`name22`);
    CREATE INDEX IF NOT EXISTS `cpe_title` ON `cpe`(`title`);
    CREATE INDEX IF NOT EXISTS `cpe_part` ON `cpe`(`part`);
    CREATE INDEX IF NOT EXISTS `cpe_vendor` ON `cpe`(`vendor`);
    CREATE INDEX IF NOT EXISTS `cpe_product` ON `cpe`(`product`);
    CREATE INDEX IF NOT EXISTS `cpe_version` ON `cpe`(`version`);
    CREATE INDEX IF NOT EXISTS `cpe_update` ON `cpe`(`update`);
    CREATE INDEX IF NOT EXISTS `cpe_edition` ON `cpe`(`edition`);
    CREATE INDEX IF NOT EXISTS `cpe_language` ON `cpe`(`language`);
    CREATE INDEX IF NOT EXISTS `cpe_sw_edition` ON `cpe`(`sw_edition`);
    CREATE INDEX IF NOT EXISTS `cpe_target_sw` ON `cpe`(`target_sw`);
    CREATE INDEX IF NOT EXISTS `cpe_target_hw` ON `cpe`(`target_hw`);
    CREATE INDEX IF NOT EXISTS `cpe_other` ON `cpe`(`other`);
    """


    #--------------------------------------------------------------------------
    def __init__(self):

        # Get the database filename.
        db_file = join( get_user_settings_folder(), self.DB_FILE )

        # Create the lock to make this class thread safe.
        self.__lock = RLock()

        # The busy flag prevents reentrance.
        self.__busy = False

        # Determine if the database existed.
        is_new = exists(db_file)
        if is_new:
            Logger.log(
                "The first time GoLismero is run, the vulnerability database"
                " must be initialized. This may take a while..."
            )

        # Open the database file.
        self.__db = sqlite3.connect(db_file)

        try:

            # Create the database schema.
            self.__create_schema()

            # Populate the database on the first run.
            if is_new:
                self.update()

        # On error delete the database and raise an exception.
        except:
            self.close()
            raise


    #--------------------------------------------------------------------------
    def close(self):
        try:
            self.__db.close()
        finally:
            self.__db     = None
            self.__cursor = None
            self.__lock   = None


    #--------------------------------------------------------------------------
    def _transaction(self, fn, args, kwargs):
        with self.__lock:
            if self.__busy:
                raise RuntimeError("The database is busy")
            try:
                self.__busy   = True
                self.__cursor = self.__db.cursor()
                try:
                    retval = fn(self, *args, **kwargs)
                    self.__db.commit()
                    return retval
                except:
                    self.__db.rollback()
                    raise
            finally:
                self.__cursor = None
                self.__busy   = False


    #--------------------------------------------------------------------------
    @transactional
    def vacuum(self):
        self.__cursor.execute("VACUUM;")


    #--------------------------------------------------------------------------
    @transactional
    def __create_schema(self):
        self.__cursor.executescript(self.SCHEMA)


    #--------------------------------------------------------------------------
    @transactional
    def update(self):
        """
        Update the database.

        This automatically downloads up-to-date XML files from NIST when needed
        and recreates the database from them.
        """

        # Download and open the XML file.
        xml_file   = self.CPE_XML_FILE
        xml_parser = self.__download(self.CPE_URL_BASE, xml_file)

        # Do we need to load new data?
        if xml_parser:
            Logger.log("Loading file: %s" % xml_file)

            # Parse the XML file and store the data into the database.
            prefix20 = "{http://cpe.mitre.org/dictionary/2.0}"
            prefix23 = "{http://scap.nist.gov/schema/cpe-extension/2.3}"
            prefixns = "{http://www.w3.org/XML/1998/namespace}"
            context  = iter(xml_parser)
            _, root  = context.next()
            main_tag = prefix20 + "cpe-item"
            for event, item in context:
                if event != "end" or item.tag != main_tag:
                    continue
                name22 = item.attrib["name"]
                name23 = item.find(".//%scpe23-item" % prefix23).attrib["name"]
                deprecated = int(
                            item.attrib.get("deprecated", "false") == "true")
                titles = {
                    t.attrib[prefixns + "lang"]: t.text
                    for t in item.iter(prefix20 + "title")
                }
                try:
                    title = titles["en-US"]
                except KeyError:
                    found = False
                    for lang, title in sorted(titles.items()):
                        if lang.startswith("en-"):
                            found = True
                            break
                    if not found:
                        title = titles[sorted(titles.keys())[0]]
                params = (name23, name22, title, deprecated)
                params = params + tuple( parse_cpe(name23) )
                self.__cursor.execute(
                    "INSERT OR REPLACE INTO `cpe` VALUES "
                    "(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    params
                )

            # Delete the XML file.
            unlink(xml_file)
            Logger.log("Deleted file: %s" % xml_file)

    # If the XML file is missing, broken or older, download it.
    # This method assumes it's being called from within an open transaction.
    def __download(self, base_url, xml_file):

        # HTTP request to make.
        req = Request(base_url + xml_file)

        # Get the last modified time from the database if available.
        self.__cursor.execute(
            "SELECT `last_modified`, `last_modified_string` FROM `files`"
            " WHERE `filename` = ? LIMIT 1;",
            (xml_file,)
        )
        row = self.__cursor.fetchone()
        if row:
            db_time, db_time_str = row
        else:
            db_time = None
            db_time_str = None

        # Also try looking for the file locally.
        # If found but can't be read, delete it.
        if exists(xml_file):
            try:
                xml_parser = etree.iterparse(
                    xml_file, events=("start", "end"))
                local_time = getmtime(xml_file)
            except Exception:
                xml_parser = None
                local_time = None
                unlink(xml_file)
        else:
            xml_parser = None
            local_time = None

        # Use the local file if newer or not yet loaded in the database.
        if local_time and (not db_time or local_time > db_time):
            Logger.log("Found local file: %s" % xml_file)
            self.__cursor.execute(
                "INSERT INTO `files` VALUES (?, ?, ?);",
                (xml_file, local_time, asctime(gmtime(local_time)))
            )
            return xml_parser

        # Otherwise, download the file if newer or not yet loaded.
        if db_time_str:
            req.add_header("If-Modified-Since", db_time_str)
        try:
            src = urlopen(req)
            downloaded = True
            db_time_str = src.info().get("Last-Modified", None)
        except HTTPError, e:
            if not db_time or e.code != 304:
                raise
            downloaded = False
            Logger.log("Already up-to-date: %s" % xml_file)
        if downloaded:
            Logger.log("Downloading from: %s" % req.get_full_url())
            try:
                with open(xml_file, "wb") as dst:
                    copyfileobj(src, dst)
            except:
                unlink(xml_file)
                raise
            xml_parser = None # free memory before using more
            xml_parser = etree.iterparse(
                xml_file, events=("start", "end"))
            if not db_time:
                db_time = getmtime(xml_file)
            if not db_time_str:
                db_time_str = asctime(gmtime(db_time))
            self.__cursor.execute(
                "INSERT INTO `files` VALUES (?, ?, ?);",
                (xml_file, db_time, db_time_str)
            )

            # Return the open XML file.
            return xml_parser


    #--------------------------------------------------------------------------
    @transactional
    def resolve(self, cpe, include_deprecated = True):
        """
        Resolve the given CPE with wildcards.

        :param CPE: CPE name.
        :type CPE: str | unicode

        :param include_deprecated: True to include deprecated names in the
            results, False otherwise.
        :type include_deprecated: bool

        :returns: Set of matching CPE names.
        :rtype: set(str|unicode)
        """

        ver = get_cpe_version(cpe).replace(".", "")
        parsed = parse_cpe(cpe)

        params = [x for x in parsed if x and x != "*"]
        if not params:
            return set([cpe])
        params.insert(0, cpe)

        columns = [
            "part", "vendor", "product", "version", "update", "edition"
            "language", "sw_edition", "target_sw", "target_hw", "other"
        ]

        query = "SELECT `name%s` FROM `cpe` WHERE " % ver
        if not include_deprecated:
            query += "`deprecated` = 0 AND "
        query += "(`name%s` = ?" % ver
        query += " OR (%s)" % " AND ".join(
            "`%s` = ?" % columns[i]
            for i in xrange(len(columns))
            if parsed[i] and parsed[i] != "*"
        )
        query += ");"

        self.__cursor.execute(query, params)
        return set(row[0] for row in self.__cursor.fetchall())


    #--------------------------------------------------------------------------
    @transactional
    def get_title(self, cpe):
        """
        Get the user-friendly title of a CPE name.

        :param CPE: CPE name.
        :type CPE: str | unicode
        """
        ver = get_cpe_version(cpe).replace(".", "")
        query = (
            "SELECT `title` FROM `cpe` WHERE `name%s` = ? LIMIT 1;"
        ) % ver
        self.__cursor.execute(query, (cpe,))
        row = self.__cursor.fetchone()
        if not row:
            raise KeyError("CPE name not found: %s" % cpe)
        return row[0]


    #--------------------------------------------------------------------------
    @transactional
    def search(self, **kwargs):
        """
        Search the CPE database for the requested fields.
        The value '*' is assumed for missing fields.

        :keyword title: User-friendly product name.
        :type title: str | unicode

        :keyword part: CPE class. Use "a" for applications,
            "o" for operating systems or "h" for hardware devices.
        :type part: str | unicode

        :keyword vendor: Person or organization that manufactured or
            created the product.
        :type vendor: str | unicode

        :keyword product: The most common and recognizable title or name
            of the product.
        :type product: str | unicode

        :keyword version: Vendor-specific alphanumeric strings
            characterizing the particular release version of the product.
        :type version: str | unicode

        :keyword update: Vendor-specific alphanumeric strings
            characterizing the particular update, service pack, or point
            release of the product.
        :type update: str | unicode

        :keyword edition: Legacy 'edition' attribute from CPE 2.2.
        :type edition: str | unicode

        :keyword language: Language tag for the language supported in the user
            interface of the product.
        :type language: str | unicode

        :keyword sw_edition: Characterizes how the product is tailored to a
            particular market or class of end users.
        :type sw_edition: str | unicode

        :keyword target_sw: Software computing environment within which the
            product operates.
        :type target_sw: str | unicode

        :keyword target_hw: Instruction set architecture (e.g., x86) on which
            the product operates.
        :type target_hw: str | unicode

        :keyword other: Any other general descriptive or identifying
            information which is vendor- or product-specific and which
            does not logically fit in any other attribute value.
        :type other: str | unicode

        :returns: Set of matching CPE names.
        :rtype: set(str|unicode)
        """
        columns = [
            "title",
            "part", "vendor", "product", "version", "update", "edition",
            "language", "sw_edition", "target_sw", "target_hw", "other"
        ]
        if set(kwargs).difference(columns):
            raise TypeError("Unknown keyword arguments: %s"
                    % ", " % sorted(set(kwargs).difference(columns)) )
        query = "SELECT `name23` FROM `cpe` WHERE "
        query += " AND ".join(
            "`%s` LIKE ?" % field
            for field in columns
            if field in kwargs and kwargs[field] != "*"
        )
        params = [
            "%%%s%%" % kwargs[field].replace("%", "%%")
            for field in columns
            if field in kwargs and kwargs[field] != "*"
        ]
        self.__cursor.execute(query, params)
        return set(row[0] for row in self.__cursor.fetchall())
