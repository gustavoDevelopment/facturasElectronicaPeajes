from lxml import etree
import os
import re
from bussines.tcProcesFacturacion import extraer_datos_factura
from bussines.tcEmail import primer_dia_del_mes
from bussines.tcEmail import primer_dia_del_siguiente_mes
from bussines.tcEmail import ultimo_dia_del_mes
from objects.fo_obj_email import ConfiguracionEmail
from objects.fo_obj_plantilla import do_on_get_columns
from bussines.tcCausar import crear_archivo_excel_con_cabecera


#fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","peajes","ad090047025200025008b3f11.xml")
#fileXml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test","peajes","ad090047025200025008b3ae8.xml")

#print("FIe XMl: ",fileXml)
#factura_id, texto_factura = extraer_datos_factura(fileXml)
#sprint(texto_factura)

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

#tenant_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build","tenant","af657458-4160-48c0-bc95-a53d9da18df0","email.json")
#print("Tenant File Email Exists",tenant_file,os.path.exists(tenant_file))
#configuracionEmail = ConfiguracionEmail(tenant_file)
#configuracionEmail.cargar_configuracion()
#email=configuracionEmail.obtener_config_email()
#print("Email: ",email)

tenant_id = "test"
plantilla_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "build",
        "tenant",
        tenant_id,
        "plantilla.json"
    )
cabeceras=do_on_get_columns(plantilla_file)
print(os.path.dirname( os.path.abspath(__file__)))
crear_archivo_excel_con_cabecera(os.path.dirname( os.path.abspath(__file__)),"unitTest",tenant_id,cabeceras)


