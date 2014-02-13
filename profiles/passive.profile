[golismero]
description = Perform a passive scan on a website.
include_subdomains = yes
allow_parent = yes
depth = infinite
max_links = 0
follow_redirects = yes
follow_first_redirect = no
disable_plugins = all
enable_plugins = import, dns, dns_malware, geoip, theharvester, suspicious_url, report
