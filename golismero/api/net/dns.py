#!/usr/bin/python
# -*- coding: utf-8 -*-

# Required since "dns" is both an external module and the name of this file.
from __future__ import absolute_import

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

__all__ = ["DNS"]

from ..data.information.dns import *  # noqa
from ..data import LocalDataCache
from ...common import Singleton

import dns.query
import dns.resolver
import dns.reversename
import socket

from dns.zone import *
from netaddr import IPAddress
from netaddr.core import AddrFormatError


#------------------------------------------------------------------------------
class _DNS(Singleton):
    # Some code borrowed from the dnsrecon project:
    # https://github.com/darkoperator/dnsrecon

    REQUEST_TIMEOUT = 2.0 # In seconds

    # Public list of free DNS servers.
    #
    # This list was taken from:
    #
    # http://pcsupport.about.com/od/tipstricks/a/free-public-dns-servers.htm
    #
    PUBLIC_NAMESERVERS = [
        # Level 3 (http://www.level3.com/)
        "209.244.0.3",
        "209.244.0.4",

        # Google
        "8.8.8.8",
        "8.8.4.4",

        # Security (http://www.securly.com/)
        "184.169.143.224",
        "184.169.161.155",

        # Comodo Secure DNS (http://www.comodo.com/secure-dns/)
        "8.26.56.26",
        "8.20.247.20",

        # OpenDNS Home (http://www.opendns.com/)
        "208.67.222.222",
        "208.67.220.220",

        # DNS Advantage (http://www.neustar.biz/enterprise/dns-services/free-recursive-dns)
        "156.154.70.1",
        "156.154.71.1",

        # Norton ConnectSafe (https://dns.norton.com/dnsweb/faq.do)
        "198.153.192.40",
        "198.153.194.40",

        # SafeDNS (https://www.safedns.com/features/)
        "195.46.39.39",
        "195.46.39.40",

        # OpenNIC (http://www.opennicproject.org/)
        "74.207.247.4",
        "64.0.55.201",

        # Public -Root (http://public-root.com/root-server-check/index.htm)
        "199.5.157.131",
        "208.71.35.137",

        # SmartViper (http://www.markosweb.com/free-dns/)
        "208.76.50.50",
        "208.76.51.51",

        # Dyn (http://dyn.com/support/internet-guide-setup/)
        "216.146.35.35",
        "216.146.36.36",

        # Hurricane Electric (http://he.net/)
        "74.82.42.42",

        # puntCAT (http://www.servidordenoms.cat/)
        "109.69.8.51",
    ]


    #--------------------------------------------------------------------------
    def check_tcp_dns(self, address, dns_port=53):
        """
        Function to check if a server is listening at port 53 TCP. This
        will aid in IDS/IPS detection since a AXFR will not be tried if
        TCP port 53 is found to be closed.

        :param address: IP address or domain name.
        :type address: str

        :param dns_port: Port number to connect to the server.
        :type dns_port: int

        :return: True if server accepts TCP connections, False otherwise.
        :rtype: bool
        """
        if not isinstance(address, basestring):
            raise TypeError("Expected basestring, got '%s'" % type(address))

        if not isinstance(dns_port, int):
            raise TypeError("Expected int, got '%s'" % type(dns_port))
        if dns_port < 1:
            raise ValueError("Port number must be greater than 0.")

        s = socket.socket()
        s.settimeout(self.REQUEST_TIMEOUT)

        try:
            s.connect((address, dns_port))
        except Exception:
            return False
        else:
            return True
        finally:
            s.close()


    #--------------------------------------------------------------------------
    def resolve(self, target, type, nameservers=None):
        """
        Function for performing general resolution types.

        Special type of register is "ALL", that returns all of the registers
        returned by the query.

        :param target: Name to resolve.
        :type target: str

        :param type: Type of query: ALL, A, AAAA, NS, PTR...
        :type type: int | str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: DNS registers.
        :rtype: list(DnsRegister)
        """
        return self._make_request(type, target, nameservers)


    #--------------------------------------------------------------------------
    def get_a(self, host, nameservers=None, also_CNAME=False):
        """
        Resolve the A records for a given host.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :param also_CNAME: Set this var to True if you want to return also the CNAME Registers returned by the query.
        :tyep algo_CNAME: bool

        :return: Type A registers.
        :rtype: list(DnsRegisterA)
        """

        # Special case for localhost
        if host.lower() == "localhost":
            return [DnsRegisterA("127.0.0.1")]

        r = self._make_request("A", host, nameservers, auto_resolve=not also_CNAME)

        # Get all the register: CNAME and A
        if also_CNAME:
            m_return         = []
            if not isinstance(r, list):
                m_return.extend(self._dnslib2register("ALL", r))
            else:
                m_return_extend = m_return.extend
                for lr in r:
                    m_return_extend(self._dnslib2register("ALL", lr))

            return m_return
        else:
            return r


    #--------------------------------------------------------------------------
    def get_aaaa(self, host, nameservers=None, also_CNAME=False):
        """
        Resolve the A Record for a given host.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :param also_CNAME: Set this var to True if you want to return also the CNAME Registers returned by the query.
        :tyep algo_CNAME: bool

        :return: AAAA registers.
        :rtype: list(DnsRegisterAAAA)
        """

        # Special case for localhost
        if host.lower() == "localhost":
            return [DnsRegisterAAAA("::1")]

        r = self._make_request("AAAA", host, nameservers, auto_resolve=not also_CNAME)

        if also_CNAME:
            # Get all the register: CNAME and A
            m_return         = []
            if not isinstance(r, list):
                m_return.extend(self._dnslib2register("ALL", r))
            else:
                m_return_extend = m_return.extend
                for lr in r:
                    m_return_extend(self._dnslib2register("ALL", lr))


            return m_return
        else:
            return r


    #--------------------------------------------------------------------------
    def get_mx(self, host, nameservers=None):
        """
        Resolve the MX records for a given host.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: MX registers.
        :rtype: list(DnsRegisterMX)
        """
        return self._make_request("MX", host, nameservers)


    #--------------------------------------------------------------------------
    def get_ns(self, host, nameservers=None):
        """
        Returns all NS records. Also returns the IP
        address of the host both in IPv4 and IPv6.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: NS registers.
        :rtype: list(DnsRegisterNS)
        """
        return self._make_request("NS", host, nameservers)


    #--------------------------------------------------------------------------
    def get_soa(self, host, nameservers=None):
        """
        Returns all SOA records. Also returns the IP
        address of the host both in IPv4 and IPv6.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: SOA registers.
        :rtype: list(DnsRegisterSOA)
        """
        return self._make_request("SOA", host, nameservers)


    #--------------------------------------------------------------------------
    def get_spf(self, host, nameservers=None):
        """
        Resolve SPF records.

        :param host: the target to make the request.
        :type host: str

        :param nameservers: nameserver to use.
        :type nameservers: list(str)

        :return: SPF registers.
        :rtype: list(DnsRegisterSPF)
        """
        return self._make_request("SPF", host, nameservers)


    #--------------------------------------------------------------------------
    def get_txt(self, host, nameservers=None):
        """
        Resolve TXT records.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: TXT registers.
        :rtype: list(DnsRegisterTXT)
        """
        return self._make_request("TXT", host, nameservers)


    #--------------------------------------------------------------------------
    def get_ptr(self, ipaddress, nameservers=None):
        """
        Resolve PTR records given it's IPv4 or IPv6 address.

        :param ipaddress: Target IP address.
        :type ipaddress: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: PTR registers.
        :rtype: list(DnsRegisterPTR)
        """
        if not isinstance(ipaddress, basestring):
            raise TypeError("Expected basestring, got '%s'" % type(ipaddress))

        # Detect the IP address version
        m_ipobj = None
        try:
            m_ipobj = IPAddress(ipaddress)
        except AddrFormatError:
            raise ValueError("Wrong IP address")

        # Make the query
        m_ip = str(dns.reversename.from_address(ipaddress))

        # Get the IPs
        if m_ip:
            if m_ipobj.version == "4":
                m_name = m_ip.replace(".in-addr.arpa.", "")
            else:
                m_name = m_ip.replace("ip6.arpa.", "")

            return self._make_request("PTR", m_name, nameservers)
        else:
            return []


    #--------------------------------------------------------------------------
    def get_srv(self, host, nameservers=None):
        """
        Function for resolving SRV Records.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: SRV registers.
        :rtype: list(DnsRegisterSRV)
        """
        return self._make_request("SRV", host, nameservers)


    #--------------------------------------------------------------------------
    def get_nsec(self, host, nameservers=None):
        """
        Function for querying for a NSEC record and retriving the rdata object.
        This function is used mostly for performing a Zone Walk against a zone.

        :param host: Target hostname.
        :type host: str

        :param nameservers: Nameservers to use.
        :type nameservers: list(str)

        :return: NSEC registers.
        :rtype: list(DnsRegisterNSEC)
        """
        return self._make_request("NSEC", host, nameservers)


    #--------------------------------------------------------------------------
    def zone_transfer(self, domain, nameservers = None, ns_allowed_zone_transfer=False):
        """
        Function for testing for zone transfers on a given Domain.

        :param domain: Target hostname.
        :type domain: str

        :param nameservers: Alternate nameservers.
        :type nameservers: list(str)

        :param ns_allowed_zone_transfer: is set to True, this funcion will return the list of
                                         nameservers with zone transfer enabled.
        :type ns_allowed_zone_transfer: bool

        :return: If successful, a list of DnsRegister objects.
                 Otherwise, an empty list. If ns_allowed_zone_transfer is enabled, it will
                 return a tuple as format: (set(servers with zone transfer enabled), list(DnsRegister))
        :rtype: list(DnsRegister) | (set(str), list(DnsRegister))
        """
        if not isinstance(domain, basestring):
            raise TypeError("Expected basestring, got '%s'" % type(domain))
        if nameservers:
            if isinstance(nameservers, list):
                for n in nameservers:
                    if not isinstance(n, basestring):
                        raise TypeError("Expected basestring, got '%s'" % type(n))
            else:
                raise TypeError("Expected list, got '%s'" % type(nameservers))

        # Results of zone transfer
        zone_records        = []
        zone_records_append = zone_records.append

        ns_zone_enabled     = set()

        # Availabe DNS servers
        ns_records   = None

        # If nameservers specified -> use it
        if nameservers:
            ns_records = set(nameservers)

        else: # Looking for nameservers for the domain

            #Find NS for domains
            ns_tmp     = self.get_ns(domain)
            #
            # Check the input domain
            #
            # If name server of the domain is NOT empty -> the domain is NOT a nameserver
            if ns_tmp:
                # Mark for not tracking
                map(LocalDataCache.on_autogeneration, ns_tmp)

                # Store only the IP address of the DNS servers
                l_dns        = set()
                l_dns_append = l_dns.add
                for d in ns_tmp:
                    for t in self.get_ips(d):
                        l_dns_append(t.address)

                        # Mark for not tracking
                        LocalDataCache.on_autogeneration(t)

                # Find SOA for Domain
                for d in self.get_soa(domain):
                    for t in self.get_ips(d):
                        l_dns_append(t.address)

                        # Mark for not tracking
                        LocalDataCache.on_autogeneration(t)
                    # Mark for not tracking
                    LocalDataCache.on_autogeneration(d)

                ns_records = l_dns

            else:
                # The domain is an DNS server
                ns_records = set((domain,))

        #
        # Make the transfer for each NS Server
        #
        for ns_srv in ns_records:
            if self.check_tcp_dns(ns_srv):
                try:
                    zone = self._from_wire(dns.query.xfr(where=ns_srv, zone=domain, timeout=10))

                    # Store the ns used to the zone transfer
                    if ns_allowed_zone_transfer:
                        ns_zone_enabled.add(ns_srv)


                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.SOA):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("SOA",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NS):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NS",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.TXT):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("TXT",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.SPF):
                        zone_records_append(self._dnslib2register("SPF",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.PTR):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("PTR",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.MX):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("MX",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.AAAA):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("AAAA",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.A):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("A",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.CNAME):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("CNAME",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.SRV):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("SRV",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.HINFO):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("HINFO",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.WKS):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("WKS",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.RP):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("RP",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.AFSDB):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("AFSDB",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.LOC):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("LOC",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.X25):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("X25",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.ISDN):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("ISDN",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.RT):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("X25",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NSAP):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NSAP",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NAPTR):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NAPTR",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.CERT):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("CERT",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.SIG):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("SIG",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.RRSIG):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("RRSIG",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.DNSKEY):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("DNSKEY",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.DS):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("DS",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NSEC):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NSEC",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NSEC3):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NSEC3",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.NSEC3PARAM):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("NSEC3PARAM",rdata))

                    for (name, rdataset) in zone.iterate_rdatasets(dns.rdatatype.IPSECKEY):
                        for rdata in rdataset:
                            zone_records_append(self._dnslib2register("IPSECKEY",rdata))

                except:
                    pass

        if ns_allowed_zone_transfer:
            return (ns_zone_enabled, zone_records)
        else:
            return zone_records


    #--------------------------------------------------------------------------
    #
    # Helpers
    #
    #--------------------------------------------------------------------------
    #
    # This method has been taken directly (with some changes) from dns recon project
    #
    def _from_wire(self, xfr, zone_factory=Zone, relativize=True):
        """
        Method for turning returned data from a DNS AXFR to RRSET.

        This method will not perform a check origin on the zone data
        as the method included with dnspython.
        """
        z = None

        for r in xfr:
            if z is None:
                if relativize:
                    origin = r.origin
                else:
                    origin = r.answer[0].name
                rdclass = r.answer[0].rdclass
                z = zone_factory(origin, rdclass, relativize=relativize)
            for rrset in r.answer:
                znode = z.nodes.get(rrset.name)
                if not znode:
                    znode = z.node_factory()
                    z.nodes[rrset.name] = znode
                zrds = znode.find_rdataset(rrset.rdclass, rrset.rdtype,
                                           rrset.covers, True)
                zrds.update_ttl(rrset.ttl)
                for rd in rrset:
                    rd.choose_relativity(z.origin, relativize)
                    zrds.add(rd)

        return z


    #--------------------------------------------------------------------------
    def get_ips(self, register):
        """
        Get the list of IPs associated the register as parameter.

        If you pass CNAME register, you get an A/AAAA register:
            >> cname = DnsRegisterCNAME("myalias.mysite.com")
            >> a = Dns.get_ips(cname)
            >> print a
            [<DnsRegisterA object at 0x103ad9a50>]
            >> print a[0]
            <DnsRegisterA object at 0x103ad9a50>
            >> print a[0].target
            127.0.0.1

        :param register: A DNS Register.
            Valid registers are: DnsRegisterA, DnsRegisterAAAA,
            DnsRegisterCNAME DnsRegisterISDN, DnsRegisterNS,
            DnsRegisterNSAP, DnsRegisterPTR, DnsRegisterSOA,
            DnsRegisterSRV, DnsRegisterWKS, DnsRegisterX25
        :type register: DnsRegister

        :return: A list with the A and AAAA registers.
        :rtype : list(DnsRegisterA|DnsRegisterAAAA)
        """
        if not isinstance(register, DnsRegister):
            raise TypeError("Expected DnsRegister, got '%s'" % type(register))

        PROP = self.PROPERTIES_WITH_IP_ADDRESSES

        if register.type not in PROP:
            return []

        if register.type in ("A", "AAAA"):
            return [register]

        m_return = []

        target = getattr(register, PROP[register.type])

        # IPv4 address
        m_return.extend(self.get_a(target))

        # IPv6 address
        m_return.extend(self.get_aaaa(target))

        return m_return

    PROPERTIES_WITH_IP_ADDRESSES = {
        "A":"target",
        "AAAA":"target",
        "CNAME":"target",
        "ISDN":"address",
        "NS":"target",
        "NSAP":"address",
        "PTR":"target",
        "SOA":"mname",
        "SRV":"target",
        "WKS":"address",
        "X25":"address"
    }


    #--------------------------------------------------------------------------
    def _dnslib2register(self, type, answer_in):
        """
        Creates a DnsRegister from a dnslib register.

        Special type of register "ALL" that converts all the types of the
        registers.

        :param type: Type of response to get: A, AAAA, CNAME...
        :type type: str

        :param answer_in: Object with the answer from dnslib.
        :type answer_in: dns.resolver.Answer

        :return: DNS register.
        :rtype: list(DnsRegister)
        """

        m_return        = []
        m_return_append = m_return.append

        if isinstance(answer_in, dns.resolver.Answer):

            for ardata in answer_in.response.answer:
                for rdata in ardata:

                    register_type = DnsRegister.id2name(rdata.rdtype)

                    # If register it different that we are looking for, skip it.
                    if type != register_type and type != "ALL":
                        continue


                    m_return_append(self.__dnsregister2golismeroregister(register_type, rdata))
        else:
            register_type = DnsRegister.id2name(answer_in.rdtype)
            m_return_append(self.__dnsregister2golismeroregister(register_type, answer_in))

        return m_return


    #--------------------------------------------------------------------------
    def __dnsregister2golismeroregister(self, register_type, answer):
        """
        Transform a dnslib register into a DnsRegister.

        :param register_type: Type of register.
        :type register_type: str

        :param answer: dnslib object with a DNS register data.
        :type answer: object

        :return: DNS register.
        :rtype: DnsRegister
        """
        m_return = None

        if register_type == "A":
            m_return = DnsRegisterA(answer.address)

        elif register_type == "AAAA":
            m_return = DnsRegisterAAAA(answer.address)

        elif register_type == "AFSDB":
            m_return = DnsRegisterAFSDB(answer.subtype, answer.hostname.to_text()[:-1])

        elif register_type == "CERT":
            m_return = DnsRegisterCERT(answer.algorithm,
                                       answer.certificate,
                                       answer.certificate_type,
                                       answer.key_tag)

        elif register_type == "CNAME":
            m_return = DnsRegisterCNAME(answer.target.to_text()[:-1])

        elif register_type == "DNSKEY":
            m_return = DnsRegisterDNSKEY(answer.algorithm,
                                         answer.flags,
                                         dns.rdata._hexify(answer.key),
                                         answer.protocol)

        elif register_type == "DS":
            m_return = DnsRegisterDS(answer.algorithm,
                                     dns.rdata._hexify(answer.digest),
                                     answer.digest_type,
                                     answer.key_tag)

        elif register_type == "HINFO":
            m_return = DnsRegisterHINFO(answer.cpu,
                                        answer.os)

        elif register_type == "IPSECKEY":
            m_return = DnsRegisterIPSECKEY(answer.algorithm,
                                           answer.gateway,
                                           answer.gateway_type,
                                           answer.key,
                                           answer.precedence)

        elif register_type == "ISDN":
            m_return = DnsRegisterISDN(answer.address,
                                       answer.subaddress)

        elif register_type == "LOC":
            m_return = DnsRegisterLOC(answer.latitude,
                                      answer.longitude,
                                      answer.altitude,
                                      answer.to_text())

        elif register_type == "MX":
            m_return = DnsRegisterMX(answer.exchange.to_text()[:-1],
                                     answer.preference)

        elif register_type == "NAPTR":
            m_return = DnsRegisterNAPTR(answer.order,
                                        answer.preference,
                                        answer.regexp,
                                        answer.replacement.to_text()[:-1],
                                        answer.service)

        elif register_type == "NS":
            m_return = DnsRegisterNS(answer.target.to_text()[:-1])

        elif register_type == "NSAP":
            m_return = DnsRegisterNSAP(answer.address)

        elif register_type == "NSEC":
            m_return = DnsRegisterNSEC(answer.next.to_text()[:-1])

        elif register_type == "NSEC3":
            m_return = DnsRegisterNSEC3(answer.algorithm,
                                        answer.flags,
                                        answer.iterations,
                                        dns.rdata._hexify(answer.salt))

        elif register_type == "NSEC3PARAM":
            m_return = DnsRegisterNSEC3PARAM(answer.algorithm,
                                             answer.flags,
                                             answer.iterations,
                                             dns.rdata._hexify(answer.salt))

        elif register_type == "PTR":
            m_return = DnsRegisterPTR(answer.target.to_text()[:-1])

        elif register_type == "RP":
            m_return = DnsRegisterRP(answer.mbox.to_text()[:-1],
                                     answer.txt.to_text()[:-1])

        elif register_type == "RPSIG":
            m_return = DnsRegisterRRSIG(answer.algorithm,
                                        answer.expiration,
                                        answer.interception,
                                        answer.key_tag,
                                        answer.labels,
                                        answer.original_ttl,
                                        answer.signer,
                                        answer.type_coverded)

        elif register_type == "SIG":
            m_return = DnsRegisterSIG(answer.algorithm,
                                      answer.expiration,
                                      answer.interception,
                                      answer.key_tag,
                                      answer.labels,
                                      answer.original_ttl,
                                      answer.signer,
                                      answer.type_coverded)

        elif register_type == "SOA":
            m_return = DnsRegisterSOA(answer.mname.to_text()[:-1],
                                      answer.rname.to_text()[:-1],
                                      answer.refresh,
                                      answer.expire)

        elif register_type == "SPF":
            m_return = DnsRegisterSPF(answer.strings)

        elif register_type == "SRV":
            m_return = DnsRegisterSRV(answer.target.to_text()[:-1],
                                      answer.priority,
                                      answer.weight,
                                      answer.port)

        elif register_type == "TXT":
            m_return = DnsRegisterTXT(answer.strings)

        elif register_type == "WKS":
            m_return = DnsRegisterWKS(answer.address,
                                      answer.protocol,
                                      answer.bitmap)

        elif register_type == "X25":
            m_return = DnsRegisterX25(answer.address)

        else:
            raise ValueError("DNS register type '%s' is incorrect." % register_type)

        return m_return


    #--------------------------------------------------------------------------
    def _make_request(self, register_type, host, nameservers=None, auto_resolve=True):
        """
        Make a request using dnslib, and return a DNS register.

        :param: register_type: Type of query: A, AAAA, CNAME...
        :type register_type: str

        :param host: Target host for the request.
        :type host: str

        :param nameservers: Custom name servers.
        :type nameservers: list(str)

        :param auto_resolve: configure this function to transform de dnslib register to the golismero register.
        :type auto_resolve: bool

        :return: a list with the DnsRegisters. Returned list can be empty, if a error has occurred.
        :type: list(DnsRegister)
        """
        if not isinstance(register_type, basestring):
            raise TypeError("Expected str, got '%s'" % type(type))
        if not isinstance(host, basestring):
            raise TypeError("Expected basestring, got '%s'" % type(host))
        if nameservers:
            if isinstance(nameservers, list):
                for n in nameservers:
                    if not isinstance(n, basestring):
                        raise TypeError("Expected basestring, got '%s'" % type(n))
            else:
                raise TypeError("Expected list, got '%s'" % type(nameservers))

        m_query_obj = None

        if nameservers:
            m_query_obj             = dns.resolver.Resolver(configure=False)
            m_query_obj.nameservers = nameservers
        else:
            m_query_obj             = dns.resolver.Resolver(configure=True)

            # Append the free public DNS servers for avoid errors when the DNS servers
            # configured in /etc/resolv.conf fails.
            m_query_obj.nameservers.extend(self.PUBLIC_NAMESERVERS)

        # Set timeouts
        m_query_obj.timeout         = self.REQUEST_TIMEOUT
        m_query_obj.lifetime        = self.REQUEST_TIMEOUT

        try:
            answer = m_query_obj.query(host, register_type)
        except Exception:
            return []

        if auto_resolve:
            return self._dnslib2register(register_type, answer)
        else:
            return answer

# Instance the singleton.
DNS = _DNS()
