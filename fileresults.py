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

#
# Guarda resultados en HTML
#
def SaveHTMLResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	protocol = PARAMETERS.PROTOCOL
	
	WR = """
		<html>
			<head>
				<title>Results</title>
				<style>
					body { background-color: Black; color: White; }
					.red { color: Red; }
					.yellow { color: Yellow; }
					.blue { color: Blue; }
				</style>
			</head>
			<body>
		"""
	
	
	
	if Resultados is None and Resultados is not cResults:
		WR += "No results to save."
		return
	
		
	# Para cada objeto del tipo cResults
	total_links = 0
	total_forms = 0
	verbose_resume = [] # variable para controlar el sumario largo: [form num,vars,war params]
	for l_r in Resultados:

		WR +=  "<h1> [" + l_r.URL + " ] </h1>\n"
		
		# Links

		if show_type == "links" or show_type == "all":
			WR +=  "\n"
			WR +=  "  <h2>Links</h2>\n"
			WR +=  "  <hr />\n"
			WR +=  "<ul>\n"
			lnk_num=1
			for l_l in l_r.Links:
				if l_l is None:
					continue
				
				WR +=" 	<li>\n"
				WR +=  "<a href='" + target + l_l.URL + "'>[" + str(lnk_num) + "] " + l_l.URL + "</a>\n"
				
				
				if len(l_l.Params) > 0:
					WR += "<ul>\n"
				
				for l_d in l_l.Params:
					
					if l_d[0] == "password" or l_d[0].lower().find("pass") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0:
						WR +=  "<li class='Red'>" + l_d[0] + " = " + l_d[1] + "</li>\n"
					else:
						WR +=  "<li>      | " + l_d[0] + " = " + l_d[1] + "</li>\n"
	
				
				if len(l_l.Params) > 0:
					WR += "</ul>\n"
	
				WR +=" 	</li>\n"
				
				lnk_num += 1
				total_links += 1
				
			WR +=  "</ul>\n"
			WR +=  "\n"
		
		# Forms
		if show_type == "forms" or show_type == "all":
			WR +=  "\n"
			WR +=  "  <h2>Forms</h2>\n"
			WR +=  "  <hr />\n"
			
			frm_num = 1
			for l_f in l_r.Forms:
				
				pre_url = protocol + "://" + domain
				
				# Enlaces, si es del tipo GETS
				if l_f.Method.lower() == "get":
					
					if l_f.Target.find("/") <> 0: # Si comienza con la "/" no la agregamos a mano
						pre_url += "/"
						
					pre_url += l_f.Target
					
					if l_f.Target.find("?") == -1: # Si no contiene el simbolo se agrega, sino el resto son parametros nuevos
						pre_url += "?"
					else:
						pre_url +="&"
						
					for p in l_f.Params:
						pre_url += p[0] + "=" + p[1] + "&"
					
					# Eliminamos el ultimo "&"
					pre_url=pre_url[0:len(pre_url)-1]
					
					WR += "<h3>  [" + str(frm_num) + "] <a href='" + pre_url + "'>" +  l_f.Name + "</a></h3>\n"
				else:
					WR +=  "<h3>  [" + str(frm_num) + "] " + l_f.Name + "</h3>\n"
					
				WR +=  "<ul>"
				WR +=  "<li>Method: <span class='yellow'>" + l_f.Method.upper() + "</span></li>\n"
				WR +=  "<li>Target: <span class='blue'><a href='"  + pre_url + "' >"  + l_f.Target + "</a></span></li>\n"
				WR += "<hr />"
					
				if len(l_f.Params) > 0:
					WR += "<ul>\n"		
				
				war_params = 0
				
				# Form params
				for l_d in l_f.Params:
					#	[type] Name | value  
					if l_d[2].lower() == "password":
						war_params +=1
						WR +=  "<li> [<span class='red'>" + l_d[2] + "</span>] " + l_d[0] + " = " + l_d[1] + "</li>\n"
					elif  l_d[2].lower() == "text" and  (l_d[0].lower().find("usuario") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0 ):
						war_params +=1
						WR +=  "<li> ["+ l_d[2] + "] <span class='red'>" + l_d[0] + "</span> = " + l_d[1] + "</li>\n"
					else:
						WR +=  "<li> ["+ l_d[2] + "] " + l_d[0] + " = " + l_d[1] + "</li>\n"

				# Actualizar sumario verboso
				verbose_resume.append([frm_num,len(l_f.Params),war_params])

				frm_num += 1
				total_forms += 1

				if len(l_f.Params) > 0:
					WR += "</ul>\n"
				
				WR +=  "</ul>"
			# Separador entre URLs
			WR += "\n"
			
		WR += "\n"
		

		WR +=  "<p>Total links: " + str(total_links) + "</p>\n"
		WR +=  "<p>Total Forms: " + str(total_forms) + "</p>\n"

		if PARAMETERS.SUMMARY is True:
			WR += "<ul>"
			for f in  verbose_resume:
				WR += "<li>Form: [F" + str(f[0]) + "]\t\tParams: " + str(f[1]) + "\tDangerous params: " + str(f[2]) + "</li>"
			WR += "</ul>" 
		WR += """
			</body>
			</html>
		
			"""

	return WR



#
# Guarda los resultados en XML
#
def SaveXMLResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	protocol = PARAMETERS.PROTOCOL
	
	WR = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n"
	WR = "<golismero>\n"
	
	
	
	if Resultados is None and Resultados is not cResults:
		WR += "   <error>No results to save.</error>"
		return
	
		
	# Para cada objeto del tipo cResults
	for l_r in Resultados:

		WR +=  "   <site url='" + l_r.URL + "' />\n"
		
		# Links
		if show_type == "links" or show_type == "all":
			WR +=  "   <links>\n"
			
			# Para cada link
			for l_l in l_r.Links:
				if l_l is None:
					continue
				
				WR += "      <link url='" + target + l_l.URL + "'>\n"

				for l_d in l_l.Params:
					WR +=  "	     <param name='" + l_d[0] + "' value='" + l_d[1] + "' />\n"
				
				WR += "      </link>\n"
			WR +=  "   </links>\n"
		
		# Forms
		if show_type == "forms" or show_type == "all":

			WR +=  "   <forms>\n"
			
			# Para cada formulario
			for l_f in l_r.Forms:
				
				# Creacion del URL completa
				long_action = ""
				if l_f.Target.replace(protocol + "://","").find(domain) != 0: # Si el action/target y el dominio es diferente
					long_action = protocol + "://" + l_f.Target # URL completa
				else:
					long_action = protocol + "://" + domain + l_f.Target # URL completa
				
				WR += "      <form name='%s' action='%s' method='%s' >\n" % (l_f.Name, long_action, l_f.Method) 

				
				# Form params
				for l_d in l_f.Params:
					WR +=  "         <param name='%s' value='%s' type='%s' />\n" %  (l_d[0], l_d[2], l_d[2])
				WR += "      </form>\n"

			WR +=  "   </forms>\n"
	
	
	WR += "   <fingerprint probability="" framework="">" # por implementar 
	WR += "</golismero>\n"

	return WR


		
#
# Guarda resultados en modo texto
#
def SaveTextResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	
	WR = "" # definir la variable
	
	if Resultados is None and Resultados is not cResults:
		WR += "No results to save."
		return
	
		
	# Para cada objeto del tipo cResults
	total_links = 0
	total_forms = 0
	verbose_resume = [] # variable para controlar el sumario largo: [form num,vars,war params]
	for l_r in Resultados:
		WR += "\n"
		WR +=  "[ " + l_r.URL + " ]\n"
		
		# Links

		if show_type == "links" or show_type == "all":
			WR +=  "\n"
			WR +=  "  Links\n"
			WR +=  "  =====\n"
			lnk_num=1
			for l_l in l_r.Links:
				if l_l is None:
					continue
				
				WR +=  "  [" + str(lnk_num) + "] " + l_l.URL + "\n"
				
				for l_d in l_l.Params:
					if l_d[0] == "password" or l_d[0].lower().find("pass") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0:
						WR +=  "      | +++" + l_d[0] + "+++ = " + l_d[1] + "\n"
					else:
						WR +=  "      | " + l_d[0] + " = " + l_d[1] + "\n"
	
				lnk_num += 1
				total_links += 1
			
			WR +=  "\n"
		
		# Forms
		if show_type == "forms" or show_type == "all":
			WR +=  "\n"
			WR +=  "  Forms\n"
			WR +=  "  =====\n"
			frm_num = 1
			for l_f in l_r.Forms:
				WR +=  "  [" + str(frm_num) + "] " + l_f.Name + "\n"
				WR +=  "      | Method: " + l_f.Method.upper() + "\n"
				WR +=  "      | Target: "  + l_f.Target + "\n"
				WR += "      |"
				WR += "-" * (len(l_f.Target) + len(l_f.Method.upper()) + 5) + "\n"
							
				war_params = 0
				
				# Form params
				for l_d in l_f.Params:
					#	[type] Name | value  
					if l_d[2].lower() == "password":
						war_params +=1
						WR +=  "      | [+++" + l_d[2] + "+++] " + l_d[0] + " = " + l_d[1] + "\n"
					elif  l_d[2].lower() == "text" and  (l_d[0].lower().find("usuario") > 0 or l_d[0].lower().find("user") > 0 or l_d[0].lower().find("name") > 0 ):
						war_params +=1
						WR +=  "      | ["+ l_d[2] + "] +++" + l_d[0] + "+++ = " + l_d[1] + "\n"
					else:
						WR +=  "      | ["+ l_d[2] + "] " + l_d[0] + " = " + l_d[1] + "\n"

				# Parametros en crudo
				WR +=  "      |"
				WR +=  "-" * (len(l_f.Target) + len(l_f.Method.upper()) + 5)
				WR +=  "\n"
				WR +=  "      | Raw:\n"
				WR +=  "        "
				raw_params = ""
				for l_d in l_f.Params:
					raw_params+=l_d[0] + "=" + l_d[1] + "&"				
				# Eliminamos el ultimo &
				raw_params=raw_params[0:len(raw_params)-1]
				WR +=  raw_params 
				WR += "\n"			

				# Actualizar sumario verboso
				verbose_resume.append([frm_num,len(l_f.Params),war_params])

				frm_num += 1
				total_forms += 1
				
			# Separador entre URLs
			WR += "\n"

		WR +=  "Total links: " + str(total_links) + "\n"
		WR +=  "Total Forms: " + str(total_forms) + "\n"
		
		if PARAMETERS.SUMMARY is True:
			for f in verbose_resume:
				print "         |- Form: [F" + str(f[0]) + "]\t\tParams: " + str(f[1]) + "\tDangerous params: " + str(f[2])

	return WR

#
# Guarda los resultados en formato CSV
#
def SaveCSVResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	protocol = PARAMETERS.PROTOCOL
	
	WR = "" # definir la variable
	
	if Resultados is None and Resultados is not cResults:
		WR += "# No results to save.\n\r"
		return
	
		
	# Para cada objeto del tipo cResults
	
	for l_r in Resultados:
		# Links

		if show_type == "links" or show_type == "all":
			WR += "# LINKS\n\r"
			WR += "# link,param1=value1:param2=value2:param3=value3:...\n\r"

			for l_l in l_r.Links:
				if l_l is None:
					continue
			
				pre_url = protocol + "://" + domain				
				if l_l.URL.find("/") <> 0: # Si comienza con la "/" no la agregamos a mano
					pre_url += "/"
				
				WR += "\"" + pre_url + l_l.URL.replace(",","\,") + "\","
				
				WR += "\""
				tmp= ""
				for l_d in l_l.Params:
					tmp += l_d[0].replace(",","\,").replace(":","\:") + "=" + l_d[1].replace(",","\,").replace(":","\:") + ":"
				
				# Eliminar el ultimo ":"
				tmp=tmp[0:len(tmp)-1]
				WR+=tmp
				WR += "\"\n\r"

		
		# Forms
		if show_type == "forms" or show_type == "all":
			WR += "# FORMS\n\r"
			WR += "# Form name,Method,Action,param1=value1:param2=value2:param3=value3:...,'param1=value1&param2=valu2...'\n\r"

			for l_f in l_r.Forms:
				
				# Name
				WR += "\"" + l_f.Name.replace(",","\,") + "\","
				# Method
				WR += "\"" + l_f.Method.upper() .replace(",","\,") + "\","				
				
				# Target
				if l_f.Method.lower() == "get":
					pre_url = protocol + "://" + domain				
					if l_f.Target.find("/") <> 0: # Si comienza con la "/" no la agregamos a mano
						pre_url += "/"
						
					pre_url += l_f.Target
					
					if l_f.Target.find("?") == -1: # Si no contiene el simbolo se agrega, sino el resto son parametros nuevos
						pre_url += "?"
					else:
						pre_url +="&"
						
					for p in l_f.Params:
						pre_url += p[0] + "=" + p[1] + "&"
						
					WR += "\"" + pre_url.replace(",","\,") + "\","
				else:		
					WR += "\"" + l_f.Target.replace(",","\,") + "\","
								
				WR += "\""
				tmp= ""
				for l_d in l_l.Params:
					tmp += l_d[0].replace(",","\,").replace(":","\:") + "=" + l_d[1].replace(",","\,").replace(":","\:") + ":"
				
				# Eliminar el ultimo ":"
				tmp=tmp[0:len(tmp)-1]
				WR+=tmp				 
				
				raw_params = ""
				for l_d in l_f.Params:
					raw_params+=l_d[0] + "=" + l_d[1] + "&"				
				# Eliminamos el ultimo &
				raw_params=raw_params[0:len(raw_params)-1]
				WR +=",\"" + raw_params + "\""
				WR += "\"\n\r"


	return WR

#
# Genera script para lanzar el WFUZZ
#
def SaveWFUZZResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	protocol = PARAMETERS.PROTOCOL
	
	WR = "" # definir la variable
	
	if Resultados is None and Resultados is not cResults:
		WR += "# No results to save.\n\r"
		return
	
		
	# Para cada objeto del tipo cResults
	
	links = 1
	forms = 1
	for l_r in Resultados:
		# Links

		if show_type == "links" or show_type == "all":
			WR += "#\n"
			WR += "# LINKS\n"
			WR += "#\n"
			
			for l_l in l_r.Links:
				if l_l is None:
					continue
			
				WR += "# Link " + str(links) + "\n"
			
				pre_url = protocol + "://" + domain + l_l.URL + "?"
			
				tmp= ""
				if len(l_l.Params) > 0:
					for l_d in l_l.Params:
						tmp += l_d[0] + "=FUZZ&"
					
					# Eliminar el ultimo ":"
					tmp=tmp[0:len(tmp)-1]
				else:
					tmp += "FUZZ"
	
				# Creacion del comando
				WR += "wfuzz -c -o html -z file,wordlist/WORD_LIST --hc 302,400,401,404,500,XXX " + pre_url + tmp + "\n"
				
				links += 1
		
		# Forms
		if show_type == "forms" or show_type == "all":
			WR += "#\n"
			WR += "# FORMS\n"
			WR += "#\n"

			for l_f in l_r.Forms:
				
				#if l_f.Target.lower().find("no action") > 0:
				#	continue
				
				# Name
				WR += "# Form "+ l_f.Name + "\n"
				
				# Action
				pre_url = ""
				if l_f.Method.lower() == "get":
					
					# Creacion del URL completa
					if l_f.Target.replace(protocol + "://","").find(domain) != 0: # Si el action/target y el dominio es diferente
						pre_url = protocol + "://" + l_f.Target # URL completa
					else:
						pre_url = protocol + "://" + domain + l_f.Target # URL completa
						
					# Si no contiene el simbolo "?" se agrega, sino solo el resto son parametros nuevos
					if l_f.Target.find("?") == -1: 
						pre_url += "?"
					else:
						pre_url +="&"
				
				else: # Tipo post
					pre_url = protocol + "://" + domain 
				
				# Extraccion de parametros
				param = ""
				for l_d in l_f.Params:
					param += l_d[0] + "=FUZZ&" 
				# Eliminar el ultimo "&"
				param=param[0:len(param)-1]				 
				
				# Creacion de los comandos
				if l_f.Method.lower() == "get":
					WR += "wfuzz -c -o html -z file,wordlist/WORD_LIST --hc 302,400,401,404,500,XXX " + pre_url + param + "\n"
				else:
					WR += "wfuzz -c -o html -z file,wordlist/WORD_LIST -d \"" + param + "\" --hc 302,400,401,404,500,XXX " + pre_url + "\n"
	return WR

#
# Genera salida que facilitar el scripting
#
def SaveSCRIPTINGResults(PARAMETERS):
	
	Resultados=PARAMETERS.RESULTS
	show_type=PARAMETERS.SHOW_TYPE
	target = PARAMETERS.TARGET
	domain = PARAMETERS.DOMAIN
	protocol = PARAMETERS.PROTOCOL
	
	WR = "" # definir la variable
	
	if Resultados is None and Resultados is not cResults:
		WR += "# No results to save.\n\r"
		return
	
		
	# Para cada objeto del tipo cResults
	
	for l_r in Resultados:
		# Links

		if show_type == "links" or show_type == "all":

			for l_l in l_r.Links:
				if l_l is None:
					continue
				
				WR += "L\t"
			
				pre_url = protocol + "://" + domain				
				if l_l.URL.find("/") <> 0: # Si comienza con la "/" no la agregamos a mano
					pre_url += "/"
				
				WR += pre_url + l_l.URL.replace(",","\,") + "\t"
				
				tmp= ""
				for l_d in l_l.Params:
					tmp += l_d[0].replace(",","\,").replace(":","\:") + "=" + l_d[1].replace(",","\,").replace(":","\:") + ":"
				
				# Eliminar el ultimo ":"
				tmp=tmp[0:len(tmp)-1]
				WR+=tmp
				WR += "\n"

		
		# Forms
		if show_type == "forms" or show_type == "all":

			for l_f in l_r.Forms:
				
				WR += "F\t"
				
				# Name
				WR += l_f.Name.replace(",","\,") + "\t"
				# Method
				WR += l_f.Method.upper() .replace(",","\,") + "\t"				
				
				# Target
				if l_f.Method.lower() == "get":
					pre_url = protocol + "://" + domain				
					if l_f.Target.find("/") <> 0: # Si comienza con la "/" no la agregamos a mano
						pre_url += "/"
						
					pre_url += l_f.Target
					
					if l_f.Target.find("?") == -1: # Si no contiene el simbolo se agrega, sino el resto son parametros nuevos
						pre_url += "?"
					else:
						pre_url +="&"
						
					for p in l_f.Params:
						pre_url += p[0] + "=" + p[1] + "&"
						
					WR += pre_url.replace(",","\,") + "\t"
				else:		
					WR += l_f.Target.replace(",","\,") + "\t"
								

				tmp= ""
				for l_d in l_l.Params:
					tmp += l_d[0].replace(",","\,").replace(":","\:") + "=" + l_d[1].replace(",","\,").replace(":","\:") + ":"
				
				# Eliminar el ultimo ":"
				tmp=tmp[0:len(tmp)-1]
				WR+=tmp				 
				WR += "\n"


	return WR