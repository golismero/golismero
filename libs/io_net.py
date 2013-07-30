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
import cookielib

global Auth
Auth = None # Autenticacion ya realizada. Para evitar hacer muchas peticiones

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
# MAX_FOLLOW: Variable para controlar el numero maximo de redirecciones que sigue y evitar
#             bucles infinitos
def downloadURL(page, PARAMETERS, MAX_FOLLOW = 3):

	if MAX_FOLLOW < 0:
		return None, None

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
	f = None
	try:
		f = opener.open(page, timeout=20) # 30 segundos


		# Seguimos las redirecciones
		if f.code == 302:
			if PARAMETERS.FOLLOW is True:
				return downloadURL(f.headers['Location'], PARAMETERS,MAX_FOLLOW - 1)

	except urllib2.HTTPError, e:
		if not hasattr(e, 'code') or e.code != 200:
			print "[!] Error fetching URL: " + str(e)
			return None, None
		if f == None:
			print "[!] Error fetching URL: " + str(e)
			return None, None

	except IOError, e:
		if not hasattr(e, 'code') or e.code != 200:
			print "[!] Error fetching URL: " + str(e)
			return None, None
		if f == None:
			print "[!] Error fetching URL: " + str(e)
			return None, None

	# Control de errores
	if f == None:
		return None, None

	# Lee el contenido de la web
	web_content = f.read()

	# Cierre de las conexion
	f.close()
	opener.close()

	return web_content, 200