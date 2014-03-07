# -*- coding: utf-8 -*-
"""
Stupid poll implementation for non-epoll systems.
Wrapper for select. Not working for file descriptors.
"""

import select
import time

#########################################################################

if not hasattr(select, "epoll"):
    select.EPOLLIN = 1
    select.EPOLLOUT = 4
    select.EPOLLERR = 8
    select.EPOLLHUP = 16

#########################################################################

class SelectPoll(object):
    def __init__(self):
        self.fds = {}

    def register(self, fd, eventmask=select.EPOLLIN | select.EPOLLOUT):
        self.fds[fd] = eventmask

    def unregister(self, fd):
        try:
            del self.fds[fd]
        except KeyError:
            pass

    def modify(self, fd, eventmask):
        self.fds[fd] = eventmask

    @staticmethod
    def _socket_to_fd(obj):
        """
        convert a socket-like object to a file descriptor
        """
        if hasattr(obj, "fileno"):
            fd = obj.fileno()
        else:
            fd = obj
        return fd

    def poll(self, timeout):
        """
        @param timeout: seconds
        """
        if len(self.fds) == 0:
            time.sleep(timeout)
            return []

        rlist = []
        wlist = []
        xlist = []
        for fd, mask in self.fds.items():
            fd = self._socket_to_fd(fd)
            if mask & select.EPOLLIN:
                rlist.append(fd)
            if mask & select.EPOLLOUT:
                wlist.append(fd)
            xlist.append(fd)

        rlist, wlist, xlist = select.select(rlist, wlist, xlist, timeout)

        res = {}
        for fd in rlist:
            res[fd] = res.get(fd, 0) | select.EPOLLIN
        for fd in wlist:
            res[fd] = res.get(fd, 0) | select.EPOLLOUT
        for fd in xlist:
            res[fd] = res.get(fd, 0) | select.EPOLLERR

        return res.items()

#########################################################################

if hasattr(select, "epoll"):
    poll = select.epoll
else:
    poll = SelectPoll
