
What's GoLismero?
=================

GoLismero is an open source framework for security testing. It's currently geared towards web security, but it can easily be expanded to other kinds of scans.

The most interesting features of the framework are:

- Real platform independence. Tested on Windows, Linux, *BSD and OS X.
- No native library dependencies. All of the framework has been written in pure Python.
- Good performance when compared with other frameworks written in Python and other scripting languages.
- Very easy to use.
- Plugin development is extremely simple.
- The framework also collects and unifies the results of well known tools: sqlmap, xsser, openvas, dnsrecon, theharvester...
- Integration with standards: CWE, CVE and OWASP.
- Designed for cluster deployment in mind (not available yet).

Installing
==========

Strictly speaking, GoLismero doesn't require installation - only its dependencies do. So if you want to use it on a system where you don't have root privileges, you can ask the system administrator to install them for you, and just run the "git checkout" command on your home folder.

The following are step-by-step instructions to install GoLismero on different operating systems:

Debian/Ubuntu
-------------

The following commands will download and install GoLismero on your system. This requires root privileges, so you will be prompted for your password when you run the first command.

```
sudo bash
apt-get install python2.7 python2.7-dev python-pip python-docutils git perl nmap sslscan
cd /opt
git clone https://github.com/golismero/golismero.git
cd golismero
pip install -r requirements.txt
pip install -r requirements_unix.txt
ln -s /opt/golismero/golismero.py /usr/bin/golismero
exit
```

If you have an API key for Shodan, or an OpenVAS server or SpiderFoot server you want to integrate with GoLismero, run the following commands:

```
mkdir ~/.golismero
touch ~/.golismero/user.conf
chmod 600 ~/.golismero/user.conf
nano ~/.golismero/user.conf
```

At the editor, add the following sections to the file, as appropriate:

```
[shodan:Configuration]
apikey = <INSERT YOUR SHODAN API KEY HERE>

[openvas]
host = <INSERT THE OPENVAS HOST HERE>
user = <INSERT THE OPENVAS USERNAME HERE>
*password = <INSERT THE OPENVAS PASSWORD HERE>

[spiderfoot]
url = <INSERT THE SPIDERFOOT URL HERE>
```

Mac OS X
--------

First of all, on Mac we'll need to install the [Mac Ports](http://www.macports.org/install.php).

After doing that, run the following commands to download and install GoLismero on your system. This requires root privileges, so you will be prompted for your password when you run the first command.

```
sudo -s
easy_install-2.7 -U distribute
easy_install install pip
port install nmap sslscan
cd /opt
git clone https://github.com/golismero/golismero.git
cd golismero
pip install -r requirements.txt
pip install -r requirements_unix.txt
ln -s /opt/golismero/golismero.py /usr/bin/golismero
exit
```

If you have an API key for Shodan, or an OpenVAS server or SpiderFoot server you want to integrate with GoLismero, run the following commands:

```
mkdir ~/.golismero
touch ~/.golismero/user.conf
chmod 600 ~/.golismero/user.conf
nano ~/.golismero/user.conf
```

At the editor, add the following sections to the file, as appropriate:

```
[shodan:Configuration]
apikey = <INSERT YOUR SHODAN API KEY HERE>

[openvas]
host = <INSERT THE OPENVAS HOST HERE>
user = <INSERT THE OPENVAS USERNAME HERE>
*password = <INSERT THE OPENVAS PASSWORD HERE>

[spiderfoot]
url = <INSERT THE SPIDERFOOT URL HERE>
```

FreeBSD 10-Release
------------------

The following commands will download and install GoLismero on your system. This requires root privileges, so you will be prompted for your password when you run the first command.

```
su -
cd /root
pkg update
pkg install git
pkg install python27
ln -s /usr/local/bin/python2.7 /usr/local/bin/python
pkg install databases/py-sqlite3
pkg install nmap
pkg install sslscan
pkg install devel/py-pip
mkdir /opt 2> /dev/null
cd /opt
git clone https://github.com/golismero/golismero.git
cd golismero
pip install -r requirements.txt
pip install -r requirements_unix.txt
ln -s /opt/golismero/golismero.py /usr/bin/golismero
exit
```

If you have an API key for Shodan, or an OpenVAS server or SpiderFoot server you want to integrate with GoLismero, run the following commands:

```
mkdir ~/.golismero
touch ~/.golismero/user.conf
chmod 600 ~/.golismero/user.conf
nano ~/.golismero/user.conf
```

At the editor, add the following sections to the file, as appropriate:

```
[shodan:Configuration]
apikey = <INSERT YOUR SHODAN API KEY HERE>

[openvas]
host = <INSERT THE OPENVAS HOST HERE>
user = <INSERT THE OPENVAS USERNAME HERE>
*password = <INSERT THE OPENVAS PASSWORD HERE>

[spiderfoot]
url = <INSERT THE SPIDERFOOT URL HERE>
```

Windows
-------

On Windows, you'll have to install each tool separately. You can download them from here:
- [Python 2.7](http://python.org/download/releases/2.7.6/)
- [Git](https://code.google.com/p/msysgit/downloads/list)
- [Nmap](http://nmap.org/download.html#windows)
- [SSLScan](https://code.google.com/p/sslscan-win/)

Nikto is already bundled with GoLismero, but it requires the Cygwin version of Perl to run, since the native version can't handle Unix paths. You can download if from here: [Cygwin](http://cygwin.com/install.html).

SSLScan for Windows has a bug that causes crashes when writing XML output, which is the one required by GoLismero. The issue has been [unfixed since 2010](https://code.google.com/p/sslscan-win/issues/detail?id=2), so it's not likely to change soon, but there's a workaround: simply upgrade OpenSSL to a newer version. You can get an OpenSSL build from here: [Win32OpenSSL](https://slproweb.com/products/Win32OpenSSL.html).

It's usually a good idea to install Visual Studio 2008 SP1 as well. This enables the compilation of C extensions, which can speed up some Python modules.

After installing the tools, open a console and run the following commands:

```
cd %HOME%
git clone https://github.com/golismero/golismero.git
cd golismero
pip install -r requirements.txt
```

Finally, you may have to add the tools to the PATH environment variable so GoLismero can find them. You can also add GoLismero itself to the PATH.

If you have an API key for Shodan, or an OpenVAS server or SpiderFoot server you want to integrate with GoLismero, create a new file called "user.conf" where you installed GoLismero and add the following sections to the file, as appropriate:

```
[shodan:Configuration]
apikey = <INSERT YOUR SHODAN API KEY HERE>

[openvas]
host = <INSERT THE OPENVAS HOST HERE>
user = <INSERT THE OPENVAS USERNAME HERE>
*password = <INSERT THE OPENVAS PASSWORD HERE>

[spiderfoot]
url = <INSERT THE SPIDERFOOT URL HERE>
```

Quick help
==========

Using GoLismero is very easy. Below are some basic commands to start to using it:

Basic usage
-----------

This command will launch GoLismero with all default options and show the report on standard output:

```golismero scan <target>```

If you omit the default command "scan" GoLismero is smart enough to figure out what you're trying to do, so this works too:

```golismero <target>```

You can also set a name for your audit with --audit-name:

```golismero scan <target> --audit-name <name>```

And you can produce reports in different file formats. The format is guessed from the file extension, and you can write as many files as you want:

```golismero scan <target> -o <output file name>```

![Run example](https://raw.github.com/golismero/golismero/master/doc/screenshots/run_mac.png "Run example")

Additionally, you can import results from other tools with the -i option. You can use -i several times to import multiple files.

```golismero import nikto_output.csv nmap_output.xml -db database.db```

This allows you to scan the target in one step, and generate the report later. For example, to scan without generating a report:

```golismero scan <target> -db database.db -no```

And then generate the report from the database at a later time (or from a different machine!):

```golismero report report.html -db database.db```

You can also specify multiple output files:

```golismero report report.html report.txt report.rst -db example.db```

![Report example](https://raw.github.com/golismero/golismero/master/doc/screenshots/report_win.png "Report example")

Available plugins
-----------------

To display the list of available plugins:

```golismero plugins```

![Plugin list example](https://raw.github.com/golismero/golismero/master/doc/screenshots/plugin_list_mac.png "Plugin list example")

You can also query more information about specific plugins:

```golismero info <plugin>```

![Plugin info example](https://raw.github.com/golismero/golismero/master/doc/screenshots/plugin_info_mint.png "Plugin list example")

The full plugin list is also available [online](http://golismero-project.com/doc/plugin_list/index.html).

Select a specific plugin
------------------------

Use the -e option to enable only some specific plugins, and -d to disable plugins (you can use -e and -d many times):

```golismero scan <target> -e <plugin>```

You can also select multiple plugins using wildcards. For example, you can select all bruteforce plugins like this:

```golismero scan <target> -e brute*```

![Run plugin example](https://raw.github.com/golismero/golismero/master/doc/screenshots/run_plugin_mac_2.png "Run plugin example")

Reporting and eye candy
-----------------------

GoLismero currently produces reports on the console, in plain text files, in reStructured text format and in HTML format. In all cases, the reports are self-contained in a single file for easier transport - that means the HTML report is a single .html file with everything bundled in, and you can just attach it in an email to send it to someone else.

If no output files are specified, GoLismero reports on the console by default. But you can choose both at the same time too! For example, let's write an HTML report and also see the output on the console, using the special filename "-":

```golismero scan <target> -o - -o report.html```

Here's what the HTML report summary looks like on Chrome:

![Report header](https://raw.github.com/golismero/golismero/master/doc/screenshots/report_chrome_header.png "Report header")

The table of contents, on Firefox:

![Report table](https://raw.github.com/golismero/golismero/master/doc/screenshots/report_firefox_header.png "Report table")

And the details for each vulnerability, on Internet Explorer:

![Report details](https://raw.github.com/golismero/golismero/master/doc/screenshots/report_ie_detail.png "Report details")

It's also compatible with mobile devices, like for example an iPad:

![Report summary on iPad](https://raw.github.com/golismero/golismero/master/doc/screenshots/report_ipad.png "Report summary on iPad")

As you surely noticed, the layout remains consistent across all platforms. The HTML report is completely self contained in a single .html file, making it very easy to share.

Putting it all together
-----------------------

In this example we'll put everything we've seen above into practice in a single command. We'll import results from an Nmap scan, run a scan of our own but using only the DNS analysis plugins, save the results in a database file of our choosing and produce reports in HTML and reStructured text format.

```golismero -i nmap_output.xml -e dns* -db database.db -o report.rst -o report.html```

Notice how the default "scan" command was omitted but GoLismero figured it out on its own.

This is how you'd do it if you want to break it into multiple commands instead:

```
golismero import -db database.db nmap_output.xml
golismero scan -db database.db -e dns* -no
golismero report -db database.db report.rst report.html
```

Notice how the second command uses the "-no" switch to prevent the default console report from kicking in.

What will be the next features?
===============================

The next features of GoLismero will be:

- Integration with Metasploit, w3af, ZAP and many other free tools.
- Web UI. We all know true h4xx0rs only use the console, but sometimes drag&drop does come in handy. ;)
- Export results in PDF and MS Word format, to keep the boss happy.
- And more plugins of course!

Not enough? Roll your own!
==========================

GoLismero is fully extensible through plugins, and that means you can always roll your own scripts, tailored to your specific needs, or using your favorite tools.

You can start from the [plugin API documentation](http://golismero-project.com/doc/plugin_developers/index.html), and move on to the [full specifications](http://golismero-project.com/doc/fulldoc/index.html) if you want to tinker with GoLismero's internals.

More step-by-step tutorials and howtos are coming soon!

Need help? Found a bug?
=======================

If you have found a bug, you can report it using the Github issues system. You can also drop us an email (golismero.project@gmail.com) or find us on Twitter ([@golismero_pro](https://twitter.com/golismero_pro)).

Known bugs
----------

Some gotchas we already know about:
* Control-C on Python generally doesn't work very well - it may show bogus errors on screen, but you can ignore them. If stopping GoLismero takes too long, try hitting Control-C twice for force shutdown. Even then, sometimes you just have to be a patient!
* GoLismero seems to run slower on Windows than on Linux or Mac. It appears to be related to the Python standard multiprocessing module and the lack of fork() support on Windows.
* This is not a bug, just a reminder: GoLismero by default creates a new database file on each run! You can disable the database creation with the -nd switch.

[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/bd520897a768ee38569775bdb8372b8a "githalytics.com")](http://githalytics.com/golismero/golismero)
