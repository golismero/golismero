# -*- coding: utf-8 -*-
"""
SQLite queue storage.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt)
"""

from binascii import b2a_hex, a2b_hex

from sqlalchemy import (create_engine, Table, Column, Integer, Float, String,
                        LargeBinary, select, MetaData)

from snakemq.message import Message, MAX_UUID_LENGTH
from snakemq.messaging import MAX_IDENT_LENGTH
from snakemq.storage import QueuesStorageBase

###########################################################################
###########################################################################

meta = MetaData()

table = Table("snakemq_items", meta,
    Column("id_", Integer, primary_key=True), # for ordering purposes
    Column("queue_name", String(MAX_IDENT_LENGTH)),
    Column("uuid", String(MAX_UUID_LENGTH * 2), unique=True),
    Column("data", LargeBinary),
    Column("flags", Integer),
    Column("ttl", Float))

###########################################################################
###########################################################################

def transaction(method):
    def wrapper(self, *args, **kwargs):
        # self ... SqlAlchemyQueuesStorage instance
        trans = self.conn.begin()
        try:
            res = method(self, *args, **kwargs)
            trans.commit()
        except:
            trans.rollback()
            raise
        return res
    return wrapper

###########################################################################
###########################################################################

class SqlAlchemyQueuesStorage(QueuesStorageBase):
    def __init__(self, *args, **kwargs):
        """
        Parameters are passed to create_engine().
        """
        self.engine = create_engine(*args, **kwargs)
        self.conn = self.engine.connect()

    ####################################################

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    ####################################################

    @transaction
    def create_structures(self):
        meta.create_all(self.conn)

    ####################################################

    @transaction
    def drop_structures(self):
        meta.drop_all(self.conn)

    ####################################################

    def get_queues(self):
        names = self.conn.execute(
              select([table.c.queue_name]).group_by(table.c.queue_name)
            ).fetchall()
        return [r.queue_name for r in names]

    ####################################################

    def get_items(self, queue_name):
        sel = table.select().where(table.c.queue_name == queue_name).order_by(table.c.id_)
        items = []
        for res in self.conn.execute(sel).fetchall():
            items.append(Message(uuid=a2b_hex(res.uuid),
                                data=bytes(res.data),
                                ttl=res.ttl,
                                flags=res.flags))
        return items

    ####################################################

    def push(self, queue_name, item):
        self.conn.execute(table.insert().values(
                                          queue_name=queue_name,
                                          uuid=b2a_hex(item.uuid),
                                          data=item.data,
                                          ttl=item.ttl,
                                          flags=item.flags))

    ####################################################

    def delete_items(self, items):
        uuids = [b2a_hex(item.uuid) for item in items]
        self.conn.execute(table.delete().where(table.c.uuid.in_(uuids)))

    ####################################################

    def delete_all(self):
        self.conn.execute(table.delete())

    ####################################################

    @transaction
    def update_items_ttl(self, items):
        for item in items:
            self.conn.execute(table.update()
                            .where(table.c.uuid == b2a_hex(item.uuid))
                            .values(ttl=item.ttl))
