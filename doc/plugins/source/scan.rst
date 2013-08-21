Scan
****

Scan plugins perform active, non-invasive information gathering tests on the targets.

Bruteforce directories discovery (*brute_directories*)
======================================================

Tries to discover hidden folders by brute force:
www.site.com/folder/ -> www.site.com/folder2 www.site.com/folder3 ...

Bruteforce file extensions discovery (*brute_extensions*)
=========================================================

Tries to discover hidden files by brute force:
www.site.com/index.php -> www.site.com/index.php.old

Bruteforce permutations discovery (*brute_permutations*)
========================================================

Tries to discover hidden files by bruteforcing the extension:
www.site.com/index.php -> www.site.com/index.php2

Bruteforce predictables discovery (*brute_predictables*)
========================================================

Tries to discover hidden files at predictable locations.
For example: (Apache) www.site.com/error_log

Bruteforce prefixes discovery (*brute_prefixes*)
================================================

Tries to discover hidden files by bruteforcing prefixes:
www.site.com/index.php -> www.site.com/~index.php

Bruteforce suffixes discovery (*brute_suffixes*)
================================================

Tries to discover hidden files by bruteforcing suffixes:
www.site.com/index.php -> www.site.com/index2.php

Nikto (*nikto*)
===============

Run the Nikto scanner and import the results.

================= =================
**Argument name** **Default value**
----------------- -----------------
pause             0                
config            nikto.conf       
tuning            x6               
timeout           10               
================= =================

OpenVAS (*openvas*)
===================

Run the OpenVAS scanner and import the results

================= ================================
**Argument name** **Default value**               
----------------- --------------------------------
profile           Full and fast                   
host              127.0.0.1                       
user              admin                           
timeout           30                              
password          \*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*
port              9390                            
================= ================================

