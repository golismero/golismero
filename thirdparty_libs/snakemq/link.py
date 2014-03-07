# -*- coding: utf-8 -*-
"""
:author: David Siroky (siroky@dasir.cz)
:license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import select
import socket
import ssl
import os
import errno
import time
import bisect
import logging

from snakemq.exceptions import SendNotFinished

from snakemq.poll import poll
from snakemq.pollbell import Bell
from snakemq.callbacks import Callback

############################################################################
############################################################################

RECONNECT_INTERVAL = 3.0
RECV_BLOCK_SIZE = 256 * 1024
POLL_TIMEOUT = 0.2
BELL_READ = 1024

SSL_HANDSHAKE_IN_PROGRESS = 0
SSL_HANDSHAKE_DONE = 1
SSL_HANDSHAKE_FAILED = 2

############################################################################
############################################################################

class SSLConfig(object):
    """
    Container for SSL configuration.
    """
    def __init__(self, keyfile=None, certfile=None, cert_reqs=ssl.CERT_NONE,
                  ssl_version=ssl.PROTOCOL_SSLv23, ca_certs=None):
        """
        :see: ssl.wrap_socket
        """
        self.keyfile = keyfile
        self.certfile = certfile
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version
        self.ca_certs = ca_certs

############################################################################
############################################################################

class LinkSocket(object):
    def __init__(self, sock=None, ssl_config=None, remote_peer=None):
        assert (sock is None) or isinstance(sock, socket.socket)
        self.sock = sock or self.create_socket()
        self.ssl_config = ssl_config
        self.remote_peer = remote_peer

        self.is_connector = False  #: connector or listener
        self.conn_id = None
        self.reset()

    #########################################################

    def reset(self):
        self.write_buf = None  #: for SSL
        self.last_send_size = 0
        self.send_finished = True

    #########################################################

    @staticmethod
    def create_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        return sock

    #########################################################

    def listen(self, address):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(address)
        self.sock.listen(10)

    #########################################################

    def accept(self):
        newsock, addr = self.sock.accept()
        newsock.setblocking(False)
        if self.ssl_config:
            newsock = ssl.wrap_socket(newsock, server_side=True,
                                      do_handshake_on_connect=False,
                                      ssl_version=self.ssl_config.ssl_version,
                                      keyfile=self.ssl_config.keyfile,
                                      certfile=self.ssl_config.certfile,
                                      cert_reqs=self.ssl_config.cert_reqs,
                                      ca_certs=self.ssl_config.ca_certs)
        newsock = LinkSocket(newsock, self.ssl_config)
        self.remote_peer = addr
        return newsock, addr

    #########################################################

    def connect(self):
        self.is_connector = True
        if self.ssl_config:
            self.sock = ssl.wrap_socket(self.sock, server_side=False,
                                      do_handshake_on_connect=False,
                                      ssl_version=self.ssl_config.ssl_version,
                                      keyfile=self.ssl_config.keyfile,
                                      certfile=self.ssl_config.certfile,
                                      cert_reqs=self.ssl_config.cert_reqs,
                                      ca_certs=self.ssl_config.ca_certs)
        return self.sock.connect_ex(self.remote_peer)

    #########################################################

    def send(self, data):
        """
        If data is ``None`` then ``self.write_buf`` is used.
        """
        if (data is not None) and not self.send_finished:
            raise SendNotFinished(("previous send on %r is not finished, " +
                              "wait for on_ready_to_send") % self)

        data = data or self.write_buf

        self.send_finished = False
        if self.ssl_config is None:
            self.last_send_size = self.sock.send(data)
        else:
            try:
                self.last_send_size = self.sock.write(data)
                self.write_buf = None
            except ssl.SSLError as exc:
                if exc.args[0] != ssl.SSL_ERROR_WANT_WRITE:
                    raise
                self.write_buf = data

    #########################################################

    def recv(self, length):
        return self.sock.recv(length)

    #########################################################

    def fileno(self):
        return self.sock.fileno()

    #########################################################

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except socket.error as exc:
            if exc.errno not in (errno.ENOTCONN, errno.ECONNRESET):
                raise
        self.sock.close()
        if self.is_connector:
            self.reset()
            # closed socket cannot be reconnected so a new one must be created
            self.sock = self.create_socket()

    #########################################################

    def create_ssl_context(self):
        assert isinstance(self.sock, ssl.SSLSocket)
        # this is always called from handle_connect so server_side=False
        if hasattr(self.sock, "context"):
            # py3.2
            self.sock._sslobj = self.sock.context._wrap_socket(self.sock,
                                                  False, None)
        else:
            if hasattr(self.sock, "_sock"):
                raw_sock = self.sock._sock  # py2
            else:
                raw_sock = self.sock  # py3.1
            self.sock._sslobj = ssl._ssl.sslwrap(raw_sock, False,
                                        self.sock.keyfile, self.sock.certfile,
                                        self.sock.cert_reqs, self.sock.ssl_version,
                                        self.sock.ca_certs)

    #########################################################

    def __repr__(self):
        return "<%s 0x%x fileno=%r conn_id=%r>" % (self.__class__.__name__, id(self),
                                      self.fileno(), self.conn_id)

    #########################################################

    def getpeercert(self, binary_form=False):
        """
        :see: python documentation - ssl.SSLSocket.getpeercert()
        :return: peer's SSL certificate if available or None
        """
        if self.ssl_config is None:
            return None
        else:
            return self.sock._sslobj.peer_certificate(binary_form)

############################################################################
############################################################################

class Link(object):
    """
    Just a bare wire stream communication. Keeper of opened (TCP) connections.
    **Not thread-safe** but you can synchronize with the loop using
    :meth:`~.wakeup_poll` and :attr:`~.on_loop_pass`.
    """

    def __init__(self):
        self.log = logging.getLogger("snakemq.link")

        self.reconnect_interval = RECONNECT_INTERVAL  #: in seconds
        self.recv_block_size = RECV_BLOCK_SIZE

        #{ callbacks
        self.on_connect = Callback()  #: ``func(conn_id)``
        self.on_disconnect = Callback()  #: ``func(conn_id)``
        #: ``func(conn_id, data)``
        self.on_recv = Callback()
        #: ``func(conn_id, last_send_size)``, last send was successful
        self.on_ready_to_send = Callback()
        #: ``func()``, called after poll is processed
        self.on_loop_pass = Callback()
        #}

        self._do_loop = False  #: False breaks the loop

        self._new_conn_id = 0  #: counter for conn id generator

        self.poller = poll()
        self._poll_bell = Bell()
        self.log.debug("poll bell %r" % self._poll_bell)
        self.poller.register(self._poll_bell.r, select.EPOLLIN)  # read part

        self._sock_by_fd = {}
        self._sock_by_conn = {}

        self._listen_socks = {}  #: address:sock
        self._listen_socks_filenos = set()

        self._connectors = {}  #: address:sock
        self._socks_waiting_to_connect = set()
        self._plannned_connections = []  #: (when, address)
        self._reconnect_intervals = {}  #: address:interval

        self._in_ssl_handshake = set()  #: set of LinkSocket

    ##########################################################

    def cleanup(self):
        """
        Close all sockets and remove all connectors and listeners.
        """
        self._poll_bell.close()

        for address in list(self._connectors.keys()):
            self.del_connector(address)

        for address in list(self._listen_socks.keys()):
            self.del_listener(address)

        for sock in list(self._sock_by_fd.values()):
            self.handle_close(sock)

        assert not self._do_loop

        # be sure that no memory is wasted
        assert len(self._sock_by_fd) == 0
        assert len(self._sock_by_conn) == 0
        assert len(self._listen_socks) == 0
        assert len(self._listen_socks_filenos) == 0
        assert len(self._connectors) == 0
        assert len(self._socks_waiting_to_connect) == 0
        assert len(self._plannned_connections) == 0
        assert len(self._reconnect_intervals) == 0
        assert len(self._in_ssl_handshake) == 0

    ##########################################################

    def add_connector(self, address, reconnect_interval=None, ssl_config=None):
        """
        This will not create an immediate connection. It just adds a connector
        to the pool.

        :param address: remote address
        :param reconnect_interval: reconnect interval in seconds
        :return: connector address (use it for deletion)
        """
        address = socket.gethostbyname(address[0]), address[1]
        if address in self._connectors:
            raise ValueError("connector '%r' already set", address)
        sock = LinkSocket(remote_peer=address, ssl_config=ssl_config)
        self._connectors[address] = sock
        self._reconnect_intervals[address] = \
                reconnect_interval or self.reconnect_interval
        self.plan_connect(0, address)  # connect ASAP
        return address

    ##########################################################

    def del_connector(self, address):
        """
        Delete connector.
        """
        sock = self._connectors.pop(address)
        self._socks_waiting_to_connect.discard(sock)
        del self._reconnect_intervals[address]

        # filter out address from plan
        self._plannned_connections[:] = \
            [(when, _address)
                  for (when, _address) in self._plannned_connections
                  if _address != address]

    ##########################################################

    def add_listener(self, address, ssl_config=None):
        """
        Adds listener to the pool. This method is not blocking. Run only once.

        :return: listener address (use it for deletion)
        """
        address = socket.gethostbyname(address[0]), address[1]
        if address in self._listen_socks:
            raise ValueError("listener '%r' already set" % address)
        listen_sock = LinkSocket(ssl_config=ssl_config)
        listen_sock.listen(address)
        if address[1] == 0:
            address = listen_sock.sock.getsockname()

        fileno = listen_sock.fileno()
        self._sock_by_fd[fileno] = listen_sock
        self._listen_socks[address] = listen_sock
        self._listen_socks_filenos.add(fileno)
        self.poller.register(listen_sock, select.EPOLLIN)

        self.log.debug("add_listener fd=%i %r" % (fileno, address))
        return address

    ##########################################################

    def del_listener(self, address):
        """
        Delete listener.
        """
        sock = self._listen_socks.pop(address)
        fileno = sock.fileno()
        self._listen_socks_filenos.remove(fileno)
        del self._sock_by_fd[fileno]
        sock.close()

    ##########################################################

    def wakeup_poll(self):
        """
        Thread-safe.
        """
        self._poll_bell.write(b"a")

    ##########################################################

    def send(self, conn_id, data):
        """
        After calling `send` wait for :py:attr:`~.on_ready_to_send` before
        sending next data.

        This operation is non-blocking, data might be lost if you close
        connection before proper delivery. Always wait for
        :py:attr:`~.on_ready_to_send` to have confirmation about successful
        send and information about amount of sent data.

        Do not feed this method with large bulks of data in MS Windows. It
        sometimes blocks for a little time even in non-blocking mode.

        Optimal data size is 16k-64k.
        """
        try:
            sock = self._sock_by_conn[conn_id]
            sock.send(data)
            self.poller.modify(sock, select.EPOLLIN | select.EPOLLOUT)
        except socket.error as exc:
            err = exc.args[0]
            if err == errno.EWOULDBLOCK:
                pass # ignore it, make caller to wait for "ready to send"
            elif err in (errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN,
                        errno.ECONNABORTED, errno.EPIPE, errno.EBADF):
                self.handle_close(sock)
            else:
                raise

    ##########################################################

    def close(self, conn_id):
        self.handle_close(self._sock_by_conn[conn_id])

    ##########################################################

    def loop(self, poll_timeout=POLL_TIMEOUT, count=None, runtime=None):
        """
        Start the communication loop.

        :param poll_timeout: in seconds, should be less then the minimal
                              reconnect time
        :param count: count of poll events (not timeouts) or None
        :param runtime: max time of running loop in seconds (also depends
                        on the poll timeout) or None
        """
        self._do_loop = True

        # plan fresh connects
        self.deal_connects()

        time_start = time.time()
        while (self._do_loop and
                (count is not 0) and
                not ((runtime is not None) and
                      (time.time() - time_start > runtime))):
            is_event = len(self.poll(poll_timeout))
            self.on_loop_pass()
            if is_event and (count is not None):
                count -= 1
            self.deal_connects()

        self._do_loop = False

    ##########################################################

    def stop(self):
        """
        Interrupt the loop. It doesn't perform a cleanup.
        """
        self._do_loop = False

    ##########################################################

    def get_socket_by_conn(self, conn):
        """
        :return: LinkSocket
        """
        return self._sock_by_conn[conn]

    ##########################################################
    ##########################################################

    def new_connection_id(self, sock):
        """
        Create a virtual connection ID. This ID will be passed to ``on_*``
        functions. It is a unique identifier for every new connection during
        the instance's existence.
        """
        # NOTE e.g. pair address+port can't be used as a connection identifier
        # because it is not unique enough. It might be the same for 2 connections
        # distinct in time.

        self._new_conn_id += 1
        conn_id = "%ifd%i" % (self._new_conn_id, sock.fileno())
        sock.conn_id = conn_id
        self._sock_by_conn[conn_id] = sock
        return conn_id

    ##########################################################

    def del_connection_id(self, sock):
        conn_id = sock.conn_id
        del self._sock_by_conn[conn_id]
        sock.conn_id = None

    ##########################################################

    def plan_connect(self, when, address):
        item = (when, address)
        idx = bisect.bisect(self._plannned_connections, item)
        self._plannned_connections.insert(idx, item)

    ##########################################################

    def connect(self, address):
        """
        Try to make an actual connection.
        :return: True if connected
        """
        sock = self._connectors[address]
        err = sock.connect()

        self.poller.register(sock)
        self._sock_by_fd[sock.fileno()] = sock
        self._socks_waiting_to_connect.add(sock)

        if err in (0, errno.EISCONN):
            self.handle_connect(sock)
            return True
        elif err in (errno.ECONNREFUSED, errno.ENETUNREACH):
            self.handle_conn_refused(sock)
        elif err not in (errno.EINPROGRESS, errno.EWOULDBLOCK):
            raise socket.error(err, errno.errorcode[err])

        return False

    ##########################################################

    def ssl_handshake(self, sock):
        failed = False
        err = None

        if sock.sock._sslobj is None:
            self._in_ssl_handshake.remove(sock)
            return SSL_HANDSHAKE_FAILED

        try:
            if sock.sock._sslobj is None:
                # this might be caused by SSL-wrapping a socket with not
                # fully created connection (like if you nmap a port)
                failed = True
                err = "no _sslobj"
            else:
                sock.sock.do_handshake()
        except ssl.SSLError as exc:
            err = exc
            if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                self.poller.modify(sock, select.EPOLLIN)
            elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self.poller.modify(sock, select.EPOLLOUT)
            else:
                failed = True
        except socket.error as exc:
            err = exc
            failed = True
        else:
            self._in_ssl_handshake.remove(sock)
            self.poller.modify(sock, select.EPOLLIN)
            self.log.debug("SSL handshake done %s, cipher=%r" %
                            (sock.conn_id, sock.sock.cipher()))
            return SSL_HANDSHAKE_DONE
        
        if failed:
            self.log.error("SSL handshake %s: %r" % (sock.conn_id, err))
            self.handle_close(sock)
            self._in_ssl_handshake.remove(sock)
            return SSL_HANDSHAKE_FAILED

        return SSL_HANDSHAKE_IN_PROGRESS

    ##########################################################

    def handle_connect(self, sock):
        self._socks_waiting_to_connect.remove(sock)
        conn_id = self.new_connection_id(sock)
        self.log.info("connect %s %r" % (conn_id, sock.remote_peer))

        handshake_res = SSL_HANDSHAKE_IN_PROGRESS
        if sock.ssl_config:
            sock.create_ssl_context()
            self._in_ssl_handshake.add(sock)
            handshake_res = self.ssl_handshake(sock)
            if handshake_res == SSL_HANDSHAKE_FAILED:
                return

        self.poller.modify(sock, select.EPOLLIN)

        if (sock.ssl_config is None) or (handshake_res == SSL_HANDSHAKE_DONE):
            self.on_connect(conn_id)

    ##########################################################

    def handle_accept(self, sock):
        try:
            newsock, address = sock.accept()
        except socket.error as exc:
            self.log.error("accept %r: %r" % (sock, exc))
            return

        conn_id = self.new_connection_id(newsock)
        self.log.info("accept %s %r" % (conn_id, address))

        self._sock_by_fd[newsock.fileno()] = newsock
        self.poller.register(newsock, select.EPOLLIN)

        handshake_res = SSL_HANDSHAKE_IN_PROGRESS
        if newsock.ssl_config:
            self._in_ssl_handshake.add(newsock)
            handshake_res = self.ssl_handshake(newsock)
            if handshake_res == SSL_HANDSHAKE_FAILED:
                return

        if (newsock.ssl_config is None) or (handshake_res == SSL_HANDSHAKE_DONE):
            self.on_connect(conn_id)

    ##########################################################

    def handle_recv(self, sock):
        conn_id = sock.conn_id
        if conn_id is None:
            # socket could be closed in one poll round before recv
            return

        # do not put it in a draining cycle to avoid other links starvation
        try:
            fragment = sock.recv(self.recv_block_size)
        except ssl.SSLError as exc:
            if exc.args[0] != ssl.SSL_ERROR_WANT_READ:
                raise
            # wait for next round, SSL context has not enough data do decrypt
        except socket.error as exc:
            # TODO catch SSL exceptions
            err = exc.args[0]
            if err in (errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN,
                        errno.ECONNABORTED, errno.EPIPE, errno.EBADF):
                self.log.error("recv %s error %s" %
                                  (conn_id, errno.errorcode[err]))
                self.handle_close(sock)
            elif err != errno.EWOULDBLOCK:
                raise
        else:
            if fragment:
                self.log.debug("recv %s len=%i" % (conn_id, len(fragment)))
                self.on_recv(conn_id, fragment)
            else:
                self.handle_close(sock)

    ##########################################################

    def handle_conn_refused(self, sock):
        self._socks_waiting_to_connect.remove(sock)
        self.poller.unregister(sock)
        del self._sock_by_fd[sock.fileno()]
        sock.close()

        address = sock.remote_peer
        self.plan_connect(time.time() + self._reconnect_intervals[address],
                          address)

    ##########################################################

    def handle_close(self, sock):
        self.poller.unregister(sock)
        del self._sock_by_fd[sock.fileno()]
        sock.close()

        if sock.conn_id is not None:
            self.log.info("disconnect %s " % sock.conn_id)
            if (sock.ssl_config is None) or (sock not in self._in_ssl_handshake):
                self.on_disconnect(sock.conn_id)
            self.del_connection_id(sock)

        if sock.is_connector:
            address = sock.remote_peer
            interval = self._reconnect_intervals.get(address)
            if interval:
                self.plan_connect(time.time() + interval, address)

    ##########################################################

    def handle_ready_to_send(self, sock):
        if sock.write_buf is None:
            sock.send_finished = True
            self.poller.modify(sock, select.EPOLLIN)
            self.log.debug("ready to send %s (last send len=%i)" % 
                            (sock.conn_id, sock.last_send_size))
            self.on_ready_to_send(sock.conn_id, sock.last_send_size)
        else:
            self.log.debug("ready to send %s, repeat" % sock.conn_id)
            sock.send(None)  # repeat last buffer

    ##########################################################

    def handle_sock_err(self, sock):
        if sock in self._socks_waiting_to_connect:
            self.handle_conn_refused(sock)
        else:
            self.handle_close(sock)

    ##########################################################

    def handle_sock_io(self, fd, sock, mask):
        if mask & select.EPOLLOUT:
            if sock in self._socks_waiting_to_connect:
                self.handle_connect(sock)
            else:
                self.handle_ready_to_send(sock)
        if mask & select.EPOLLIN:
            if fd in self._listen_socks_filenos:
                self.handle_accept(sock)
            else:
                self.handle_recv(sock)

    ##########################################################

    def handle_fd_mask(self, fd, mask):
        if fd == self._poll_bell.r:
            assert mask & select.EPOLLIN
            self._poll_bell.read(BELL_READ)  # flush the pipe
        else:
            # socket might have been already discarded by the Link
            # so this pass might be skipped
            if fd not in self._sock_by_fd:
                return
            sock = self._sock_by_fd[fd]

            if mask & (select.EPOLLERR | select.EPOLLHUP):
                self.handle_sock_err(sock)
            else:
                if sock in self._in_ssl_handshake:
                    if self.ssl_handshake(sock) == SSL_HANDSHAKE_DONE:
                        # connection is ready for user IO
                        self.on_connect(sock.conn_id)
                else:
                    self.handle_sock_io(fd, sock, mask)

    ##########################################################

    def poll(self, poll_timeout):
        """
        :return: values returned by poll
        """
        fds = []
        try:
            fds[:] = self.poller.poll(poll_timeout)
        except IOError as exc:
            if exc.errno != errno.EINTR:  # hibernate does that
                raise

        for fd, mask in fds:
            self.handle_fd_mask(fd, mask)
        return fds

    ##########################################################

    def deal_connects(self):
        now = time.time()
        to_remove = 0
        for when, address in self._plannned_connections:
            reconnect_interval = self._reconnect_intervals[address]
            if (when <= now) or (when > now + reconnect_interval * 2):
                to_remove += 1
                self.connect(address)
            else:
                break

        if to_remove:
            del self._plannned_connections[:to_remove]
