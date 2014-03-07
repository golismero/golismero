from lib import markup
from lib import graphs
import re

class htmlExport():
	def __init__(self, emails, hosts_ips, people, vhosts, dns_brute_results, dns_reverse_results, dns_tld_results, shodan_results, html_filename, word):
		self.emails=emails
		self.hosts_ips=hosts_ips
		self.people=people
		self.vhost=vhosts
		self.html_filename=html_filename
		self.dns_brute_results=dns_brute_results
		self.dns_reverse_results=dns_reverse_results
		self.dns_tld_results=dns_tld_results
		self.shodan_results=shodan_results
		self.word=word

		self.style=""
	
	def styler(self):
		a="""<style type='text/css'>body {
			 background: #e1e5e4  top no-repeat; 
		 }

		h1 { font-family: times, Times New Roman, times-roman, georgia, serif;
			color: #680000;
			margin: 0;
			padding: 0px 0px 6px 0px;
			font-size: 51px;
			line-height: 44px;
			letter-spacing: -2px;
			font-weight: bold;
		}

		h3 { font-family: times, Times New Roman, times-roman, georgia, serif;
			color: #444;
			margin: 0;
			padding: 0px 0px 6px 0px;
			font-size: 30px;
			line-height: 44px;
			letter-spacing: -2px;
			font-weight: bold;
		}

		li { font-family: times, Times New Roman, times-roman, georgia, serif;
			color: #444;
			margin: 0;
			padding: 0px 0px 6px 0px;
			font-size: 15px;
			line-height: 15px;
			letter-spacing: 0.4px;
		}

		.HarvesterTable{
			border-collapse: collapse;
			border-spacing: 0;
			margin:0px;padding:0px;
			border:1px solid #000000;
			box-shadow: 10px 10px 5px #888888;
			font-size: 15px
		}

		.HarvesterTable tr:first-child
		{
			background-color:#dddddd;
			border-width:0px 0px 1px 1px;
		}

		.HarvesterTable tr td
		{
			border-width:0px 0px 1px 1px;
			font-family: times,Times New Roman,times-roman,georgia,serif
		}

		.HarvesterTable td
		{
			padding-right:10px;
		}

		h2{
		font-family: times, Times New Roman, times-roman, georgia, serif;
				font-size: 48px;
				line-height: 40px;
				letter-spacing: -1px;
				color: #680000 ;
				margin: 0 0 0 0;
				padding: 0 0 0 0;
				font-weight: 100;

		}

		pre {
		overflow: auto;
		padding-left: 15px;
		padding-right: 15px;
		font-size: 11px;
		line-height: 15px;
		margin-top: 10px;
		width: 93%;
		display: block;
		background-color: #eeeeee;
		color: #000000;
		max-height: 300px;
		}
		</style>
		"""
		self.style=a
			
	def writehtml(self):
		page = markup.page()
		#page.init (title="theHarvester Results",css=('edge.css'),footer="Edge-security 2011")A
		page.html()
		self.styler()
		page.head(self.style)
		page.body()
		page.h1("theHarvester results")
		page.h2("for: " + self.word)
		page.h3("Dashboard:")

		graph = graphs.BarGraph('vBar')
		graph.values = [len(self.emails),
						len(self.hosts_ips),
						len(self.vhost),
						len(self.dns_tld_results),
						len(self.dns_brute_results),
						len(self.dns_reverse_results),
						len(self.shodan_results)]
		graph.labels = ['Emails','hosts','Vhost','TLD','Brute','Reverse','Shodan']
		graph.showValues = 1
		page.body(graph.create())

		page.h3("E-mails names found:")
		if self.emails!=[]:
			page.ul( class_="emaillist")
			page.li( self.emails, class_="emailitem")
			page.ul.close( )
		else:
			page.h2("No emails found")

		page.h3("Hosts found:")
		if self.hosts_ips!=[]:
			page.table(class_="HarvesterTable")
			page.addcontent("<tr><td>IP</td><td>Host</td></tr>")
			for host, ip in self.hosts_ips.iteritems() :
				page.addcontent("<tr><td>"+ip+"</td><td>"+host+"</td></tr>")
			page.table.close()

		else:
			page.h2("No hosts found")

		if len(self.people)>0:
			page.h3("People found:")
			page.ul( class_="peoplelist")
			page.li(self.people, class_="peopleitem")
			page.ul.close( )

		if len(self.dns_tld_results)>0:
			page.h3("TLD domains found in TLD expansion:")
			page.table(class_="HarvesterTable")
			page.addcontent("<tr><td>IP</td><td>Host</td></tr>")
			for host, ip in self.dns_tld_results.iteritems() :
				page.addcontent("<tr><td>"+ip+"</td><td>"+host+"</td></tr>")
			page.table.close()

		if len(self.dns_brute_results)>0:
			page.h3("Hosts found in DNS brute force:")
			page.table(class_="HarvesterTable")
			page.addcontent("<tr><td>IP</td><td>Host</td></tr>")
			for host, ip in self.dns_brute_results.iteritems() :
				page.addcontent("<tr><td>"+ip+"</td><td>"+host+"</td></tr>")
			page.table.close()

		if len(self.dns_reverse_results)>0:
			page.h3("Hosts found with reverse lookup :")
			page.table(class_="HarvesterTable")
			page.addcontent("<tr><td>IP</td><td>Host</td></tr>")
			for host, ip in self.dns_reverse_results.iteritems() :
				page.addcontent("<tr class='dnsrevitem'><td>"+ip+"</td><td>"+host+"</td></tr>")
			page.table.close()

		if len(self.vhost)>0:
			page.h3("Virtual hosts found:")
			page.ul( class_="pathslist")
			page.li(self.vhost, class_="pathitem")
			page.ul.close( )

		if len(self.shodan_results)>0:
			shodanalysis=[]
			page.h3("Shodan results:")
			for shodan_result in self.shodan_results:
				page.h3(shodan_result.ip+":"+shodan_result.host+' - Updated: '+shodan_result.last_update)
				page.a("Port :" + shodan_result.port)
				page.pre(shodan_result.banner)
				page.pre.close()
				banner=shodan_result.banner

				reg_server=re.compile('Server:.*')
				temp=reg_server.findall(banner)
				if temp != []:
					shodanalysis.append(shodan_result.ip+":"+shodan_result.host+" - "+temp[0])

			if shodanalysis != []:
				page.h3("Server technologies:")
				repeated=[]
				for x in shodanalysis:
					if x not in repeated:
						page.pre(x)
						page.pre.close()
						repeated.append(x)

		page.body.close()
		page.html.close()
		file = open(self.html_filename,'w')
		for x in page.content:
			try:
				file.write(x)
			except:
				print "Exception" +  x # send to logs
				pass
		file.close()
		return "ok"
