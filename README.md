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

```python golismero.py <target>```

You can also set a name for your audit with --audit-name:

```python golismero.py <target> --audit-name <name>```

And you can produce reports in different file formats. The format is guessed from the file extension, and you can write as many files as you want:

```python golismero.py <target> -o <output file name>```

![Run example](https://raw.github.com/golismero/golismero/master/doc/screenshots/run_mac.png "Run example")

Additionally, you can import results from other tools with the -i option. You can use -i several times to import multiple files. This example shows how to parse the results from a Nikto scan and produce a report. To keep GoLismero from re-scanning the target, we'll disable all plugins:

```python golismero.py www.example.com -i nikto_output.csv -o report.html -d all```

![Import export example](https://raw.github.com/golismero/master/doc/screenshots/import_export_win.png "Import export example")

All results are automatically stored in a database file. You can prevent this with the -nd option:

```python golismero.py <target> -nd```

![No database example](https://raw.github.com/golismero/master/doc/screenshots/no_db_mint.png "No database example")

This allows you to scan the target in one step, and generating the report later. For example, to scan without generating a report:

```python golismero.py <target> -db database.db -no```

And then generate the report from the database at a later time (or from a different machine!):

```python golismero.py -db database.db -d all -o report.html```

Available plugins
-----------------

To display the list of available plugins:

```python golismero.py --plugin-list```

![Plugin list example](https://raw.github.com/golismero/master/doc/screenshots/plugin_list_mac_2.png "Plugin list example")

You can also query more information about specific plugins:

```python golismero.py --plugin-info <plugin name>```

![Plugin info example](https://raw.github.com/golismero/master/doc/screenshots/plugin_info_mint.png "Plugin list example")

The full plugin list is also available [online](http://golismero-project.com/doc/plugin_list/index.html).

Select a specific plugin
------------------------

Use the -e option to enable only some specific plugins, and -d to disable plugins (you can use -e and -d many times):

```python golismero.py <target> -e <plugin id>```

You can also select multiple plugins using wildcards. For example, you can select all bruteforce plugins like this:

```python golismero.py <target> -e brute*```

![Run plugin example](https://raw.github.com/golismero/master/doc/screenshots/run_plugin_mac_2.png "Run plugin example")

Reporting and eye candy
-----------------------

This is how to generate an HTML report for an audit:

```python golismero.py <target> -o report.html```

Report summary:

![Report summary](https://raw.github.com/golismero/master/doc/screenshots/report1.png "Report summary")

Report details:

![Report details](https://raw.github.com/golismero/master/doc/screenshots/report2.png "Report details")

What will be the next features?
===============================

The next features of golismero will be:

- Integration with Nmap, SQLMap, Metasploit and many other tools.
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
* Control-C on Python generally doesn't work very well - sometimes it just shows bogus errors on screen, but you can ignore them. If stopping GoLismero takes too long, try hitting Control-C twice for force shutdown. Even then, sometimes you just have to be a patient!
* When running the Nikto plugin, GoLismero may appear unresponsive. But everything is OK, this happens because the plugin waits for Nikto to finish its scan before printing anything on screen. So be patient! :) we expect to improve this soon.
* GoLismero seems to run slower on Windows than on Linux or Mac. We're still not completely sure why, but it seems to be related to the Python standard multiprocessing module and the lack of fork() support on Windows.
* This is not a bug, just a reminder: GoLismero by default creates a new database file on each run! You can disable the database creation with the -nd switch.
