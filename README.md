### This repository contains the unstable development version.
### For the stable version go to: <a href="https://github.com/golismero/golismero">https://github.com/golismero/golismero</a></font></p>

---

What's GoLismero 2.0?
=====================

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

Quick help
==========

Using GoLismero 2.0 is very easy. Below are some basic commands to start to using it:

Installing
----------

Just [download](https://github.com/golismero/golismero/archive/master.zip) and extract the compressed file anywhere you like. GoLismero already ships all of its dependencies, with the exception of the Python interpreter itself.

You can also get the latest version using Git:

```git clone https://github.com/golismero/golismero.git```

Basic usage
-----------

This command will launch GoLismero with all default options and show the report on standard output:

```python golismero.py scan <target>```

If you omit the default command "scan" GoLismero is smart enough to figure out what you're trying to do, so this works too:

```python golismero.py <target>```

You can also set a name for your audit with --audit-name:

```python golismero.py scan <target> --audit-name <name>```

And you can produce reports in different file formats. The format is guessed from the file extension, and you can write as many files as you want:

```python golismero.py scan <target> -o <output file name>```

![Run example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/run_mac.png "Run example")

Additionally, you can import results from other tools with the -i option. You can use -i several times to import multiple files.

```python golismero.py import -i nikto_output.csv -i nmap_output.xml -db database.db```

All results are automatically stored in a database file. You can prevent this with the -nd option:

```python golismero.py <target> -nd```

![No database example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/no_db_mint.png "No database example")

This allows you to scan the target in one step, and generating the report later. For example, to scan without generating a report:

```python golismero.py scan <target> -db database.db -no```

And then generate the report from the database at a later time (or from a different machine!):

```python golismero.py report -db database.db -o report.html```

You can also specify multiple output files by repeating the -o option:

```python golismero.py report -db database.db -o report.html -o report.rst -o report.txt```

![Report example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/report_win.png "Report example")

Available plugins
-----------------

To display the list of available plugins:

```python golismero.py plugins```

![Plugin list example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/plugin_list_mac_2.png "Plugin list example")

You can also query more information about specific plugins:

```python golismero.py info <plugin>```

![Plugin info example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/plugin_info_mint.png "Plugin list example")

The full plugin list is also available [online](http://golismero-project.com/doc/plugin_list/index.html).

Select a specific plugin
------------------------

Use the -e option to enable only some specific plugins, and -d to disable plugins (you can use -e and -d many times):

```python golismero.py <target> -e <plugin>```

You can also select multiple plugins using wildcards. For example, you can select all bruteforce plugins like this:

```python golismero.py <target> -e brute*```

![Run plugin example](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/run_plugin_mac_2.png "Run plugin example")

Reporting and eye candy
-----------------------

GoLismero currently produces reports on the console, in plain text files, in reStructured text format and in HTML format. In all cases, the reports are self-contained in a single file for easier transport - that means the HTML report is a single .html file with everything bundled in, and you can just attach it in an email to send it to someone else.

If no output files are specified, GoLismero reports on the console by default. But you can choose both at the same time too! For example, let's write an HTML report and also see the output on the console, using the special filename "-":

```python golismero.py scan <target> -o - -o report.html```

Here's what the HTML report summary looks like:

![Report summary](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/report1.png "Report summary")

And the HTML report details:

![Report details](https://raw.github.com/cr0hn/golismero/master/doc/screenshots/report2.png "Report details")

Putting it all together
-----------------------

In this example we'll put everything we've seen above into practice in a single command. We'll import results from an Nmap scan, run a scan of our own but using only the DNS analysis plugins, save the results in a database file of our choosing and produce reports in HTML and reStructured text format.

```python golismero.py -i nmap_output.xml -e dns* -db database.db -o report.rst -o report.html```

Notice how the default "scan" command was ommitted but GoLismero figured it out on its own.

This is how you'd do it if you want to break it into multiple commands instead:

```
python golismero.py import -db database.db -i nmap_output.xml
python golismero.py scan -db database.db -e dns* -no
python golismero.py report -db database.db -o report.rst -o report.html
```

Notice how the second command uses the "-no" switch to prevent the default console report from kicking in.

What will be the next features?
===============================

The next features of golismero will be:

- Integration with SQLMap, ZAP, Metasploit, Shodan and many other tools.
- Web UI. We all know true h4xx0rs only use the console, but sometimes drag&drop does come in handy. ;)
- Export results in PDF format.
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
