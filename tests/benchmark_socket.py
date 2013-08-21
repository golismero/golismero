#!/usr/bin/env python
# Socket test

from platform import uname, system_alias, python_implementation, python_version, architecture
from select import select
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from thread import start_new_thread

def print_current_platform():
    (system, node, release, version, machine, processor) = uname()
    bits = architecture()[0]
    alias = "%s %s %s" % system_alias(system, release, version)
    python = "%s %s" % (python_implementation(), python_version())
    print "Using %s (%s) on %s, %s" % (python, bits, alias, machine)

def test_fd_limit():
    print "Testing the maximum number of sockets that can be created..."
    top = 1024 * 1024
    limit = top
    fds = []
    try:
        try:
            while limit > 0:
                fds.append(socket(AF_INET, SOCK_STREAM))
                limit -= 1
        finally:
            for fd in fds:
                try:
                    fd.close()
                except Exception:
                    pass
    except Exception:
        if limit == top:
            raise
    if limit:
        print "--> Limit found at %d sockets" % (top - limit)
    else:
        print "--> No limit found, stopped trying at %d" % top

def test_select_limit():
    print "Testing the maximum number of sockets that can be selected..."
    top = 1024 * 1024
    limit = top
    fds = []
    try:
        try:
            while limit > 0:
                fds.append(socket(AF_INET, SOCK_STREAM))
                select(fds, fds, fds, 0.1)
                limit -= 1
        finally:
            for fd in fds:
                try:
                    fd.close()
                except Exception:
                    pass
    except Exception:
        if limit == top:
            raise
    if limit:
        print "--> Limit found at %d sockets" % (top - limit)
    else:
        print "--> No limit found, stopped trying at %d" % top

def test_accept_limit():
    print "Testing the maximum number of incoming connections that can be accepted..."
    top = 1024 * 1024
    limit = top
    try:
        ls = socket(AF_INET, SOCK_STREAM)
        try:
            ls.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            ls.bind(("127.0.0.1", 0))
            ls.listen(top)
            p = ls.getsockname()[1]
            start_new_thread(helper_accept_limit, (ls,))
            fds = []
            try:
                while limit > 0:
                    s = socket(AF_INET, SOCK_STREAM)
                    try:
                        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                        s.settimeout(1.0)
                        s.connect(("127.0.0.1", p))
                        ##print ".",
                    except Exception:
                        s.close()
                        raise
                    fds.append(s)
                    limit -= 1
            finally:
                for s in fds:
                    try:
                        try:
                            s.recv(1)
                            s.shutdown(2)
                        finally:
                            s.close()
                    except Exception:
                        pass
        finally:
            ls.close()
    except Exception:
        if limit == top:
            raise
    if limit:
        print "--> Limit found at %d sockets" % (top - limit)
    else:
        print "--> No limit found, stopped trying at %d" % top

def helper_accept_limit(ls):
    try:
        while True:
            s = ls.accept()
            try:
                try:
                    s.shutdown(2)
                finally:
                    s.close()
            except Exception:
                pass
    except Exception:
        pass

if __name__ == "__main__":
    print_current_platform()
    test_fd_limit()
    test_select_limit()
    test_accept_limit()  # this one can mess up your networking for a while...

# Some results...
"""
Using CPython 2.7.5 (32bit) on Windows 7 6.1.7601, AMD64
Testing the maximum number of sockets that can be created...
--> No limit found, stopped trying at 1048576
Testing the maximum number of sockets that can be selected...
--> Limit found at 512 sockets
Testing the maximum number of incoming connections that can be accepted...
--> Limit found at 16364 sockets
"""
