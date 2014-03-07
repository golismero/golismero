# -*- coding: utf-8 -*-
"""
SQLite queue storage.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt)
"""

import platform
import sqlite3
from binascii import b2a_hex, a2b_hex

from snakemq.message import Message, MAX_UUID_LENGTH
from snakemq.messaging import MAX_IDENT_LENGTH
from snakemq.storage import QueuesStorageBase

###########################################################################
###########################################################################

class SqliteQueuesStorage(QueuesStorageBase):
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.crs = self.conn.cursor()
        self.test_format()
        self.sweep()

    ####################################################

    def sweep(self):
        # PyPy has broken VACUUM implementation
        if platform.python_implementation() != "PyPy":
            with self.conn:
                self.crs.execute("""VACUUM""")

    ####################################################

    def test_format(self):
        """
        Make sure that the database content is OK.
        """
        # just check if the table is present
        try:
            self.conn.rollback()
            self.crs.execute("SELECT count(1) FROM items LIMIT 1")
        except Exception:  # little bit vague
            self.conn.rollback()
            self.create_structures()

    ####################################################

    def close(self):
        if self.crs:
            self.crs.close()
            self.crs = None
        if self.conn:
            self.conn.close()
            self.conn = None

    ####################################################

    def create_structures(self):
        with self.conn:
            # UUID is stored as hex
            self.crs.execute("""CREATE TABLE items (queue_name VARCHAR(%i),
                                                    uuid VARCHAR(%i),
                                                    data BLOB,
                                                    ttl REAL,
                                                    flags INTEGER)""" %
                                    (MAX_IDENT_LENGTH, MAX_UUID_LENGTH * 2))

    ####################################################

    def get_queues(self):
        self.crs.execute("""SELECT queue_name FROM items GROUP BY queue_name""")
        return [r[0] for r in self.crs.fetchall()]

    ####################################################

    def get_items(self, queue_name):
        self.crs.execute("""SELECT uuid, data, ttl, flags FROM items
                                   WHERE queue_name = ?""",
                          (queue_name,))
        items = []
        for res in self.crs.fetchall():
            uuid = a2b_hex(res[0])  # XXX python2 hack
            data = bytes(res[1])  # XXX python2 hack
            items.append(Message(uuid=uuid,
                                data=data,
                                ttl=res[2],
                                flags=res[3]))
        return items

    ####################################################

    def push(self, queue_name, item):
        with self.conn:
            self.crs.execute("""INSERT INTO items
                                    (queue_name, uuid, data, ttl, flags)
                                    VALUES (?, ?, ?, ?, ?)""",
                          (queue_name, b2a_hex(item.uuid), item.data,
                          item.ttl, item.flags))

    ####################################################

    def delete_items(self, items):
        with self.conn:
            for item in items:
                self.crs.execute("""DELETE FROM items WHERE uuid = ?""",
                              (b2a_hex(item.uuid),))

    ####################################################

    def delete_all(self):
        with self.conn:
            self.crs.execute("DELETE FROM items")

    ####################################################

    def update_items_ttl(self, items):
        with self.conn:
            for item in items:
                self.crs.execute("""UPDATE items SET ttl = ? WHERE uuid = ?""",
                                  (item.ttl, b2a_hex(item.uuid)))
