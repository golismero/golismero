import string
import httplib, sys
import myparser
import re
from search_results import *

class search_jigsaw:
	def __init__(self,word,options):
		self.word=word.replace(' ', '%20')
		self.last_results=u""
		self.total_results=u""
		self.server="www.jigsaw.com"
		self.hostname="www.jigsaw.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.quantity=100
		self.limit=int(options.limit)
		self.counter=0
		
	def do_search(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/FreeTextSearch.xhtml?opCode=search&autoSuggested=True&freeText=" + self.word)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.last_results = unicode(h.getfile().read(), encoding)

		self.total_results+=self.last_results


	def check_next(self):
		renext = re.compile('>  Next  <')
		nextres=renext.findall(self.last_results)

		return True if nextres !=[] else False

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.people = raw_results.people_jigsaw()
		return results

	def process(self):

		print "[-] Searching Jigsaw:"

		while (self.counter < self.limit):
			self.do_search()

			if self.check_next() == True:
				self.counter+=self.quantity
				print "\r\tProcessed "+ str(self.counter) + " results..."
			else:
				break
