import string
import httplib, sys
import myparser
from search_results import *

class search_pgp:
	def __init__(self,word,options):
		self.word=word
		self.server="pgp.rediris.es:11371"
		self.hostname="pgp.rediris.es"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.total_results=""
		
	def process(self):
		print "[-] Searching PGP Key Server:"
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/pks/lookup?search=" + self.word + "&op=index")
		h.putheader('Host', self.hostname)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		# Even though pgp returns a content-type of UTF-8,
		# It's still really ISO-8859-1 - otherwise we
		# get 'invalid continuation byte'
		returncode, returnmsg, response_headers = h.getreply()
		response_body = h.getfile().read()
		self.total_results+=unicode(response_body, "ISO-8859-1")
		
	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.emails = raw_results.emails()
		results.hostnames = raw_results.hostnames()
		return results