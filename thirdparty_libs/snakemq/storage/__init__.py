# -*- coding: utf-8 -*-
"""
Queues persistent storage.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt)
"""

from collections import defaultdict, deque

###########################################################################
###########################################################################

class QueuesStorageBase(object):
    def close(self):
        raise NotImplementedError

    def get_queues(self):
        """
        @return: list of queues names
        """
        raise NotImplementedError

    def get_items(self, queue_name):
        """
        @return: items of the queue
        """
        raise NotImplementedError

    def push(self, queue_name, item):
        raise NotImplementedError

    def delete_items(self, items):
        raise NotImplementedError

    def delete_all(self):
        """
        Delete all items and queues.
        """
        raise NotImplementedError

    def update_items_ttl(self, items):
        raise NotImplementedError

###########################################################################
###########################################################################

class MemoryQueuesStorage(QueuesStorageBase):
    """
    For testing purposes - B{THIS STORAGE IS NOT PERSISTENT.}
    """
    def __init__(self):
        self.queues = defaultdict(deque)  #: name:queue

    def close(self):
        pass

    def get_queues(self):
        return self.queues.keys()

    def get_items(self, queue_name):
        return self.queues[queue_name]

    def push(self, queue_name, item):
        self.queues[queue_name].append(item)

    def delete_items(self, items):
        for queue in self.queues.values():
            for item in items:
                try:
                    queue.remove(item)
                except ValueError:
                    pass

    def delete_all(self):
        self.queues.clear()

    def update_items_ttl(self, items):
        # TTLs are already updated by the caller
        pass

