[golismero]
description = Perform a DNS security audit.
only_vulns = yes
include_subdomains = yes
depth = 0
follow_redirects = no
follow_first_redirect = no
disable_plugins = all
enable_plugins = dns, zone_transfer, brute_dns
