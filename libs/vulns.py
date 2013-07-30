
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

import sys
import os
import io
import mmap

def checkURLVulns(url, dicts_files):
	'''
	Comprueba si una URL puede ser vulnerable

	@return: (pos inicio coincicencia, longitud) o (-1, -1) si no hay coincidencia
	'''

	if url is not None and dicts_files is not None:
		for f in dicts_files:

			m_coincidencia = url.lower().find(f)

			# primera coincidencia pasada
			if m_coincidencia <> -1:

				m_parts = url.split('?')

				# Buscamos en la primera parte
				if len(m_parts) < 0:
					# sino tiene parametros la url ni el simbolo de '?'
					if len(url) == len(f):
						m_coincidencia = url.lower().find(f)

						return m_coincidencia, len(f)

				elif len(m_parts) > 0: # si tiene el simbolo ?

					if len(m_parts[0]) == len(f):
						m_coincidencia = url.lower().find(f)

						return m_coincidencia, len(f)

				# Buscamos en los parametros, si hay
				if len(m_parts) > 1:
					# dividimos los parametros
					m_params = m_parts[1].split("&")

					if len(m_params) > 0:
						for p in m_params:
							# Buscamos en el contenido del parametro
							c_p = p.split('=')

							if len(c_p) > 1:

								if len(f) == len(c_p[1]):

									m_coincidencia = c_p[1].lower().find(f)

									if m_coincidencia <> -1:
										# Si hay coincidencia buscamos su posicion relativa dentro de la URL
										m_coincidencia = url.lower().find(c_p[0] + "=") + len(c_p[0] + "=") # el + len() es para que solo se cuente el contenido del parametro

										return m_coincidencia, len(f)


	# Sino hay coincidencia
	return -1, -1



def loadVulnsFiles():
	'''
	Carga los diccionarios con las vulnerabilidades a partir de los ficheros.

	@return: Descriptor al fichero con las vulnerabilidades
	'''

	m_curr = os.curdir # directorio actual
	m_wordlist_dir = m_curr + "/wordlist/wfuzz/Discovery/"

	# obtenemos todos los ficheros con los diccionarios
	files = os.listdir(m_wordlist_dir)

	# Contenido de los ficheros
	output_files = []

	# Cargamos en memoria todos los ficheros
	if files is not None:
		for f in files:
			l_file = m_wordlist_dir + "/" + f
			try:

				l_f = open(l_file, "r")
				while 1:
					rl = l_f.readline()

					if not rl:
						break

					# filtramos
					s = rl.replace('\n','').replace('\r','').replace(' ','')

					if s <> "/" and s <> "":
						output_files.append(s)

				l_f.close()
			except IOError:
				continue

	return output_files


def SearchVulnsAndWriteText(URL, dicts, Start_Color):
	'''
	Comprueba si la URL pasada como parametro es vulnerable a una serie de ataques de diccionario.

	@param dicts: Fichero de memoria que contiene los diccionarios con las vulnerabilidades
	@param Start_Color: Color con el que pintar las URLs vulnerables

	@return: Devuelve la URL con el formato coloreado correcto o la URL original si no encuentra vuln
	'''

	m_pos, m_len = checkURLVulns(URL, dicts)

	# URL de retorno
	m_new_URL = ""


	if m_pos <> -1 and m_len <> -1:
		l_pos = 0
		# Posicion inicial de la coincidencia
		if m_pos == 0:
			l_pos == 0
		else:
			l_pos = m_pos - 1

		# Primera parte
		m_new_URL = URL[0:l_pos]

		# Agregamos el color
		m_new_URL += Start_Color
		# agregamos el resto de la url detectada
		m_new_URL += URL[m_pos: m_pos + m_len]

		# Cierre del color
		m_new_URL += chr(27) + "[0m"

		# Resto de la URL
		m_new_URL += URL[m_pos + m_len:]

	else:
		m_new_URL = URL

	return m_new_URL



def SearchVulnsAndWriteHTML(URL, dicts, Start_Color):
	'''
	Comprueba si la URL pasada como parametro es vulnerable a una serie de ataques de diccionario.

	@param dicts: Fichero de memoria que contiene los diccionarios con las vulnerabilidades
	@param Start_Color: Color con el que pintar las URLs vulnerables

	@return: Devuelve la URL con el formato coloreado correcto o la URL original si no encuentra vuln
	'''

	m_pos, m_len = checkURLVulns(URL, dicts)

	# URL de retorno
	m_new_URL = ""


	if m_pos <> -1 and m_len <> -1:
		l_pos = 0
		# Posicion inicial de la coincidencia
		if m_pos == 0:
			l_pos == 0
		else:
			l_pos = m_pos - 1

		# Primera parte
		m_new_URL = URL[0:l_pos]

		# Agregamos el color
		m_new_URL += Start_Color
		# agregamos el resto de la url detectada
		m_new_URL += URL[m_pos: m_pos + m_len]

		# Cierre del color
		m_new_URL += "</span>"

		# Resto de la URL
		m_new_URL += URL[m_pos + m_len:]

	else:
		m_new_URL = URL

	return m_new_URL


def isVulnsBool(URL, dicts):
	'''
	Comprueba si la URL pasada como parametro es vulnerable a una serie de ataques de diccionario.

	@param dicts: Fichero de memoria que contiene los diccionarios con las vulnerabilidades
	@param Start_Color: Color con el que pintar las URLs vulnerables

	@return: Devuelve True si es vulnerable, false en caso contrario.
	'''
	m_pos, m_len = checkURLVulns(URL, dicts)

	if m_pos <> -1 and m_len <> -1:
		return True
	else:
		return False

if __name__ == "__main__":

	a = loadVulnsFiles()
	#print str(a)

	print checkURLVulns("/on/navegacion/11822/11822-redireccion.htm", a)
