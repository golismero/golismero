from bingsearch import *

class search_bing_api(search_bing):
	def __init__(self,word,options):
		self.apiserver="api.search.live.net"
		self.bing_api_key = ""

		search_bing.__init__(self, word, options)

	def do_search(self):
		h = httplib.HTTP(self.apiserver)
		h.putrequest('GET', "/xml.aspx?Appid="+ self.bing_api_key + "&query=%40" + self.word +"&sources=web&web.count=40&web.offset="+str(self.counter))
		h.putheader('Host', "api.search.live.net")
		h.putheader('User-agent', self.userAgent)	
		h.endheaders()

		returncode, returnmsg, response_headers = h.getreply()
		encoding=response_headers['content-type'].split('charset=')[-1]
		self.total_results+=unicode(h.getfile().read(), encoding)
	
	def process(self):
		print "[-] Searching Bing using API Key:"

		if self.bing_api_key=="":
			print "Cannot perform a Bing API Search without a Key in discovery/bingsearch.py"
			return

		while (self.counter < self.limit):
			self.do_search()
			time.sleep(0.3)

			self.counter+=self.quantity
			print "\r\tProcessed "+ str(self.counter) + " results..."