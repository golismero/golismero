import IPy
import DNS
import string
import socket
import sys
import re

class dns_reverse():
	def __init__(self,range,verbose=True):
		self.range= range
		self.iplist=''
		self.verbose=verbose
		try:
			DNS.ParseResolvConf("/etc/resolv.conf")
			nameserver=DNS.defaults['server'][0]
		except:
			print "Error in DNS resolvers"
			sys.exit()

	def run(self,host):
		a=string.split(host, '.')
		a.reverse()
		b=string.join(a,'.')+'.in-addr.arpa'
		nameserver=DNS.defaults['server'][0]
		if self.verbose:
			ESC=chr(27)
			sys.stdout.write(ESC + '[2K' + ESC+'[G')
			sys.stdout.write("\r\t" + host)
			sys.stdout.flush()
		try:
			name=DNS.Base.DnsRequest(b,qtype='ptr').req().answers[0]['data']
			return name
		except:
			pass

	def get_ip_list(self,ips):
		"""Generates the list of ips to reverse"""
		try:
			list=IPy.IP(ips)
		except:
			print "Error in IP format, check the input and try again. (Eg. 192.168.1.0/24)"
			sys.exit()
		name=[]
		for x in list:
			name.append(str(x))
		return name 
	
	def list(self):
		self.iplist=self.get_ip_list(self.range)
		return self.iplist

	def process(self):
		results = {}
		for ip in self.iplist:
			found_host=self.run(ip)
			if found_host!=None:
				results[found_host]=ip
		return results
	
class dns_force():
	def __init__(self,domain,dnsserver,verbose=False):
		self.domain=domain
		self.nameserver = dnsserver
		self.file="dns-names.txt"
		self.subdo = False 
		self.verbose = verbose
		try:
			self.subdomains = [line.rstrip() for line in open(self.file,"r")]
		except:
			print "Error opening dns dictionary file"
			sys.exit()

	def getdns(self,domain):
		DNS.ParseResolvConf("/etc/resolv.conf")
		nameserver=DNS.defaults['server'][0]
		dom=domain
		if self.subdo == True:
			dom=domain.split(".")
			dom.pop(0)
			rootdom=".".join(dom)
		else:
			rootdom=dom
		if self.nameserver is None:
			r=DNS.Request(rootdom,qtype='SOA').req()
			primary,email,serial,refresh,retry,expire,minimum = r.answers[0]['data']
			test=DNS.Request(rootdom,qtype='NS',server=primary,aa=1).req()
			if test.header['status'] != "NOERROR":
				print "Error"
				sys.exit()
			self.nameserver= test.answers[0]['data']
		elif self.nameserver == "local":
			self.nameserver=nameserver
		return self.nameserver

	def is_valid_ip (self, address):
		try:
			socket.inet_aton(address)
			ip = True
		except socket.error:
			ip = False
		return ip

	def run(self, subdomain):
		if self.nameserver is None:
			self.nameserver = self.getdns(self.domain)	
		host=subdomain+"."+str(self.domain)
		if self.verbose:
			ESC=chr(27)
			sys.stdout.write(ESC + '[2K' + ESC+'[G')
			sys.stdout.write("\r\t" + host)
			sys.stdout.flush()
		try:
			request=DNS.Request(host, qtype='a', server=self.nameserver).req()
			ip=request.answers[0]['data']

			return {host:ip if self.is_valid_ip(ip) else ''}
		except Exception,e:
			pass

	def process(self):
		results = {}

		for subdomain in self.subdomains:
			found_host_ip=self.run(subdomain)
			if found_host_ip!=None:
				results.update (found_host_ip)
		return results

class dns_tld():
	def __init__(self, domain, dnsserver, verbose=False):
		self.domain=domain
		self.nameserver = dnsserver
		self.subdo = False 
		self.verbose = verbose

		self.file="effective_tld_names.dat"
		# Read latesst poublic suffixes - retrieved from:
		# http://mxr.mozilla.org/mozilla-central/source/netwerk/dns/effective_tld_names.dat?raw=1
		try:
			self.tlds = self.extract_tlds_from_file(self.file)
		except Exception,e:
			print "Error opening Public Suffix file " + self.file
			sys.exit()

	def extract_tlds_from_file(self, tld_file):
		with open(tld_file) as f:
			return { line.strip() for line in f if len(line)>1 and line[0] is not '/'}

	def getdns(self,domain):
		DNS.ParseResolvConf("/etc/resolv.conf")
		nameserver=DNS.defaults['server'][0]
		dom=domain
		if self.subdo == True:
			dom=domain.split(".")
			dom.pop(0)
			rootdom=".".join(dom)
		else:
			rootdom=dom
		if self.nameserver is None:
			r=DNS.Request(rootdom,qtype='SOA').req()
			primary,email,serial,refresh,retry,expire,minimum = r.answers[0]['data']
			test=DNS.Request(rootdom,qtype='NS',server=primary,aa=1).req()
			if test.header['status'] != "NOERROR":
				print "Error"
				sys.exit()
			self.nameserver= test.answers[0]['data']
		elif self.nameserver == "local":
			self.nameserver=nameserver
		return self.nameserver

	def is_valid_ip (self, address):
		try:
			socket.inet_aton(address)
			ip = True
		except socket.error:
			ip = False
		return ip

	def run(self,tld):
		self.nameserver = self.getdns(self.domain)	
		host=self.domain.split(".")[0]+"."+tld
		if self.verbose:
			ESC=chr(27)
			sys.stdout.write(ESC + '[2K' + ESC+'[G')
			sys.stdout.write("\r\tSearching for: " + host)
			sys.stdout.flush()
		try:
			request=DNS.Request(host,qtype='a',server=self.nameserver).req()
			ip = request.answers[0]['data']

			return {host:ip if self.is_valid_ip(ip) else ''}
		except Exception,e:
			pass

	def process(self):
		results={}
		for x in self.tlds:
			found_host_ip=self.run(x)
			if found_host_ip!=None:
				results.update (found_host_ip)
		return results