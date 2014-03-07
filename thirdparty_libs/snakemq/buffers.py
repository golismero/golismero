# -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import threading
from collections import deque

# TODO utilize io module

############################################################################
############################################################################

MAX_BUF_CHUNK_SIZE = 64 * 1024

############################################################################
############################################################################

class BufferException(Exception):
    pass

class BufferTimeout(BufferException):
    pass

class BufferTooLarge(BufferException):
    """
    Raised when you want to put larger piece then the buffer max size.
    """
    pass

############################################################################
############################################################################

class StreamBuffer(object):
    def __init__(self):
        self.size = 0  #: current size of the buffer
        self.max_size = None
        self.queue = deque()
        self.not_full_cond = threading.Condition()

    ############################################################

    def __del__(self):
        self.clear()

    ############################################################

    def clear(self):
        with self.not_full_cond:
            self.queue.clear()
            self.size = 0
            self.not_full_cond.notify()

    ############################################################

    def set_max_size(self, max_size):
        """
        @param max_size: None or number of bytes: L{StreamBuffer.put} will
                      block if the content will be bigger then C{max_size}.
                      WARNING: there must be only one thread inserting data at
                      a time
        """
        assert (max_size is None) or (max_size > 0)
        self.max_size = max_size

    ############################################################

    def put(self, data, timeout=None):
        """
        Add to the right side. It will block if the buffer will exceed C{max_size}.
        If C{max_size} is set then C{len(data)} must not be longer then the maximal
        size.
        """
        assert type(data) == bytes
        if not data:
            # do not insert an empty string
            return

        data_len = len(data)
        if self.max_size and (data_len > self.max_size):
            raise BufferTooLarge("len(data)=%i > max_size=%i" %
                                  (data_len, self.max_size))

        with self.not_full_cond:
            if self.max_size and (self.size + data_len > self.max_size):
                self.not_full_cond.wait(timeout)
                if self.size + data_len > self.max_size:
                    raise BufferTimeout

            self.size += data_len
            for i in range(len(data) // MAX_BUF_CHUNK_SIZE + 1):
                chunk = data[i * MAX_BUF_CHUNK_SIZE:(i + 1) * MAX_BUF_CHUNK_SIZE]
                if not chunk:
                    break
                self.queue.append(chunk)
                del chunk
            del data

    ############################################################

    def get(self, size, cut=True):
        """
        Get from the left side.
        @param cut: True = remove returned data from buffer
        @return: max N-bytes from the buffer.
        """
        assert (((self.size > 0) and (len(self.queue) > 0))
             or ((self.size == 0) and (len(self.queue) == 0)))

        retbuf = []
        i = 0
        with self.not_full_cond:
            orig_size = self.size
            while size and self.queue:
                if cut:
                    fragment = self.queue.popleft()
                else:
                    fragment = self.queue[i]

                if len(fragment) > size:
                    if cut:
                        # paste back the rest
                        self.queue.appendleft(fragment[size:])
                    # get only needed
                    fragment = fragment[:size]
                    frag_len = size
                else:
                    frag_len = len(fragment)

                retbuf.append(fragment)
                del fragment

                size -= frag_len
                if cut:
                    self.size -= frag_len
                else:
                    i += 1
                    if i == len(self.queue):
                        break

            if (self.max_size and (orig_size >= self.max_size) and
                                  (self.size < self.max_size)):
                self.not_full_cond.notify()

        return b"".join(retbuf)

    ############################################################

    def cut(self, size):
        """
        More efficient version of get(cut=True) and no data will be returned.
        """
        assert (((self.size > 0) and (len(self.queue) > 0))
             or ((self.size == 0) and (len(self.queue) == 0)))

        with self.not_full_cond:
            orig_size = self.size
            while size and self.queue:
                fragment = self.queue.popleft()

                if len(fragment) > size:
                    # paste back the rest
                    self.queue.appendleft(fragment[size:])
                    frag_len = size
                else:
                    frag_len = len(fragment)

                del fragment
                size -= frag_len
                self.size -= frag_len

            if (self.max_size and (orig_size >= self.max_size) and
                                  (self.size < self.max_size)):
                self.not_full_cond.notify()

    ############################################################

    def __len__(self):
        assert sum([len(item) for item in self.queue]) == self.size
        return self.size
