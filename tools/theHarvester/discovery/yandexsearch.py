import string
import httplib, sys
import myparser
import re
import time
from search_results import *

class search_yandex:
	def __init__(self,word,options):
		self.word=options.word
		self.total_results=u""
		self.server="yandex.com"
		self.hostname="yandex.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.limit=options.limit
		self.counter=options.start
		self.quantity=50
		
	def do_search(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/search?text=%40"+ self.word + "&numdoc="+str(self.quantity)+"&lr="+str(self.counter))
		h.putheader('Host', self.hostname)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def process(self):
		print "[-] Searching Yandex:"
		while self.counter <= self.limit:
			self.do_search()
			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.emails = raw_results.emails()
		results.hostnames = raw_results.hostnames()
		return results