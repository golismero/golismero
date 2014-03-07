from lib import htmlExport
from lxml import etree

class HarvesterOutput:
	def __init__(self, output_results = None):
		self.output_results = output_results

		self.output_formats = {'H':self.__process_html,
							   'X':self.__process_xml}

	def get_output_formats (self):
		return self.output_formats.keys()

	def process_output (self, requested_formats):
		if requested_formats is None:
			return

		for format in requested_formats:
			self.output_formats[format[0]](format[1])

	def __process_html (self, filename):
		try:
			print "\nSaving HTML file: " + filename
			html = htmlExport.htmlExport(self.output_results.emails, self.output_results.search_hosts_ips,
										 self.output_results.people, self.output_results.virtual_host_results,
										 self.output_results.dns_brute_results, self.output_results.dns_reverse_results,
										 self.output_results.dns_tld_results, self.output_results.shodan_results,
										 filename, self.output_results.word)
			save = html.writehtml()
		except Exception,e:
			print e
			print "Error creating the HTML file"

	def __process_xml (self, filename):
		if filename is None:
			return

		print "\nSaving XML file: " + filename

		root = etree.Element(u"theHarvester")
		emails_elem = etree.SubElement(root, u"emails")
		for x in self.output_results.emails:
			email_elem = etree.SubElement(emails_elem, u"email")
			email_elem.text = x

		hosts_elem = etree.SubElement(root, u"hosts")
		for host, ip in self.output_results.search_hosts_ips.iteritems() :
			self.__add_host (hosts_elem, host, ip)

		people_elem = etree.SubElement(root, u"people")
		for x in self.output_results.people:
			person_elem = etree.SubElement(people_elem, u"person")
			person_elem.text = x

		vhosts_elem = etree.SubElement(root, u"vhosts")
		for host, ip in self.output_results.virtual_host_results.iteritems() :
			self.__add_host (vhosts_elem, host, ip)

		dns_brute_elem = etree.SubElement(root, u"dns_brute_hosts")
		for host, ip in self.output_results.dns_brute_results.iteritems() :
			self.__add_host (dns_brute_elem, host, ip)

		dns_tld_elem = etree.SubElement(root, u"dns_tld_hosts")
		for host, ip in self.output_results.dns_tld_results.iteritems() :
			self.__add_host (dns_tld_elem, host, ip)

		dns_reverse_elem = etree.SubElement(root, u"dns_reverse_hosts")
		for host, ip in self.output_results.dns_reverse_results.iteritems() :
			self.__add_host (dns_reverse_elem, host, ip)

		dns_shodan_elem = etree.SubElement(root, u"shodan")
		for shodan_result in self.output_results.shodan_results:
			host_elem = etree.SubElement(dns_shodan_elem, u"host")
			name_elem = etree.SubElement(host_elem, u"name")
			name_elem.text = shodan_result.host
			ip_elem = etree.SubElement(host_elem, u"ip")
			ip_elem.text = shodan_result.ip
			port_elem = etree.SubElement(host_elem, u"port")
			port_elem.text = shodan_result.port
			banner_elem = etree.SubElement(host_elem, u"banner")
			banner_elem.text = etree.CDATA(shodan_result.banner)
			last_update_elem = etree.SubElement(host_elem, u"last_update")
			last_update_elem.text = shodan_result.last_update

		with open(filename,'w') as file:
			try:
				file.write(etree.tostring(root, pretty_print=True))
			except Exception as e:
				print e
				print "Error creating the XML file"

	def __add_host (self, parent_element, host_name, ip):
		host_elem = etree.SubElement(parent_element, u"host")
		name_elem = etree.SubElement(host_elem, u"name")
		name_elem.text = host_name
		ip_elem = etree.SubElement(host_elem, u"ip")
		ip_elem.text = ip
