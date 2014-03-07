import httplib, sys
import myparser
import time
from search_results import *

class search_bing:
	def __init__(self,word,options):
		self.word=word.replace(' ', '%20')
		self.total_results=u""
		self.server="www.bing.com"
		self.hostname="www.bing.com"
		self.userAgent="(Mozilla/5.0 (Windows; U; Windows NT 6.0;en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6"
		self.quantity=50 # the number to retrieve at once
		self.limit=int(options.limit)
		self.counter=options.start


	def do_search(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/search?q=%40" + self.word + "&count=50&first="+ str(self.counter))
		h.putheader('Host', self.hostname)
		h.putheader('Cookie: SRCHHPGUSR=ADLT=DEMOTE&NRSLT=50')
		h.putheader('Accept-Language: en-us,en')
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()
		returncode, returnmsg, response_headers = h.getreply()

		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)

	def do_search_vhost(self):
		h = httplib.HTTP(self.server)
		h.putrequest('GET', "/search?q=ip:" + self.word + "&go=&count="+str(self.quantity)+"&FORM=QBHL&qs=n&first="+ str(self.counter))
		h.putheader('Host', self.hostname)
		h.putheader('Cookie: mkt=en-US;ui=en-US;SRCHHPGUSR=NEWWND=0&ADLT=DEMOTE&NRSLT=50')
		h.putheader('Accept-Language: en-us,en')
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)
				
	def get_allhostnames(self):
		rawres=myparser.parser(self.total_results,self.word)
		return rawres.hostnames_all()

	def process(self):
		print "[-] Searching Bing:"

		while (self.counter < self.limit):
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

	def process_vhost(self):
		while (self.counter < self.limit):#Maybe it is good to use other limit for this.
			self.do_search_vhost()
			self.counter+=50
