# -*- coding: utf-8 -*-
"""
Data bandwidth throttle.

:author: David Siroky (siroky@dasir.cz)
:license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

import time

from snakemq.link import POLL_TIMEOUT
from snakemq.callbacks import Callback

############################################################################
############################################################################

TIME_QUANTUM = POLL_TIMEOUT * 2

############################################################################
############################################################################

class ConnectionInfo(object):
    def __init__(self, speed):
        self.speed = speed
        self.last_send_size = 0
        self.last_send_time = 0

    ##########################################################

    def can_send(self):
        """
        :return: bytes count that can be sent now
        """
        tdiff = time.time() - self.last_send_time
        if tdiff <= 0:
            return 0
        max_quantum = self.speed * TIME_QUANTUM
        max_send_size = max(0,
                            min(self.speed * tdiff - self.last_send_size,
                                max_quantum))
        return int(max_send_size)

    ##########################################################

    def cut(self, size):
        if size > 0:
            self.last_send_time = time.time()
            self.last_send_size = size

############################################################################
############################################################################

class Throttle(object):
    def __init__(self, link, speed):
        """
        :param link: :class:`~snakemq.link.Link`
        :param speed: maximum speed in bytes per second (for individual connection)
        """
        self.link = link
        # XXX BAD HACK - this naive implementation needs 2 rounds
        self.speed = speed * 2

        # pass on unused Link object callbacks
        self.on_connect = link.on_connect
        self.on_disconnect = link.on_disconnect
        self.on_recv = link.on_recv

        # bridge callbacks
        self.on_ready_to_send = Callback()
        self.on_loop_pass = Callback()

        # hooks for throttling
        self.link.on_connect.add(self._on_connect)
        self.link.on_disconnect.add(self._on_disconnect)
        self.link.on_ready_to_send.add(self._on_ready_to_send)
        self.link.on_loop_pass.add(self._on_loop_pass)

        #: data buffers {conn_id: ConnectionInfo}
        self.connections = {}
        #: set of connections waiting for throttle release
        self.stopped = set()

    ##########################################################

    def send(self, conn_id, buf):
        send_size = self.connections[conn_id].can_send()
        if send_size > 0:
            self.stopped.discard(conn_id)
            self.link.send(conn_id, buf[:send_size])
        else:
            self.stopped.add(conn_id)

    ##########################################################

    def _on_connect(self, conn_id):
        self.connections[conn_id] = ConnectionInfo(self.speed)

    ##########################################################

    def _on_disconnect(self, conn_id):
        del self.connections[conn_id]
        self.stopped.discard(conn_id)

    ##########################################################

    def _on_ready_to_send(self, conn_id, sent_length):
        connection = self.connections[conn_id]
        connection.cut(sent_length)
        send_size = connection.can_send()
        if send_size > 0:
            self.stopped.discard(conn_id)
            self.on_ready_to_send(conn_id, sent_length)
        else:
            self.stopped.add(conn_id)

    ##########################################################

    def _on_loop_pass(self):
        for conn_id in list(self.stopped):
            self._on_ready_to_send(conn_id, 0)
