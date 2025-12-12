from lxml import etree
import os
import re
from bussines.tcProcesFacturacion import extraer_datos_factura
from bussines.tcEmail import primer_dia_del_mes
from bussines.tcEmail import primer_dia_del_siguiente_mes
from bussines.tcEmail import ultimo_dia_del_mes

#fileXml = os.path.join(os.getcwd(), "testXml","ad0900470252000250081eac8.xml")
#factura_id, texto_factura = extraer_datos_factura(fileXml)
#print(texto_factura)

print("Find Facturas desde ",primer_dia_del_mes(3,2025)," hasta ",primer_dia_del_siguiente_mes(3,2025))
print("Find Facturas desde ",primer_dia_del_mes(3,2025)," hasta ",ultimo_dia_del_mes(3,2025))
