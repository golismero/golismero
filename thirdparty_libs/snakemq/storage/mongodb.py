# -*- coding: utf-8 -*-
"""
MongoDB queue storage.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt)
"""

from binascii import b2a_base64, a2b_base64

from snakemq.message import Message
from snakemq.storage import QueuesStorageBase

import pymongo

###########################################################################
###########################################################################

class MongoDbQueuesStorage(QueuesStorageBase):
    def __init__(self, host="localhost", port=27017, database="snakemq",
                  collection="snakemq"):
        self.conn = pymongo.Connection(host, port)
        self.database = self.conn[database]
        self.collection = self.database[collection]
        self.all_items = self.collection.snakemq_items

    ####################################################

    def close(self):
        self.conn.disconnect()
        self.conn = None
        self.database = None
        self.collection = None
        self.all_items = None

    ####################################################

    def get_queues(self):
        grouped = self.all_items.group(["queue_name"], {}, {},
                                        "function(obj, prev){}")
        return [item["queue_name"] for item in grouped]

    ####################################################

    def get_items(self, queue_name):
        items = []
        # XXX this might need some explicit sorting
        dbitems = self.all_items.find({"queue_name": queue_name})
        for item in dbitems:
            items.append(Message(uuid=a2b_base64(item["uuid"]),
                                  data=a2b_base64(item["data"]),
                                  ttl=item["ttl"],
                                  flags=item["flags"]))
        return items

    ####################################################

    def push(self, queue_name, item):
        item = {"queue_name": queue_name, "uuid": b2a_base64(item.uuid),
                "data": b2a_base64(item.data), "ttl": item.ttl, "flags": item.flags}
        self.all_items.insert(item)

    ####################################################

    def delete_items(self, items):
        for item in items:
            self.all_items.remove({"uuid": b2a_base64(item.uuid)})

    ####################################################

    def delete_all(self):
        self.all_items.remove()

    ####################################################

    def update_items_ttl(self, items):
        for item in items:
            self.all_items.update({"uuid": b2a_base64(item.uuid)},
                      {"$set": {"ttl": item.ttl}})
