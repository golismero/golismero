# -*- coding: utf-8 -*-
"""
Link loop poll interruptor.

Read part must be nonblocking.
"""
# pylint: disable=C0103

import os
import socket
import errno
import select

if os.name != "nt":
    import fcntl

############################################################################
############################################################################

class BellBase(object):
    def __init__(self):
        self.r = None
        self.w = None

    def wait(self, timeout=1):
        select.select([self.r], [], [], timeout)

    def __repr__(self):
        return "<%s %x r=%r w=%r>" % (self.__class__.__name__,
                                      id(self), self.r, self.w)

############################################################################
############################################################################

class PosixBell(BellBase):
    def __init__(self):
        BellBase.__init__(self)
        self.r, self.w = os.pipe()
        fcntl.fcntl(self.r, fcntl.F_SETFL, os.O_NONBLOCK)

    def write(self, buf):
        os.write(self.w, buf)

    def read(self, num):
        return os.read(self.r, num)

    def close(self):
        os.close(self.r)
        os.close(self.w)

############################################################################
############################################################################

class WinBell(BellBase):
    """
    WinBell is no bell.
    """
    def __init__(self):
        BellBase.__init__(self)
        r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r.bind(("127.0.0.1", 0))
        r.listen(1)
        self.sw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sw.connect(r.getsockname())
        self.w = self.sw.fileno()
        self.sr = r.accept()[0]
        self.sr.setblocking(False)
        self.r = self.sr.fileno()
        r.close()

    def write(self, buf):
        self.sw.send(buf)

    def read(self, num):
        try:
            return self.sr.recv(num)
        except socket.error as exc:
            # emulate os.read exception
            if exc.errno == errno.WSAEWOULDBLOCK:
                new_exc = OSError()
                new_exc.errno = errno.EAGAIN
                raise new_exc
            else:
                raise

    def close(self):
        self.sr.close()
        self.sw.close()

############################################################################
############################################################################

if os.name == "nt":
    Bell = WinBell
else:
    Bell = PosixBell
