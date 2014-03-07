# -*- coding: utf-8 -*-
"""
Packet format: ``[4B size|payload]``, size is bytes count (unsigned integer in
network order) of all following packet data.

:author: David Siroky (siroky@dasir.cz)
:license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import logging
import struct
from collections import deque

from snakemq.exceptions import NoConnection
from snakemq.buffers import StreamBuffer
from snakemq.exceptions import SnakeMQBrokenPacket
from snakemq.callbacks import Callback

############################################################################
############################################################################

SEND_BLOCK_SIZE = 64 * 1024

BIN_SIZE_FORMAT = "!I"  # network order 32-bit unsigned integer
SIZEOF_BIN_SIZE = struct.calcsize(BIN_SIZE_FORMAT)

############################################################################
############################################################################

def size_to_bin(size):
    # make the size a signed integer - negative integers might be
    # reserved for future extensions
    return struct.pack(BIN_SIZE_FORMAT, size)

#################################################################

def bin_to_size(buf):
    return struct.unpack(BIN_SIZE_FORMAT, buf)[0]

############################################################################
############################################################################

class ReceiveBuffer(StreamBuffer):
    def __init__(self):
        StreamBuffer.__init__(self)
        self.packet_size = None  # cache for packet size by its header

    ############################################################

    def get_packets(self):
        """
        :return: list of fully received packets
        """
        packets = []
        while self.size:
            if self.packet_size is None:
                if self.size < SIZEOF_BIN_SIZE:
                    # wait for more data
                    break
                header = self.get(SIZEOF_BIN_SIZE, True)
                self.packet_size = bin_to_size(header)
                if self.packet_size < 0:
                    raise SnakeMQBrokenPacket("wrong packet header")
            else:
                if self.size < self.packet_size:
                    # wait for more data
                    break
                packets.append(self.get(self.packet_size, True))
                self.packet_size = None

        return packets

############################################################################
############################################################################

class ConnectionInfo(object):
    """
    Connection information and receive buffer handler.
    """
    def __init__(self):
        self.send_buffer = StreamBuffer()
        self.recv_buffer = ReceiveBuffer()
        self.send_in_progress = False
        self.queued_packet_ids = deque()  # pairs of (packet_length, packet_id)

############################################################################
############################################################################

class Packeter(object):
    def __init__(self, link):
        """
        :param link: :class:`~snakemq.link.Link`
        """
        self.link = link
        self.log = logging.getLogger("snakemq.packeter")

        #{ callbacks
        self.on_connect = Callback()  #: ``func(conn_id)``
        self.on_disconnect = Callback()  #: ``func(conn_id)``
        self.on_packet_recv = Callback()  #: ``func(conn_id, packet)``
        #: ``func(conn_id, packet_id)``, just a signal when a packet was fully sent
        self.on_packet_sent = Callback()
        self.on_error = Callback()  #: ``func(conn_id, exception)``
        #}

        self._connections = {}  # conn_id:ConnectionInfo
        self._last_packet_id = 0

        self.link.on_connect.add(self._on_connect)
        self.link.on_disconnect.add(self._on_disconnect)
        self.link.on_recv.add(self._on_recv)
        self.link.on_ready_to_send.add(self._on_ready_to_send)

    ###########################################################
    ###########################################################

    def send_packet(self, conn_id, buf):
        """
        Queue data to be sent over the link.

        :return: packet id
        """
        assert type(buf) == bytes
        try:
            conn = self._connections[conn_id]
        except KeyError:
            raise NoConnection

        self._last_packet_id += 1
        packet_id = self._last_packet_id

        buf = size_to_bin(len(buf)) + buf
        conn.send_buffer.put(buf)
        conn.queued_packet_ids.append((len(buf), packet_id))
        self._send_to_link(conn_id, conn)

        return packet_id

    ###########################################################
    ###########################################################

    def _on_connect(self, conn_id):
        self._connections[conn_id] = ConnectionInfo()
        self.on_connect(conn_id)

    ###########################################################

    def _on_disconnect(self, conn_id):
        # TODO signal unsent data and unreceived data
        del self._connections[conn_id]
        self.on_disconnect(conn_id)

    ###########################################################

    def _on_recv(self, conn_id, buf):
        recv_buffer = self._connections[conn_id].recv_buffer
        recv_buffer.put(buf)
        try:
            packets = recv_buffer.get_packets()
        except SnakeMQBrokenPacket as exc:
            self.log.error("conn=%s %r" % (conn_id, exc))
            self.on_error(conn_id, exc)
            self.link.close(conn_id)
            return

        for packet in packets:
            self.log.debug("recv packet %s len=%i" % (conn_id, len(packet)))
            self.on_packet_recv(conn_id, packet)

    ###########################################################

    def _on_ready_to_send(self, conn_id, sent_length):
        conn = self._connections[conn_id]
        conn.send_in_progress = False

        conn.send_buffer.cut(sent_length)
        while sent_length > 0:
            first, packet_id = conn.queued_packet_ids.popleft()
            if first <= sent_length:
                self.on_packet_sent(conn_id, packet_id)
            else:
                conn.queued_packet_ids.appendleft((first - sent_length,
                                                packet_id))
            sent_length -= first

        self._send_to_link(conn_id, conn)

    ###########################################################

    def _send_to_link(self, conn_id, conn):
        if conn.send_in_progress:
            return
        buf = conn.send_buffer.get(SEND_BLOCK_SIZE, False)
        if buf:
            self.link.send(conn_id, buf)
            conn.send_in_progress = True
