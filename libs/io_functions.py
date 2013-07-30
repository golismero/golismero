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

from Data import *
from fileresults import *
from vulns import *
import io
from libs.vulns import *




# Internas
RESULT_FILE_HANDLE = None # Descriptor fichero resultados

#
# Crear el fichero de resultados
#
def MakeFileResults(Params):
	"""Crear el fichero de resultados"""
	try:
		if Params.OUTPUT_FILE is not None:
			RESULT_FILE_HANDLE=open(Params.OUTPUT_FILE,"w")
	except:
		print "[!] No se ha podido abrir el fichero de resultados."


#
# Guarda informacion en el fichero de resultados
# WRF: Write File Results
def WRF(Text):
	try:
		if RESULT_FILE_HANDLE is not None:
			RESULT_FILE_HANDLE.writeline(Text)	
	except:
		print "[!] No se ha podido escribir en el fichero de resultados"


#
# Informacion de Debug
#
def logInfo(Text,DebugLevel):
	pass

def LogError(Text,DebugLevel):
	pass


#
# Write resultos to file with correct format
#
def writeToFile(PARAMETERS):
	
	# First check
	FILE = PARAMETERS.OUTPUT_FILE
	FORMAT = PARAMETERS.OUTPUT_FORMAT
	
	if FILE is not None and FORMAT is not None:
		FORMAT = FORMAT.lower()
		
		# Open file
		f_handle = None
		try:
			f_handle = open(FILE,"w+")
		except IOError,e:
			print "Error opening results file: " + str(e)
			return
		
		Text_to_write = ""
		if FORMAT == "text":
			 Text_to_write = SaveTextResults(PARAMETERS)
		elif FORMAT == "html":
			Text_to_write = SaveHTMLResults(PARAMETERS)
			#f_handle.writelines(SaveHTMLResults(PARAMETERS)
		elif FORMAT == "csv":
			Text_to_write = SaveCSVResults(PARAMETERS)
		elif FORMAT == "scripting":
			Text_to_write = SaveSCRIPTINGResults(PARAMETERS)
		elif FORMAT == "wfuzz":
			Text_to_write = SaveWFUZZResults(PARAMETERS)
		elif FORMAT == "xml":
			Text_to_write = SaveXMLResults(PARAMETERS)
		else:
			print "Format not correct!"
		
		f_handle.write(Text_to_write.encode('ascii','xmlcharrefreplace')) # codificamos para evitar posteriores errores
		f_handle.close()
		

#
# Presentar resultados en pantalla
#
def ShowScreenResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	isCompact=PARAMETERS.COMPACT
	isVulns = PARAMETERS.VULNS
	
	if Resultados is None and Resultados is not cResults:
		print "No results to print."
		return
		
	# Console colors
	LINKS = ""
	METHODS = ""
	TYPE = ""
	END_COLOR = ""
	if PARAMETERS.COLOR is True:
		LINKS = chr(27) + COLOR_BLUE
		METHODS = chr(27) + COLOR_YELLOW
		TYPE = chr(27) + COLOR_RED
		END_COLOR = chr(27) + "[0m"
		
	# Para cada objeto del tipo cResults
	total_links = 0
	total_forms = 0
	verbose_resume = [] # variable para controlar el sumario largo: [form num,vars,war params]
	for l_r in Resultados:
		print ""
		print "[ " + l_r.URL + " ]"
		
		# Links

		if show_type == "links" or show_type == "all":
			
			print ""
			print "  Links"
			print "  ====="
				
			lnk_num=1
			for l_l in l_r.Links:
				if l_l is None:
					continue
				
				
				
				# hay que buscar vulnerabilidades?
				l_url = l_l.URL
				if isVulns is True:
					l_url = SearchVulnsAndWriteText(l_url, PARAMETERS.VULNS_DATA, TYPE)
			
					# Si coinciden es que no se ha encontrando y coloreamos normalmente
					if l_url == l_l.URL:
						l_url = LINKS + l_l.URL + END_COLOR
				
				
				# Mostramos el link
				print "  [L" + str(lnk_num) + "] " + l_url 
				
				# Sino se ha pedido el modo compato
				if isCompact is False:
					for l_d in l_l.Params:
						if l_d[0] == "password" or l_d[0].lower().find("pass") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0:
							print "        | " + TYPE + l_d[0] + END_COLOR + " = " + l_d[1]
						else:
							print "        | " + l_d[0] + " = " + l_d[1]
				
				
				if len(l_l.Params) > 0:
					print "        | Raw:"
					
					# Modo Raw
					params = ""
					for l_d in l_l.Params:
						params +=l_d[0] + "=" + l_d[1] + "&"
					
					# Eliminamos el ultimo "&"
					params=params[0:len(params)-1]
					
					# resultados
					print "        | " + params
	
				lnk_num += 1
				total_links += 1
			
			print ""
		
		# Forms
		if show_type == "forms" or show_type == "all":
			print ""
			print "  Forms"
			print "  ====="
			frm_num = 1
			for l_f in l_r.Forms:
				print "  [F" + str(frm_num) + "] " + l_f.Name
				print "      | Method: " + METHODS + l_f.Method.upper() + END_COLOR
					
				# hay que buscar vulnerabilidades?
				l_target = l_f.Target
				if isVulns is True:
					l_target = SearchVulnsAndWriteText(l_url, PARAMETERS.VULNS_DATA, TYPE)
					# Si coinciden es que no se ha encontrando y coloreamos normalmente
					if l_target == l_f.Target:
						l_target = LINKS + l_f.Target  + END_COLOR
				
				
				print "      | Target: "  + l_target
				print "      |",
				print "-" * (len(l_f.Target) + len(l_f.Method.upper()) + 5)
				
				# Form params
				war_params = 0
				
				for l_d in l_f.Params:
					#	[type] Name | value  
					if l_d[2].lower() == "password":
						war_params +=1
						# Sino se ha pedido el modo compato
						if isCompact is False:
							print "      | ["+ TYPE + l_d[2] + END_COLOR + "] " + l_d[0] + " = " + l_d[1]
					elif  l_d[2].lower() == "text" and  (l_d[0].lower().find("usuario") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0 ):
						war_params +=1
						# Sino se ha pedido el modo compato
						if isCompact is False:
							print "      | ["+ l_d[2] + "] " + TYPE + l_d[0] + END_COLOR + " = " + l_d[1]
					else:
						# Sino se ha pedido el modo compato
						if isCompact is False:
							print "      | ["+ l_d[2] + "] " + l_d[0] + " = " + l_d[1]

				# Parametros en crudo
				if isCompact is False:
					print "      |",
					print "-" * (len(l_f.Target) + len(l_f.Method.upper()) + 5)
					
				print "      | Raw:"
				print "       ",
				raw_params = ""
				for l_d in l_f.Params:
					raw_params+=l_d[0] + "=" + l_d[1] + "&"				
				# Eliminamos el ultimo &
				raw_params=raw_params[0:len(raw_params)-1]
				print raw_params,				
				print ""
				
				# Actualizar sumario verboso
				verbose_resume.append([frm_num,len(l_f.Params),war_params])

				frm_num += 1
				total_forms += 1
				
			# Separador entre URLs
			print ""
		
		
		print "Total links: " + str(total_links)
		print "Total Forms: " + str(total_forms)

		if PARAMETERS.SUMMARY is True:
			for f in verbose_resume:
				print "         |- Form: [F" + str(f[0]) + "]\t\tParams: " + str(f[1]) + "\tDangerous params: " + str(f[2]) 
		print ""

