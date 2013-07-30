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
from bs4 import *

	
#
# Obtiene todos los datos de un formulario
#
def ExtractFormsInfo(text):
	"""Obtiene las propiedades de un formulario"""
		
	bs=BeautifulSoup(text)
	a=bs.findAll("form")
	
	results = []
	
	for f in a:

		# Propiedades del formulario
		m_res = cForm() 
		
		if 'name' in f.attrs:
			m_res.Name = f.attrs['name']
		else:
			m_res.Name = "form unnamed"

		if 'action' in f.attrs:
			m_res.Target = f.attrs['action'].replace(" ","")
		else:
			m_res.Target = "No action"				
			
		if 'method' not in f.attrs:
			m_res.Method = 'GET'
		else:
			m_res.Method = f.attrs['method']

		
		#
		# Los input
		#
		for sf in f.findAll('input'):
			
			if 'name' in sf.attrs:
				if 'value' in sf.attrs:
					m_value = sf.attrs['value']
				else:
					m_value = ""

				if 'type' in sf.attrs:
					m_type = sf.attrs['type']
				else:
					m_type = "No info"
									
				m_res.Params.append([sf.attrs['name'], m_value, m_type])
				
		results.append(m_res)
		
	return results



#
# Recupera y formatea el contenido de un formularios
#
def getFormInfo(Text):
	"""Recupera y formatea el contenido de un formularios"""
	m_Results = []
	
	if Text is not None:
		# Obtenemos la lista de formularios
		m_Results = ExtractFormsInfo(Text)

		
	return m_Results	




