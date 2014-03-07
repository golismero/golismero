import string
import re
import HTMLParser


class parser:
    def __init__(self, results, word):
        self.results = results
        self.word = word
        self.temp = []

    def genericClean(self):

        for e in ('<em>','<b>', '</b>', '</em>', '<strong>', '</strong>'):
            self.results = string.replace(self.results, e, '')

        for e in ('%2f', '%2F', '%3a', '%3A', '%3D', '%3C', ':', '=', '<', '/', '\\', ';', '&'):
            self.results = string.replace(self.results, e, ' ')

    def urlClean(self):

        for e in ('<em>','</em>'):
            self.results = string.replace(self.results, e, '')

        for e in ('<', '>', ':', '=', ';', '&', '%3A', '%3D', '%3C', '%2f'):
            self.results = string.replace(self.results, e, ' ')

    def emails(self):
        self.genericClean()
        reg_emails = re.compile('[a-zA-Z0-9.\-_]*' + '@' + '[a-zA-Z0-9.-]*' + self.word)
        self.temp = reg_emails.findall(self.results)
        emails = self.unique()
        return emails

    def fileurls(self, file):
        urls = []
        reg_urls = re.compile('<a href="(.*?)"')
        self.temp = reg_urls.findall(self.results)
        allurls = self.unique()
        for x in allurls:
            if x.count('webcache') or x.count('google.com') or x.count('search?hl'):
                pass
            else:
                urls.append(x)
        return urls

    def people_linkedin(self):

        reg_people = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)

        results = []  #self.temp = reg_people.search(self.results)
        self.temp = reg_people.findall(self.results)
        for x in self.temp:
            if '| LinkedIn' in x:
                y = x
                for e in (' | LinkedIn', ' profiles ', 'LinkedIn', '"', '<b>', '</b>'):
                    y = string.replace(y, e, '')

                if y != " ":
                    results.append(HTMLParser.HTMLParser().unescape(y))

        self.temp = results
        results = self.unique()
        return results

    def people_123people(self):
        reg_people = re.compile('www\.123people\.com/s/[a-zA-Z0-9.-_]*\+[a-zA-Z0-9.-_]*\+?[a-zA-Z0-9.-_]*\"')
        self.temp = reg_people.findall(self.results)
        self.temp2 = []
        for x in self.temp:
            y = x.replace("www.123people.com/s/", "").replace('"', '').replace('+', ' ')
            self.temp2.append(HTMLParser.HTMLParser().unescape(y))
        return self.temp2

    def people_jigsaw(self):
        res = []
        #reg_people = re.compile("'tblrow' title='[a-zA-Z0-9.-]*'><span class='nowrap'/>")
        reg_people = re.compile("href=javascript:showContact\('[0-9]*'\)>[a-zA-Z0-9., ]*</a></span>")
        self.temp = reg_people.findall(self.results)
        for x in self.temp:
            a = x.split('>')[1].replace("</a", "")
            res.append(HTMLParser.HTMLParser().unescape(a))
        return res

    def profiles(self):
        reg_people = re.compile('">[a-zA-Z0-9._ -]* - <em>Google Profile</em>')
        self.temp = reg_people.findall(self.results)
        results = []
        for x in self.temp:
            y = string.replace(x, ' <em>Google Profile</em>', '')
            y = string.replace(y, '-', '')
            y = string.replace(y, '">', '')
            if y != " ":
                results.append(HTMLParser.HTMLParser().unescape(y))
        return results


    def hostnames(self):
        self.genericClean()
        reg_hosts = re.compile('[a-zA-Z0-9.-]*\.' + self.word)
        self.temp = reg_hosts.findall(self.results)
        hostnames = self.unique()
        return hostnames


    def set(self):
        reg_sets = re.compile('>[a-zA-Z0-9]*</a></font>')
        self.temp = reg_sets.findall(self.results)
        sets = []
        for x in self.temp:
            y = string.replace(x, '>', '')
            y = string.replace(y, '</a</font', '')
            sets.append(HTMLParser.HTMLParser().unescape(y))
        return sets


    def hostnames_all(self):
        reg_hosts = re.compile('<cite>(.*?)</cite>')
        temp = reg_hosts.findall(self.results)
        for x in temp:
            if x.count(':'):
                res = x.split(':')[1].split('/')[2]
            else:
                res = x.split("/")[0]
            self.temp.append(res)
        hostnames = self.unique()
        return hostnames


    def unique(self):
        self.new = []
        for x in self.temp:
            if x != "" and x[0] != "@" and x.lower() not in self.new:
                self.new.append(x.lower())

        return self.new
