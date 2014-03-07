import httplib
import myparser
import time
from search_results import *
import sys

class search_dogpile:
	def __init__(self,word,options):
		self.word=word
		self.total_results=u""
		self.server="www.dogpile.com"
		self.hostname="www.dogpile.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.limit=options.limit
		self.counter=options.start
		self.quantity = 10

	def do_search(self):
		h = httplib.HTTP(self.server)

		#Dogpile is hardcoded to return 10 results
		h.putrequest('GET', "/search/web?qsi=" + str(self.counter) + "&q=\"%40" + self.word + "\"")
		h.putheader('Host', self.hostname)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def process(self):
		print "[-] Searching DogPile:"

		while self.counter < self.limit and self.counter <= 1000:
			self.do_search()
			time.sleep(1)

			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()

		results.emails = raw_results.emails()
		results.hostnames = raw_results.hostnames()
		return results