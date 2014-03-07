import httplib, sys
import myparser
from search_results import *

class search_linkedin:
	def __init__(self,word,options):
		self.word=word.replace(' ', '%20')
		self.total_results=""
		self.server="www.google.com"
		self.hostname="www.google.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.quantity=100
		self.limit=int(options.limit)
		self.counter=0
		
	def do_search(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/search?num="+str(self.quantity)+"&start=" + str(self.counter) + "&hl=en&meta=&q=site%3Alinkedin.com%20" + self.word)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()
		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def process(self):
		print "[-] Searching LinkedIn:"

		while (self.counter < self.limit):
			self.do_search()
			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.people = raw_results.people_linkedin()
		return results