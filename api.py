#!/usr/bin/python

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


from xml.dom.minidom import parse
from libs.io_net import *
from libs.io_functions import *
from libs.checks import *
from libs.spider import *
from libs.Data import *
from libs.vulns import *



class GoLink:
	'''
		Store link info and parameters
	'''
	url = None
	params = []
	
class GoLinkParam:
	'''
		Store info for each simple links
	'''
	name = None
	value = None

class GoForm:
	'''
		Store form info as name, action and method. Also include params, if it have.
	'''
	name = None
	action = None
	method = None
	params = []
	
class GoFormParam:
	'''
		Store params for each form
	'''
	name = None
	value = None
	type = None
	
class GoFingerprint:
	'''
		Store fingerprint info.
	'''
	probability = None
	framework = None

class GoLISMERO_DATA:
	'''
	This class store info loaded from xml results generated for GoLISMERO
	'''
	site = None
	links = []
	forms = []
	fingerprint = None
	
	def __str__(self):
		
		R = ""
		
		
		try:
			
			R += self.site + "\n"

			# Links
			for i in self.links:
				url = i.url
				
				if url is None:
					url = "unknown"
				
				R +=  "|=" + url + "\n"
				
				if i.params is not None and len(i.params) > 0:
					for p in i.params:
						name = p.name
						value = p.value
						
						if name == None:
							name = "unknown"
							
						if value == None:
							value = "unknown"
							
							R +=  "|--" + name + "=" + value + "\n"
			
			# Forms
			for f in self.forms:
				name = f.name
				method = f.method
				action = f.action
				
				if name == None:
					name = "not named"
					
				if method == None:
					method = "unknown"
					
				if action == None:
					action = "unknown"
				
				R +=  "|=" + name + ": method=" + method + "|" + action + "\n"

				if f.params is not None and len(f.params) > 0:

					for fp in f.params:
						type = fp.type
						name = fp.name
						value = fp.value
		
						if type == None:
							type = "unknown"
						
						if name == None:
							name = "unknown"
							
						if value == None:
							value = "unknown"
										
						R +=  "|--(" + type + ")" + name + "=" + value + "\n"
						
			
			# Fingerprint
			if self.fingerprint is not None:
				R += "|= Application: " + self.fingerprint.framework + "as probability: " + self.fingerprint.probability + "\n"
			
		except:
			return R
		
		return R
			
			
	def loadGoLISMEROXML(self,file):
		'''
		Open and load info from a XML file generated of GoLISMERO
		'''
		dom = parse(file)

		g = GoLISMERO_DATA()
			
		for node in dom.getElementsByTagName("golismero"):
			
			for s in  node.getElementsByTagName("site"):
				self.site = s.attributes['url'].value
			
			# recuperamos los enlaces
			for l in dom.getElementsByTagName("link"):
				l_l = GoLink()
				l_l.url = l.attributes['url'].value
				
				# Busqueda de atributos
				for a in l.getElementsByTagName("param"):
					p = GoLinkParam()
					p.name = a.attributes['name'].value
					p.value = a.attributes['value'].value
					
					l_l.params.append(p)
				self.links.append(l_l)
					
		
			# recuperamos los enlaces
			for f in dom.getElementsByTagName("form"):
				l_f = GoForm()
				l_f.action = f.attributes['name'].value
				l_f.action = f.attributes['action'].value
				l_f.method = f.attributes['method'].value
				
				# Busqueda de atributos
				for a in f.getElementsByTagName("param"):
					p = GoFormParam()
					p.name = a.attributes['name'].value
					p.type = a.attributes['type'].value
					p.value = a.attributes['value'].value
					
					l_f.params.append(p)
				self.forms.append(l_f)
	
			# Fingerprint
			for fp in dom.getElementsByTagName("fingerprint"):
				l_fp = GoFingerprint()
				l_fp.framework = fp.attributes['framework'].value
				l_fp.probability = fp.attributes['probability'].value
	
				self.fingerprint = l_fp




#
# Parametros de la linea de comandos
#
class cParams:
	'''
	Command line parameters data store. Necesary for call GoLISMERO.
	'''

	def __init__(self):
		# Parametros de entrada
		self.RECURSIVITY = 0 
		self.OUTPUT_FILE = None # Fichero con los resultados
		self.TARGET = None
		self.SHOW_TYPE= None
		self.COLOR = False
		self.OUTPUT_FILE=None
		self.OUTPUT_FORMAT=None
		self.IS_NCSS=False
		self.IS_NJS=False
		self.IS_NIMG=False
		self.IS_NMAIL=False
		self.IS_N_PARAMS_LINKS = False
		self.COMPACT = False
		self.FOLLOW = False
		self.VERSION = False
		self.VULNS = False
		self.VULNS_DATA = None # Array que contiene todas la vulnerabilidades cargadas de los ficheros
		
		self.RESULTS = ""
		self.SUMMARY=False
		self.DOMAIN=None
		self.PROTOCOL=None
		self.PROXY=None
		self.COOKIE=None
		self.AUTH_USER=None
		self.AUTH_PASS=None




def GoLISMERO_Main(PARAMETERS):
	'''
		Start point to call GoLISMERO. It returns results in var "RESULTS" of object passed as parameters.
		
		@param PARAMETERS: an objecto of type cParams that contain all params for GoLISMERO execution.
		@return: None
	'''
	
	if PARAMETERS.TARGET is None:
		raise IOError("You mush specify a target (-t).")
	
	# Mostrar version
	if PARAMETERS.VERSION is True:
		raise IOError("Function not allowed on api call.")

	
	# Comprobamos opciones de autenticacion
	if (PARAMETERS.AUTH_USER is not None and PARAMETERS.AUTH_PASS is None) or (PARAMETERS.AUTH_USER is None and PARAMETERS.AUTH_PASS is not None):
		raise IOError("[!] If you want authentication you need to expecify authentication type.")
		
	elif PARAMETERS.AUTH_USER is not None and PARAMETERS.AUTH_PASS is not None:
		# Comprobamos que la autenticacion con el usuario y password funciona
		if checkAuthCredentials(PARAMETERS.TARGET, PARAMETERS.PROXY, PARAMETERS.AUTH_USER, PARAMETERS.AUTH_PASS) is False:
			raise IOError("[!] User or password are not correct and can't connect to target.")
	
	# Check proxy
	if PARAMETERS.PROXY is not None:
		if isCheckProxy(PARAMETERS.PROXY) is False:
			raise IOError("[!] Proxy format is not correct.")
		
	# Si se tienen que buscar vulnerabilidades se cargan los ficheros
	if PARAMETERS.VULNS is not None:
		PARAMETERS.VULNS_DATA = loadVulnsFiles()


	PARAMETERS.TARGET = PrepareURL(PARAMETERS.TARGET)
	PARAMETERS.DOMAIN = getDomain(PARAMETERS.TARGET)
	PARAMETERS.PROTOCOL = getProtocol(PARAMETERS.TARGET)
	
	# Crear fichero de salida, si procede
	MakeFileResults(PARAMETERS)
	
	# Ejecucion principal
	spider(PARAMETERS)

	# Write results to file
	if PARAMETERS.OUTPUT_FILE is not None:
		writeToFile(PARAMETERS)

	
