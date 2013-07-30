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

from re import finditer
from urlparse import urlparse

#
# Comprueba si una URL contiene una hoja de estilos
#
# Devuelve: True/False
def _isCheckCSS(url):
	if url is not None:
		url_parsed=urlparse(url)
		if url_parsed is not None:
			if url_parsed.path.find(".css") > 0 or url_parsed.params.find(".css") > 0:
				return True
		else:
			return False
	else:
		return False

#
# Comprueba si una URL contiene un archivo javascript
#
def _isCheckJS(url):
	if url is not None:
		url_parsed=urlparse(url)
		if url_parsed is not None:
			if url_parsed.path.find(".js") > 0 or url_parsed.params.find(".js") > 0:
				return True
		else:
			return False
	else:
		return False
	
#
# Comprueba si una URL contiene una direccion de correo
#
def _isCheckMail(url):
	if url is not None:
		if url.lower().find("mailto:") > 0:
			return True
		else:
			return False
	else:
		return False

#
# Comprueba si una URL contiene un archivo de imagen
#
def _isCheckIMG(url):
	if url is not None:
		url_parsed=urlparse(url)
		if url_parsed is not None:
			images=["jpg", "jpeg", "png", "tiff", "tif", "gif", "bmp", "svg","ico"]
			for img in images:
				if url_parsed.path.lower().find(img) > 0 or url_parsed.params.lower().find(img) > 0:
					return True
		else:
			return False
	else:
		return False


#
# Formatea los links de una web y sus parametros
#
def FormatGETLinks(link):
	Params = []
	
	i_t_text = link.find("?")+1;
	# Cogemos la parte de la derecha de la URL, a partir del "?"
	if i_t_text > 0:
		t_text=link[i_t_text:]
		
		# Extraemos los parametros
		for i in t_text.split("&"):
			j = i.split("=")
			if len(j) > 1:
				Params.append([j[0],j[1]])
			if len(j) > 0:
				Params.append([j[0],""])

	return Params


#
# Extrae el link elimiandole los parametros, quitandole el dominio, el http/https y comprobando si 
# pertenece al mismo dominio que se esta recorriendo
#
def _PrepareLink(url, target, domain):
	
	return_url=""

	#Si tiene http puede tratarse de un link externo
	if(url.lower().find("http") >= 0 or url.lower().find("https") >= 0):
		#Si contiene el dominio, no nos saldremos del site por lo que seguimos investigando
		if(url.lower().find(domain.lower()) >= 0):
			# cogermos la parte de la URL que implique solo el protolo + el dominio
			p=url.lower().find(domain.lower()) + len(domain)
			return_url = url[p:] # URL sin la parte del dominio.

	#Caso de que no contenga http y por tanto navegue dentro del site
	else:
		try:
			#Eliminamos todos los parametros que pueda haber detras del ?, para evitar bucles
			cleanUrl=url.split('?')
			if(cleanUrl[0].find('/')==0):
				url2 = cleanUrl[0]
			else:
				url2 = "/"+cleanUrl[0]					
			
			return_url=url2
			 
		except:
			pass
	
	return return_url

#
#Funcion que recupera todos los enlaces de una pagina que esten dentro del mismo dominio
#
def getLinksBackup(pageText,PARAMETERS):
	"""Recupera todos los enlaces de una pagina"""
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	isNcss = PARAMETERS.IS_NCSS
	isNjs = PARAMETERS.IS_NJS
	isNimg = PARAMETERS.IS_NIMG
	
	links = []
	
	#try:
	#Recuperamos los enlaces
	mo = finditer('href="(.*?)[\'"]', pageText)
	for url in mo:
		l_url=url.group(0).replace("'", '').replace('"', "").replace('href=', "").replace("&amp;","&").replace(" ","")

		# Si es un enlace a una pagina local
		if l_url.find("#") == 0:
			continue
		
		# Filtramos la URL a almacenar
		l_stored_url=_PrepareLink(l_url, target, domain)

		# Guardamos
		if l_stored_url is not None:
			# Comprobamos restricciones
			if isNcss == 1:
				if _isCheckCSS(l_stored_url) is False:
					links.append(l_stored_url)
			elif isNjs == 1:
				if _isCheckJS(l_stored_url) is False:
					links.append(l_stored_url)
			elif isNimg == 1:
				if _isCheckIMG(l_stored_url) is False:
					links.append(l_stored_url)
			else:
				links.append(l_stored_url)
	

	#Recuperamos los fuentes de informacion
	mo = finditer('src="(.*?)[\'"]', pageText)
	for url in mo:
		l_url=url.group(0).replace("'", '').replace('"', "").replace('src=', "").replace("&amp;","&").replace(" ","")

		# Si es un enlace a una pagina local
		if l_url.find("#") == 0:
			continue
		
		# Filtramos la URL a almacenar
		l_stored_url=_PrepareLink(l_url, target, domain)

		# Comprobamos que no es un enlace vacio

		# Guardamos
		if l_stored_url is not None:
			# Comprobamos restricciones
			if isNcss == 1:
				if _isCheckCSS(l_stored_url) is False:
					links.append(l_stored_url)
			elif isNjs == 1:
				if _isCheckJS(l_stored_url) is False:
					links.append(l_stored_url)
			elif isNimg == 1:
				if _isCheckIMG(l_stored_url) is False:
					links.append(l_stored_url)
			else:
				links.append(l_stored_url)
	
	return links
	
	#except:
		#print "Ocurrio un error: "

#
#Funcion que recupera todos los enlaces de una pagina que esten dentro del mismo dominio
#
def getLinks(pageText,PARAMETERS):
	"""Recupera todos los enlaces de una pagina"""
	
	links = []
	
	# Tipo href
	links.extend(_getLinks(pageText, 'href="(.*?)[\'"]', 'href=', PARAMETERS))
	# Tipo src
	links.extend(_getLinks(pageText, 'src="(.*?)[\'"]', 'src=', PARAMETERS))
	# Tipo data
	links.extend(_getLinks(pageText, 'data="(.*?)[\'"]', 'data=', PARAMETERS))
	return links



#
#Funcion que recupera todos los enlaces de una pagina que esten dentro del mismo dominio
#
def _getLinks(pageText,exp_reg,property,PARAMETERS):
	"""Recupera todos los enlaces de una pagina"""
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	isNcss = PARAMETERS.IS_NCSS
	isNjs = PARAMETERS.IS_NJS
	isNimg = PARAMETERS.IS_NIMG
	isNmail = PARAMETERS.IS_NMAIL
	
	links = []
	
	#try:
	#Recuperamos los enlacesproperty
	mo = finditer(exp_reg, pageText)
	for url in mo:
		l_url=url.group(0).replace("'", '').replace('"', "").replace(property, "").replace("&amp;","&").replace(" ","")

		# Si es un enlace a una pagina local
		if l_url.find("#") == 0:
			continue
		
		# Filtramos la URL a almacenar
		l_stored_url=_PrepareLink(l_url, target, domain)

		if l_stored_url == "":
			continue

		# Guardamos
		if l_stored_url is not None:
			# Comprobamos restricciones
			if isNcss is True and _isCheckCSS(l_stored_url) is True:
					continue
			elif isNjs is True and _isCheckJS(l_stored_url) is True:
					continue
			elif isNimg is True and _isCheckIMG(l_stored_url) is True:
					continue
			elif isNmail is True and _isCheckMail(l_stored_url) is True:
					continue
			else:
				links.append(l_stored_url)

	
	return links
	
	#except:
		#print "Ocurrio un error: "



