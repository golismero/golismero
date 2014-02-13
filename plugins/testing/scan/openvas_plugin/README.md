# How to use OpenVAS correlation

To use OpenVAS correlation you must setup plugins first. Follow these steps:

## 1 - Download OpenVAS plugins

You need the OpenVAS plugins feed. You can download it from [http://www.openvas.org/openvas-nvt-feed-current.tar.bz2](http://www.openvas.org/openvas-nvt-feed-current.tar.bz2) or get it from your OpenVAS installation.

## 2 - Generate database

Now we need to generate the database. To do that, you must run:

```python setup.py -p YOUR_PLUGIN_LOCATION -v```

## 3 - Done

Now we can a SQLite3 database in the running place, called: **openvas.sqlite3**

