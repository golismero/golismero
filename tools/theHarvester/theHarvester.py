#!/usr/bin/env python
# coding: utf-8

import string
import sys
from socket import *
from discovery import *
from harvesteroutput import HarvesterOutput
from lib import hostchecker
from collections import namedtuple

from argparse import ArgumentParser, RawTextHelpFormatter

ShodanItem = namedtuple("ShodanItem", "ip host banner port last_update")
OutputItem = namedtuple("OutputItem", "word emails search_hosts_ips people virtual_host_results dns_brute_results dns_reverse_results dns_tld_results shodan_results")

engine_list = {'google':googlesearch.search_google,
			  'bing':bingsearch.search_bing,
			  'bingapi':bingsearchapi.search_bing_api,
#				  'exalead':exaleadsearch.search_exalead, #To be implemented
#			  'yandex':yandexsearch.search_yandex, # To be fixed
			  'pgp':pgpsearch.search_pgp,
			  'people123':people123.search_123people,
			  'jigsaw':jigsaw.search_jigsaw,
			  'linkedin':linkedinsearch.search_linkedin,
			  'dogpile':dogpilesearch.search_dogpile,
			  'google-profiles':googleprofilesearch.search_google_profiles,
			  }

def perform_search (word, options):
	results = search_results.search_results()
	if options.engine !='all':
		search = engine_list[options.engine](word, options)
		search.process()
		results = search.get_results()
	else:
		print "Full Search:"
		# If we're doing a full search we also want to get all the virtual servers
		options.virtual = True

		for engine_name, engine_entry in engine_list.iteritems() :
			search = engine_entry(word, options)
			search.process()
			results.extend (search.get_results())

	return results

def validate_output(output):
	valid_output = HarvesterOutput().get_output_formats()

	if output is None:
		return None

	for param in output:
		try:
			if (False in (param[0] in valid_output, len(param[1]) >0)):
				return False
		except ValueError, e:
			return False

	return True

def ip_to_class_c_cidr(ip_string):
	range=ip_string.split(".")
	range[3]="0/24"
	range=string.join(range,'.')
	return range

def print_banner():
	print """\n
*******************************************************************
*                                                                 *
* | |_| |__   ___    /\  /\__ _ _ ____   _____  ___| |_ ___ _ __  *
* | __| '_ \ / _ \  / /_/ / _` | '__\ \ / / _ \/ __| __/ _ \ '__| *
* | |_| | | |  __/ / __  / (_| | |   \ V /  __/\__ \ ||  __/ |    *
*  \__|_| |_|\___| \/ /_/ \__,_|_|    \_/ \___||___/\__\___|_|    *
*                                                                 *
* TheHarvester Ver. 2.3                                           *
* Coded by Christian Martorella                                   *
* Edge-Security Research                                          *
* cmartorella@edge-security.com                                   *
* Some updates by Marcus Watson (@branmacmuffin)                  *
*******************************************************************\n\n"""

def start(argv):
	engine_string = ''
	for engine_name, engine_function in engine_list.iteritems() :
		engine_string += (engine_name+ ',')

	parser = ArgumentParser(epilog=
"""\nExamples:
		./theharvester.py -d microsoft.com -l 500 -b google
		./theharvester.py -d microsoft.com -b pgp
		./theharvester.py -d microsoft -l 200 -b linkedin -qvnct\n""", formatter_class=RawTextHelpFormatter)

	parser.add_argument("-d", "--domain", dest="word", help="Domain or company name to search for")
	parser.add_argument("-b", "--engine", dest="engine", help="Data source ("+engine_string+"all) (default google)",default="google")
	parser.add_argument("-s", "--start", dest="start", type=int, help="Start in result number X (default 0)", default=0)
	parser.add_argument("-v", "--virtual", dest="virtual", action="store_true", help="Verify host name via dns resolution and search for\nvirtual hosts")
	parser.add_argument("-n", "--dns-lookup", dest="dns_lookup", action="store_true", help="Perform a DNS reverse query on all ranges discovered")
	parser.add_argument("-c", "--dns-brute", dest="dns_brute", action="store_true", help="Perform a DNS brute force for the domain name (slow)")
	parser.add_argument("-t", "--dns-tld", dest="dns_tld", action="store_true", help="Perform a DNS TLD expansion discovery")
	parser.add_argument("-e", "--dns-server", dest="dns_server", help="Use this DNS server")
	parser.add_argument("-l", "--limit", dest="limit", type=int, default=100, help="Limit the number of results to work with\n(bing goes from 50 to 50 result")
	parser.add_argument("-q", "--shodan-lookup", dest="shodan_lookup", action="store_true", help="Use SHODAN database to query discovered hosts")
	parser.add_argument("-o", "--output", dest="output", action="append", nargs=2, metavar=('[X|H]', '<filename>'),
						help="-o H <html_filename>\tOutput to HTML file\n-o X <xml_filename>\tOutput to XML file")

	options = parser.parse_args()

	print_banner()

	if not options.word:
		parser.error ("Domain search is mandatory")
		sys.exit()

	if validate_output(options.output) == False:
		parser.error("Invalid output options")

	if options.engine != 'all' and options.engine not in engine_list:
		parser.error ("Invalid search engine, try with: " + engine_string + 'all')
		parser.print_help()
		sys.exit()

	search_results = perform_search(options.word, options)
	search_results.remove_duplicates()

	output_results = OutputItem
	output_results.word = options.word
	output_results.emails = search_results.emails
	output_results.people = search_results.people

	#Results############################################################
	print "\n[+] Emails found:"
	print "------------------"
	if not search_results.emails:
		print "No emails found"
	else:
		for emails in search_results.emails:
			print emails

	print "\n[+] People found:"
	print "------------------"
	if not search_results.people:
		print "No people found"
	else:
		for person in search_results.people:
			print person

	output_results.search_hosts_ips = {}
	print "\n[+] Hosts found in search engines:"
	print "------------------------------------"
	if not search_results.hostnames:
		print "No hosts found"
	else:
		host_to_ip=hostchecker.Checker()
		output_results.search_hosts_ips=host_to_ip.hosts_to_ips(search_results.hostnames)

		if len(output_results.search_hosts_ips) == 0:
			print "No hosts found"
		else:
			for host, ip in output_results.search_hosts_ips.iteritems() :
				print ip+"\t"+host

	unique_ips = []
	if len(output_results.search_hosts_ips)>0:
		unique_ips = list(set(output_results.search_hosts_ips.values()))

	# We leave all_hosts_ips and unique_ips alone as they represent
	# the results of the initial search. If we want to go deep we can
	# always revisit them later and start adding more.
	if True in (options.dns_lookup, options.dns_brute, options.dns_tld):
		print "\n[+] Starting active queries:"

	#DNS reverse lookup on a Class C########################################
	output_results.dns_reverse_results = {}
	if options.dns_lookup==True:
		analyzed_ranges=[]
		for ip in unique_ips:
			class_c_range = ip_to_class_c_cidr(ip)
			if range not in analyzed_ranges:
				print "\n[-]Performing reverse lookup on: " + class_c_range

				a=dnssearch.dns_reverse(class_c_range,True)
				a.list()

				output_results.dns_reverse_results=a.process()
				analyzed_ranges.append(class_c_range)
			else:
				continue

		print "\nHosts found after reverse lookup:"
		print "---------------------------------"
		if len(output_results.dns_reverse_results) == 0:
			print ("None")
		for host, ip in output_results.dns_reverse_results.iteritems() :
			print host

	#DNS Brute force####################################################
	output_results.dns_brute_results = {}
	if options.dns_brute==True:
		print "[-] Starting DNS brute force:"
		a=dnssearch.dns_force(options.word, options.dns_server, verbose=True)
		output_results.dns_brute_results=a.process()
		print "[+] Hosts found after DNS brute force:\n"
		if len(output_results.dns_brute_results) == 0:
			print ("None")
			#all_hosts_ips[host] = ip

	#DNS TLD expansion###################################################
	output_results.dns_tld_results = {}
	if options.dns_tld==True:
		print "\n[-] Starting DNS TLD expansion:\n"
		a=dnssearch.dns_tld(options.word,options.dns_server,verbose=True)
		output_results.dns_tld_results=a.process()
		print "[+] Hosts found after DNS TLD expansion:"
		print "=========================================="
		if len(output_results.dns_tld_results) == 0:
			print ("None")
		for host, ip in output_results.dns_tld_results.iteritems() :
			print host

	#Virtual hosts search###############################################
	output_results.virtual_host_results = {}
	if options.virtual == True:
		print "\n[+] Virtual hosts:"
		print "=================="
		for ip in unique_ips:
			search=bingsearch.search_bing(ip, options)
			search.process_vhost()

			hostnames_from_ip=search.get_allhostnames()
			for host in hostnames_from_ip:
				print ip+"\t"+host
				# Store the virtual hosts
				# Do we want to add these to the main hostlist? Maybe not
				output_results.virtual_host_results[host] = ip

	shodanvisited=[]

	output_results.shodan_results = []
	if options.shodan_lookup == True:
		print "[+] Shodan Database search:"
		for host, ip in output_results.search_hosts_ips.iteritems() :
			try:
				if not shodanvisited.count(ip):
					print "\tSearching for: " + ip+": "+host
					a=shodansearch.search_shodan(ip)
					shodanvisited.append(ip)
					results=a.run()
					for res in results:
						output_results.shodan_results.append(ShodanItem(ip=ip, host = host, banner = str(res['banner']),
														 last_update = str(res['last_update']),
														 port = str(res['port'])))
			except:
				pass
		print "[+] Shodan results:"
		print "==================="
		for shodan_result in output_results.shodan_results:
			print shodan_result.ip +"(" + shodan_result.port + "): " + \
				  shodan_result.host + " - updated " + shodan_result.last_update

	HarvesterOutput(output_results).process_output(options.output)

if __name__ == "__main__":
	try:
		start(sys.argv[1:])
	except KeyboardInterrupt:
		print "Search interrupted by user.."
	except Exception, e:
		print e
		sys.exit()
