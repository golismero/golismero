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

from forms import *
from io_functions import *
from Links import *
from Data import *
from io_net import *


RESULTADOS=[]
global gParameters

# URLS
linksVisited = []
linksParams = []
linksAlreadyStored = []



def spider(Parameters):
	
	global gParameters
	gParameters=Parameters

	_spider(Parameters.TARGET, Parameters.RECURSIVITY)
	
	Parameters.RESULTS = RESULTADOS
	

#
# Funcion que recorre una Web en busca de links con parametros pasados por get con ?
#
def _spider(page,level):
	"""Recorre una Web en busca de links con parametros pasados por get con ?"""

	# Chequeo de recursividad
	if(level < 0 or page == None):
		return
	
	global gParameters
	
	# descargar pagina
	pageraw,http_code = downloadURL(page, gParameters)
	
	# Chequeo de que se ha podido obtener la web
	#if http_code != 200:
	#	return
	
	# Comprobamos errores 
	if pageraw is None or http_code is None:
		return


	# Estructura de resultados
	R_T = cResults()
	
	# Pagina testeada
	R_T.URL = page
	
	# Recuperar los enlaces de una pagina
	m_links=getLinks(pageraw, gParameters)
	
	# Extrae info de los formularios formularios
	if gParameters.SHOW_TYPE == "forms" or gParameters.SHOW_TYPE == "all":
		R_T.Forms.extend(getFormInfo(pageraw))
		
	# Extrae info de los enlaces
	if gParameters.SHOW_TYPE == "links" or gParameters.SHOW_TYPE == "all":
		if m_links is not None:
			for l_l in m_links:
				if l_l not in linksAlreadyStored:
					# Store link
					linksAlreadyStored.append(l_l)
					
					# Extraccion de los enlaces 
					# Comprobamos si el enlace tiene parametros
					Params = FormatGETLinks(l_l)
					
					# Esta marcada la opcion de no almacenar los enlaces sin parametros?
					if gParameters.IS_N_PARAMS_LINKS is True:
						if len(Params) > 0:
							c_l = cLink()
							c_l.URL = l_l
							c_l.Params = Params
							# Agregamos a los resultados
							R_T.Links.append(c_l)
					else: # sino lo almacenamos todo
						c_l = cLink()
						c_l.URL = l_l
						c_l.Params = Params
						# Agregamos a los resultados
						R_T.Links.append(c_l)
						
	
	RESULTADOS.append(R_T)
	
	#Recuperamos los enlaces
	if m_links is not None:
		for url in m_links:
			# Si no ha sido ya visitada ejecutamos
			if(url not in linksVisited):
				#Marcamos la web como visitada
				linksVisited.append(url)
				
				# Comprobamos esta dentro del directorio de la URL pasada como parametro
				if url.find(gParameters.TARGET) < 0:
					continue
				
				# Filtrado y preparado del link
				spider_url= gParameters.TARGET + url
				
				# Recursion para seguir la busqueda
				_spider(spider_url, int(level) - 1)