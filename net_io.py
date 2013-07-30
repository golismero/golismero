'''
GoLISMERO - Simple web analisis
Copyright (C) 2011  Daniel Garcia | dani@estotengoqueprobarlo.es

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
'''


import urllib2
from urlparse import *
from ntlm import *
from sys import exit
import re

global Auth 
Auth = None # Autenticacion ya realizada. Para evitar hacer muchas peticiones

#
# Se encarga de descargar el contenido de una web con las opciones de proxy, seguridad, custom cookies, etc
#
# Devuelve != de None si todo ha ido bien
def downloadURL_(page, PARAMETERS):
	
	web_content=None


	#opener = urllib2.build_opener()

	#proxy_handler = {}
	#if PARAMETERS.PROXY is not None:
	#	proxy_handler = urllib2.ProxyHandler({'http': PARAMETERS.PROXY})
	#	opener.add_handler(proxy_handler)
	
	# Encodding
	
#	opener.addheaders = [("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")]
	
	# User agent
	#gzip, deflate
	m_headers = {}
	m_headers['User-agent'] = 'GoLISMERO/0.1'
	# ('User-agent', 'GoLISMERO/0.1')]
	#headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
	#opener.addheaders.append(("Accept-Encoding", "gzip, deflate"))
	#opener.addheaders.append(("Accept-Encoding", ""))
	#opener.addheaders.append(('Proxy-Connection', 'keep-alive'))
	#opener.addheaders.append(('Connection', ''))
	
	# Cookie
	#if PARAMETERS.COOKIE is not None:
	#	#req.add_header("User-Agent", "GoLISMERO")
	#	pass
	
	#f = opener.open(page)
	
	#conn = httplib.HTTPConnection(PARAMETERS.DOMAIN)


	if PARAMETERS.PROXY is not None:
		ps=PARAMETERS.PROXY.split(":")[0]
		pt=PARAMETERS.PROXY.split(":")[1]
		#conn.set_tunnel(host=ps, port=int(pt))
		#conn.connect()
	
	#conn.connect()
	#conn.request("GET", "",headers=m_headers)
	
	#f=conn.getresponse()
	
	#if f is not None:
	#	web_content = f.read()
	
	#conn.close()
	
	return web_content

#
# Comprueba si un sitio soporta autenticacion o no
#
# Devuelve: True; si la soporta.
def checkIfAuth(url, proxy):
	
	opener = urllib2.build_opener()
	
	if proxy is not None:
		proxy_handler = urllib2.ProxyHandler({'http': proxy})
		opener.add_handler(proxy_handler)		

	try:
		handle = opener.open(url, timeout=20)
	except IOError, e:
		if not hasattr(e, 'code') or e.code != 401:
			return False
		else:
			return True
	
	return False

#
# Comprueba que se puede autenticar con ese usuario y password
#
# Devuelve: True; si se conecta correctamente
def checkAuthCredentials(url, proxy, user, password):
	
	global Auth
	opener = urllib2.build_opener()
	
	# si ha proxy
	if proxy is not None:
		proxy_handler = urllib2.ProxyHandler({'http': proxy})
		opener.add_handler(proxy_handler)		
	
	# Si hay autenticacion	
	if user is not None and password is not None:	
		Auth = makeAuth(url,proxy,user,password)
		
		if Auth == None:
			return False
		
		opener.add_handler(Auth)

	try:
		handle = opener.open(url, timeout=20)

	except IOError, e:
		if not hasattr(e, 'code') or e.code != 401:
			return True
		else:
			return False
	
	return True
	


#
# Detecta los parametros de autenticacion de un servidor web
# 
def getAuthParams(url, proxy):
	opener = urllib2.build_opener()
	
	if proxy is not None:
		proxy_handler = urllib2.ProxyHandler({'http': proxy})
		opener.add_handler(proxy_handler)		

	try:
		handle = opener.open(url, timeout=20)
	except IOError, e:
		if not hasattr(e, 'code') or e.code != 401:
			return None
		else:
			authline = e.headers['www-authenticate']
			authobj = re.compile(r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',re.IGNORECASE)
			matchobj = authobj.match(authline)
			if not matchobj:
				return None
			scheme = matchobj.group(1)
			realm = matchobj.group(2)
			
			return scheme, realm
	finally:
		opener.close()
		
	return None

#
# Crea el objeto de autenticacion
#
def makeAuth(url, proxy, user, password):
	
	# Comprueba si el sitio soporta autenticacion
	if checkIfAuth(url, proxy) is True:
		
		# Detectamos parametros de autenticacion
		auth_type, realm = getAuthParams(url, proxy)
		
		# Usuario y pass 
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
		passman.add_password(realm, url, user, password)
		auth = None
		# Adaptar las credenciales segun la autenticacion
		if auth_type.lower() == "basic":
			auth = urllib2.HTTPBasicAuthHandler(passman)
		elif auth_type.lower() == "digest":
			auth = urllib2.HTTPDigestAuthHandler(passman)
		elif auth_type.lower() == "ntlm":
			# create the NTLM authentication handler
			auth =  HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)
		
		return auth
	else:
		return None

#
# Descarga el contenido de un sitio web, con o sin autenticacion, con o sin proxy
#
# Devuelve: contenido web, codigo http devuelto
#
def downloadURL(page, PARAMETERS):
	
	web_content=None
	code = 200
	auth = PARAMETERS.AUTH_USER

	opener = urllib2.build_opener()

	# proxy?
	proxy_handler = {}
	if PARAMETERS.PROXY is not None:
		proxy_handler = urllib2.ProxyHandler({'http': PARAMETERS.PROXY})
		opener.add_handler(proxy_handler)
	
	# autenticacion?
	if auth is not None:
		global Auth

		# Creacion del objeto de autenticacion, sino existe
		if Auth is None:
			user = PARAMETERS.AUTH_USER
			password = PARAMETERS.AUTH_PASS
		
			if checkIfAuth(page, PARAMETERS.PROXY) is True:
				Auth = makeAuth(page, PARAMETERS.PROXY, user, password)
				
		opener.add_handler(Auth)
	
	# Cabeceras
	opener.addheaders = [('User-agent', 'GoLISMERO/0.1')]
	opener.addheaders.append(("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"))
	
	# Agregar cookie personalizada
	if PARAMETERS.COOKIE is not None:
		opener.addheaders.append(('Cookie', PARAMETERS.COOKIE))	
	
	# Lanza la peticion y comprobamos si es valida
	try:
		f = opener.open(page, timeout=20) # 30 segundos
	except IOError, e:
		if not hasattr(e, 'code') or e.code != 200:
			return None, e.code
		if f == None:
			return None, 500
	
	# Control de errores
	if f == None:
		return None, 500
	
	# Lee el contenido de la web	
	web_content = f.read()
	
	# Cierre de las conexion
	f.close()
	opener.close()
	
	return web_content, 200