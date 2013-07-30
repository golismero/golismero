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


COLOR_RED = "[1;91m"
COLOR_YELLOW = "[0;93m"
COLOR_BLUE = "[4;94m" # Enlaces subrallados y azules


#
# Parametros de la linea de comandos
#
class cParams:

	def __init__(self):
		# Parametros de entrada
		self.RECURSIVITY = 0 
		self.OUTPUT_FILE = None # Fichero con los resultados
		self.TARGET = None
		self.SHOW_TYPE= None
		self.COLOR = None
		self.OUTPUT_FILE=None
		self.OUTPUT_FORMAT=None
		self.IS_NCSS=None
		self.IS_NJS=None
		self.IS_NIMG=None
		self.IS_NMAIL=None
		self.IS_N_PARAMS_LINKS=None
		self.COMPACT = None 
		
		self.RESULTS = ""
		self.SUMMARY=None
		self.DOMAIN=None
		self.PROTOCOL=None
		self.PROXY=None
		self.COOKIE=None
		self.AUTH_USER=None
		self.AUTH_PASS=None

#
# Form data structure
#
class cForm:
	"""Structure to store From info"""
	
	def __init__(self):
		self.Name = "No name"
		self.Method = "GET"
		self.Target = "No specified"
		self.Params = []

class cLink:
	"""Structure to store links"""
	
	def __init__(self):
		self.URL = "No name" # Donde apunta el Link
		self.Params = []

		

class cResults:
	"""Structure to store all results"""
	
	def __init__(self):
		self.URL = ""
		self.Links=[]
		self.Forms=[]
		
	def Order(self):
		"""Ordena la lista de resultados"""
		self.Links=sorted(self.Links, key=lambda link: link.URL)
		self.Forms=sorted(self.Forms, key=lambda form: form.Name)
		