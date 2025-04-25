from lxml import etree
import os
import re
from bussines.tcProcesFacturacion import extraer_datos_factura
from bussines.tcEmail import primer_dia_del_mes
from bussines.tcEmail import primer_dia_del_siguiente_mes
from bussines.tcEmail import ultimo_dia_del_mes

fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","peajes","ad090047025200025008b3f11.xml")
#fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","peajes","ad090047025200025008b3ae8.xml")

print("FIe XMl: ",fileXml)
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)

#print("Find Facturas desde ",primer_dia_del_mes(3,2025)," hasta ",primer_dia_del_siguiente_mes(3,2025))
#print("Find Facturas desde ",primer_dia_del_mes(3,2025)," hasta ",ultimo_dia_del_mes(3,2025))

#current_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#print("ruta relativa de ejecucion: ",current_directory)

#Test of facture another type 
'''
fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","facturas","ad08000156150602500561731.xml")
print("FIe XMl: ",fileXml)
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)


fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","facturas","ad09004214160002500040358.xml")
print("FIe XMl: ",fileXml)
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)
'''