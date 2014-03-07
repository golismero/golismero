import time
import httplib
import myparser
import sys
from search_results import *

class search_google_profiles:
	def __init__(self,word,options):
		self.word=word
		self.files="pdf"
		self.total_results=u""
		self.server="www.google.com"
		self.server_api="www.googleapis.com"
		self.hostname="www.google.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.quantity=100
		self.limit=options.limit
		self.counter=options.start
		self.api_key="AIzaSyBuBomy0n51Gb4836isK2Mp65UZI_DrrwQ"

	def do_search_profiles(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', '/search?num='+ str(self.quantity) + '&start=' + str(self.counter) + '&hl=en&meta=&q=site:www.google.com%20intitle:"Google%20Profile"%20"Companies%20I%27ve%20worked%20for"%20"at%20' + self.word + '"')
		h.putheader('Host', self.hostname)
		h.putheader('User-agent', self.userAgent)
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def process(self):
		print "[-] Searching Google Profiles:"
		while self.counter < self.limit:
			self.do_search_profiles()
			time.sleep(0.3)
			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.people = raw_results.profiles()
		return results
