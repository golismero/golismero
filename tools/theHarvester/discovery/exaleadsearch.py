import string
import httplib, sys
import myparser
import re
import time
from search_results import *

class search_exalead:
	def __init__(self, word, options):
		self.word=word
		self.files="pdf"
		self.total_results=u""
		self.server="www.exalead.com"
		self.hostname="www.exalead.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/4.0"
		self.limit=options.limit
		self.counter=options.start
		self.quantity = 50
		
	def do_search(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/search/web/results/?q=%40"+ self.word + "&elements_per_page=50&start_index="+str(self.counter))
		h.putheader('Host', self.hostname)
		h.putheader('Referer', "http://"+self.hostname+"/search/web/results/?q=%40"+self.word)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def do_search_files(self,files):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "search/web/results/?q="+ self.word + "filetype:"+ self.files +"&elements_per_page="+str(self.quantity)+"&start_index="+self.counter)
		h.putheader('Host', self.hostname)
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()
		returncode, returnmsg, headers = h.getreply()
		self.results = h.getfile().read()
		self.total_results+= self.results

	def check_next(self):
		renext = re.compile('topNextUrl')
		nextres=renext.findall(self.results)

		return True if nextres !=[] else False

	def get_files(self):
		rawres=myparser.parser(self.total_results,self.word)
		return rawres.fileurls(self.files)

	def process(self):
		print "[-] Searching in Exalead:"
		while self.counter <= self.limit-self.quantity:
			self.do_search()
			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."

	def get_results(self):
		raw_results=myparser.parser(self.total_results,self.word)
		results = search_results()
		results.emails = raw_results.emails()
		results.hostnames = raw_results.hostnames()
		return results

	def process_files(self,files):
		while self.counter < self.limit:
			self.do_search_files(files)
			time.sleep(1)

			if self.check_next() == True:
				self.counter+=self.quantity
			else:
				break