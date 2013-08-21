import IPy
import DNS
import string
import socket
import sys

class dns_reverse():
    def __init__(self,range,verbose=True):
        self.range= range
        self.iplist=''
        self.results=[]
        self.verbose=verbose
        try:
            DNS.ParseResolvConf("/etc/resolv.conf")
            nameserver=DNS.defaults['server'][0]
        except:
            print "Error in DNS resolvers"
            sys.exit()

    def run(self,host):
        a=string.split(host, '.')
        a.reverse()
        b=string.join(a,'.')+'.in-addr.arpa'
        nameserver=DNS.defaults['server'][0]
        if self.verbose:
            ESC=chr(27)
            sys.stdout.write(ESC + '[2K' + ESC+'[G')
            sys.stdout.write("\r\t" + host)
            sys.stdout.flush()
        try:
            name=DNS.Base.DnsRequest(b,qtype='ptr').req().answers[0]['data']
            return host+":"+name
        except:
            pass

    def get_ip_list(self,ips):
        """Generates the list of ips to reverse"""
        try:
            list=IPy.IP(ips)
        except:
            print "Error in IP format, check the input and try again. (Eg. 192.168.1.0/24)"
            sys.exit()
        name=[]
        for x in list:
            name.append(str(x))
        return name

    def list(self):
        self.iplist=self.get_ip_list(self.range)
        return self.iplist

    def process(self):
        for x in self.iplist:
            host=self.run(x)
            if host!=None:
                self.results.append(host)
        return self.results


class dns_force():
    def __init__(self,domain,dnsserver,verbose=False):
        self.domain=domain
        self.nameserver = dnsserver
        self.file="dns-names.txt"
        self.subdo = False
        self.verbose = verbose
        try:
            f = open(self.file,"r")
        except:
            print "Error opening dns dictionary file"
            sys.exit()
        self.list = f.readlines()

    def getdns(self,domain):
        DNS.ParseResolvConf("/etc/resolv.conf")
        nameserver=DNS.defaults['server'][0]
        dom=domain
        if self.subdo == True:
            dom=domain.split(".")
            dom.pop(0)
            rootdom=".".join(dom)
        else:
            rootdom=dom
        if self.nameserver == False:
            r=DNS.Request(rootdom,qtype='SOA').req()
            primary,email,serial,refresh,retry,expire,minimum = r.answers[0]['data']
            test=DNS.Request(rootdom,qtype='NS',server=primary,aa=1).req()
            if test.header['status'] != "NOERROR":
                print "Error"
                sys.exit()
            self.nameserver= test.answers[0]['data']
        elif self.nameserver == "local":
            self.nameserver=nameserver
        return self.nameserver

    def run(self,host):
        if self.nameserver == "":
            self.nameserver = self.getdns(self.domain)
        hostname=str(host.split("\n")[0])+"."+str(self.domain)
        if self.verbose:
            ESC=chr(27)
            sys.stdout.write(ESC + '[2K' + ESC+'[G')
            sys.stdout.write("\r" + hostname)
            sys.stdout.flush()
        try:
            test=DNS.Request(hostname,qtype='a',server=self.nameserver).req()
            hostip=test.answers[0]['data']
            return hostip+":"+hostname
        except Exception,e:
            pass

    def process(self):
        results=[]
        for x in self.list:
            host=self.run(x)
            if host!=None:
                results.append(host)
        return results

class dns_tld():
    def __init__(self,domain,dnsserver,verbose=False):
        self.domain=domain
        self.nameserver = dnsserver
        self.subdo = False
        self.verbose = verbose
        self.tlds = ["com", "org", "net", "edu", "mil", "gov", "uk", "af", "al", "dz",
                     "as", "ad", "ao", "ai", "aq", "ag", "ar", "am", "aw", "ac","au",
                     "at", "az", "bs", "bh", "bd", "bb", "by", "be", "bz", "bj", "bm",
                     "bt", "bo", "ba", "bw", "bv", "br", "io", "bn", "bg", "bf", "bi",
                     "kh", "cm", "ca", "cv", "ky", "cf", "td", "cl", "cn", "cx", "cc",
                     "co", "km", "cd", "cg", "ck", "cr", "ci", "hr", "cu", "cy", "cz",
                     "dk", "dj", "dm", "do", "tp", "ec", "eg", "sv", "gq", "er", "ee",
                     "et", "fk", "fo", "fj", "fi", "fr", "gf", "pf", "tf", "ga", "gm",
                     "ge", "de", "gh", "gi", "gr", "gl", "gd", "gp", "gu", "gt", "gg",
                     "gn", "gw", "gy", "ht", "hm", "va", "hn", "hk", "hu", "is", "in",
                     "id", "ir", "iq", "ie", "im", "il", "it", "jm", "jp", "je", "jo",
                     "kz", "ke", "ki", "kp", "kr", "kw", "kg", "la", "lv", "lb", "ls",
                     "lr", "ly", "li", "lt", "lu", "mo", "mk", "mg", "mw", "my", "mv",
                     "ml", "mt", "mh", "mq", "mr", "mu", "yt", "mx", "fm", "md", "mc",
                     "mn", "ms", "ma", "mz", "mm", "na", "nr", "np", "nl", "an", "nc",
                     "nz", "ni", "ne", "ng", "nu", "nf", "mp", "no", "om", "pk", "pw",
                     "pa", "pg", "py", "pe", "ph", "pn", "pl", "pt", "pr", "qa", "re",
                     "ro", "ru", "rw", "kn", "lc", "vc", "ws", "sm", "st", "sa", "sn",
                     "sc", "sl", "sg", "sk", "si", "sb", "so", "za", "gz", "es", "lk",
                     "sh", "pm", "sd", "sr", "sj", "sz", "se", "ch", "sy", "tw", "tj",
                     "tz", "th", "tg", "tk", "to", "tt", "tn", "tr", "tm", "tc", "tv",
                     "ug", "ua", "ae", "gb", "us", "um", "uy", "uz", "vu", "ve", "vn",
                     "vg", "vi", "wf", "eh", "ye", "yu", "za", "zr", "zm", "zw", "int",
                     "gs", "info", "biz", "su", "name", "coop", "aero" ]

    def getdns(self,domain):
        DNS.ParseResolvConf("/etc/resolv.conf")
        nameserver=DNS.defaults['server'][0]
        dom=domain
        if self.subdo == True:
            dom=domain.split(".")
            dom.pop(0)
            rootdom=".".join(dom)
        else:
            rootdom=dom
        if self.nameserver == False:
            r=DNS.Request(rootdom,qtype='SOA').req()
            primary,email,serial,refresh,retry,expire,minimum = r.answers[0]['data']
            test=DNS.Request(rootdom,qtype='NS',server=primary,aa=1).req()
            if test.header['status'] != "NOERROR":
                print "Error"
                sys.exit()
            self.nameserver= test.answers[0]['data']
        elif self.nameserver == "local":
            self.nameserver=nameserver
        return self.nameserver

    def run(self,tld):
        self.nameserver = self.getdns(self.domain)
        hostname=self.domain.split(".")[0]+"."+tld
        if self.verbose:
            ESC=chr(27)
            sys.stdout.write(ESC + '[2K' + ESC+'[G')
            sys.stdout.write("\r\tSearching for: " + hostname)
            sys.stdout.flush()
        try:
            test=DNS.Request(hostname,qtype='a',server=self.nameserver).req()
            hostip=test.answers[0]['data']
            return hostip+":"+hostname
        except Exception,e:
            pass

    def process(self):
        results=[]
        for x in self.tlds:
            host=self.run(x)
            if host!=None:
                results.append(host)
        return results
