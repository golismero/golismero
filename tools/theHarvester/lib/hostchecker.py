#!/usr/bin/env python
# encoding: utf-8
"""
Created by laramies on 2008-08-21.
"""

import sys
import socket

class Checker():
	def hosts_to_ips(self, hosts):
		hosts_ips = {}

		for host in hosts:
			try:
				ip=socket.gethostbyname(host)
				hosts_ips[host]=ip
			except Exception, e:
				pass
		return hosts_ips
		
