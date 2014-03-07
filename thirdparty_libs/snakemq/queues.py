# -*- coding: utf-8 -*-
"""
Queues, manager. TTL is decreased only by the disconnected time. Queue manager
"downtime" is not included.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt)
"""

import time
import logging

from snakemq.storage import QueuesStorageBase
from snakemq.message import FLAG_PERSISTENT

###########################################################################
###########################################################################
# queue
###########################################################################

class Queue(object):
    def __init__(self, name, manager):
        self.name = name
        self.manager = manager
        self.queue = []
        self.last_disconnect_absolute = None
        self.connected = False

        if manager.storage:
            self.load_persistent_data()
        self.disconnect()

    ####################################################

    def load_persistent_data(self):
        self.queue[:] = self.manager.storage.get_items(self.name)

    ####################################################

    def connect(self):
        self.connected = True

        # remove outdated items and update TTL
        diff = time.time() - self.last_disconnect_absolute
        fresh_queue = []
        storage_update_ttls = []
        storage_to_delete = []
        for item in self.queue:
            if item.ttl is None:
                fresh_queue.append(item)
                continue
            item.ttl -= diff
            if item.ttl >= 0:  # must include 0
                fresh_queue.append(item)
                if item.flags & FLAG_PERSISTENT:
                    storage_update_ttls.append(item)
            else:
                if item.flags & FLAG_PERSISTENT:
                    storage_to_delete.append(item)
        if self.manager.storage:
            self.manager.storage.update_items_ttl(storage_update_ttls)
            self.manager.storage.delete_items(storage_to_delete)
        self.queue[:] = fresh_queue

    ####################################################

    def disconnect(self):
        self.connected = False
        self.last_disconnect_absolute = time.time()

    ####################################################

    def push(self, item):
        if (item.ttl is not None) and (item.ttl <= 0) and not self.connected:
            # do not queue already obsolete items
            return
        self.queue.append(item)
        to_store = (item.flags & FLAG_PERSISTENT) and self.manager.storage
        if to_store and ((item.ttl is None) or (item.ttl > 0)):
            # do not store items with ttl==0
            self.manager.storage.push(self.name, item)

    ####################################################

    def get(self):
        """
        Get first item but do not remove it. Use {Queue.pop()} to remove it
        e.g. after successful delivery. Items are always "fresh".
        @return: item or None if empty
        """
        # no need to test TTL because it is filtered in connect()
        if self.queue:
            return self.queue[0]
        else:
            return None

    ####################################################

    def pop(self):
        """
        Remove first item.
        @return: None
        """
        if not self.queue:
            return
        item = self.queue.pop(0)
        if (item.flags & FLAG_PERSISTENT) and self.manager.storage:
            self.manager.storage.delete_items([item])

    ####################################################

    def __len__(self):
        return len(self.queue)

###########################################################################
###########################################################################
# manager
###########################################################################

class QueuesManager(object):
    def __init__(self, storage):
        """
        @param storage: None or persistent storage
        """
        assert (storage is None) or isinstance(storage, QueuesStorageBase)
        self.storage = storage
        self.queues = {}  #: name:Queue
        self.log = logging.getLogger("snakemq.queuesmanager")
        if storage:
            self.load_from_storage()
            self.log.debug("queues in storage: %i" % len(self.queues))

    ####################################################

    def load_from_storage(self):
        for queue_name in self.storage.get_queues():
            self.get_queue(queue_name)

    ####################################################

    def get_queue(self, queue_name):
        """
        @return: Queue
        """
        if queue_name in self.queues:
            queue = self.queues[queue_name]
        else:
            queue = Queue(queue_name, self)
            self.queues[queue_name] = queue
        return queue

    ####################################################

    def cleanup(self):
        """
        remove empty queues
        """
        for queue_name, queue in self.queues.items():
            if not queue:
                del self.queues[queue_name]

    ####################################################

    def close(self):
        """
        Delete queues and close persistent storage.
        """
        self.queues.clear()
        if self.storage:
            self.storage.close()
            self.storage = None

    ####################################################

    def collect_garbage(self):
        """
        Call this periodically to remove obsolete items and empty queues.
        """
        # TODO

    ####################################################

    def __len__(self):
        return len(self.queues)
