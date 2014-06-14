#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
Golismero project mail: contact@golismero-project.com


This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import os

try:
    import cPickle as Pickle
except ImportError:
    import pickle as Pickle


#------------------------------------------------------------------------------
signatures = {

"Internet Information Server (IIS)":

"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
<title>403 - Prohibido: acceso denegado.</title>
<style type="text/css">
<!--
body{margin:0;font-size:.7em;font-family:Verdana, Arial, Helvetica, sans-serif;background:#EEEEEE;}
fieldset{padding:0 15px 10px 15px;}
h1{font-size:2.4em;margin:0;color:#FFF;}
h2{font-size:1.7em;margin:0;color:#CC0000;}
h3{font-size:1.2em;margin:10px 0 0 0;color:#000000;}
#header{width:96%;margin:0 0 0 0;padding:6px 2% 6px 2%;font-family:"trebuchet MS", Verdana, sans-serif;color:#FFF;
background-color:#555555;}
#content{margin:0 0 0 2%;position:relative;}
.content-container{background:#FFF;width:96%;margin-top:8px;padding:10px;position:relative;}
-->
</style>
</head>
<body>
<div id="header"><h1>Error del servidor</h1></div>
<div id="content">
 <div class="content-container"><fieldset>
  <h2>403 - Prohibido: acceso denegado.</h2>
  <h3>No tiene permiso para ver este directorio o esta página con las credenciales que ha proporcionado.</h3>
 </fieldset></div>
</div>
</body>
</html>
""",


#------------------------------------------------------------------------------
"Nginx":

"""<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>""",


#------------------------------------------------------------------------------
"Apache Tomcat":

"""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
 <head>
  <title>403 Access Denied</title>
  <style type="text/css">
    <!--
    BODY {font-family:Tahoma,Arial,sans-serif;color:black;background-color:white;font-size:12px;}
    H1 {font-family:Tahoma,Arial,sans-serif;color:white;background-color:#525D76;font-size:22px;}
    PRE, TT {border: 1px dotted #525D76}
    A {color : black;}A.name {color : black;}
    -->
  </style>
 </head>
 <body>
   <h1>403 Access Denied</h1>
   <p>
    You are not authorized to view this page.
   </p>
   <p>
    If you have already configured the Manager application to allow access and
    you have used your browsers back button, used a saved book-mark or similar
    then you may have triggered the cross-site request forgery (CSRF) protection
    that has been enabled for the HTML interface of the Manager application. You
    will need to reset this protection by returning to the
    <a href="<%=request.getContextPath()%>/html">main Manager page</a>. Once you
    return to this page, you will be able to continue using the Manager
    appliction's HTML interface normally. If you continue to see this access
    denied message, check that you have the necessary permissions to access this
    application.
   </p>
   <p>
    If you have not changed
    any configuration files, please examine the file
    <tt>conf/tomcat-users.xml</tt> in your installation. That
    file must contain the credentials to let you use this webapp.
   </p>
   <p>
    For example, to add the <tt>manager-gui</tt> role to a user named
    <tt>tomcat</tt> with a password of <tt>s3cret</tt>, add the following to the
    config file listed above.
   </p>
<pre>
&lt;role rolename="manager-gui"/&gt;
&lt;user username="tomcat" password="s3cret" roles="manager-gui"/&gt;
</pre>
   <p>
    Note that for Tomcat 7 onwards, the roles required to use the manager
    application were changed from the single <tt>manager</tt> role to the
    following four roles. You will need to assign the role(s) required for
    the functionality you wish to access.
   </p>
    <ul>
      <li><tt>manager-gui</tt> - allows access to the HTML GUI and the status
          pages</li>
      <li><tt>manager-script</tt> - allows access to the text interface and the
          status pages</li>
      <li><tt>manager-jmx</tt> - allows access to the JMX proxy and the status
          pages</li>
      <li><tt>manager-status</tt> - allows access to the status pages only</li>
    </ul>
   <p>
    The HTML interface is protected against CSRF but the text and JMX interfaces
    are not. To maintain the CSRF protection:
   </p>
   <ul>
    <li>Users with the <tt>manager-gui</tt> role should not be granted either
        the <tt>manager-script</tt> or <tt>manager-jmx</tt> roles.</li>
    <li>If the text or jmx interfaces are accessed through a browser (e.g. for
        testing since these interfaces are intended for tools not humans) then
        the browser must be closed afterwards to terminate the session.</li>
   </ul>
   <p>
    For more information - please see the
    <a href="/docs/manager-howto.html">Manager App HOW-TO</a>.
   </p>
 </body>

</html>""",


#------------------------------------------------------------------------------
"Apache":

"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
<title>Authentication required!</title>
<link rev="made" href="mailto:admin@localhost" />
<style type="text/css"><![CDATA[
    body { color: #000000; background-color: #FFFFFF; }
    a:link { color: #0000CC; }
    p, address {margin-left: 3em;}
    span {font-size: smaller;}
]]></style>
</head>

<body>
<h1>Authentication required!</h1>
<p>

    This server could not verify that you are authorized to access
    the URL specified.
    You either supplied the wrong credentials (e.g., bad password), or your
    browser doesn't understand how to supply the credentials required.

        <p></p>

    In case you are allowed to request the document, please
    check your user-id and password and try again.

</p>
<p>
If you think this is a server error, please contact
the <a href="mailto:admin@localhost">webmaster</a>.
</p>

<h2>Error 403</h2>
<address>
  <a href="/">Apache 2.4.1 </a><br />
  <span>App engine 2.0</span>
</address>
</body>
</html>"""

}


#-------------------------------------------------------------------------------
def main():
    signatures_file = os.path.join(os.path.split(__file__)[0], "signatures.dat")

    # Dump the info
    Pickle.dump(signatures, open(signatures_file, "wb"))

if __name__ == '__main__':
    main()
