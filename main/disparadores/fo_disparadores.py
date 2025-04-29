from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
from objects.fo_obj_email import ConfiguracionEmail
import os

def do_on_facture_optimus(tenants,tenant_path):
    tenant_id = input("Ingrese el ID del tenant a ejecutar: ").strip()
    if(tenant_id== "0"):
        return
    tenant_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build","tenant",tenant_id,"email.json")
    configuracionEmail = ConfiguracionEmail(tenant_file)
    configuracionEmail.cargar_configuracion()
    if(configuracionEmail.find is False):
        return
    else:
        month = input("Ingrese el MES: ")
        year = input("Ingrese el YEAR : ")
        subFolderDate= str(month)+str("_")+str(year)
        email=configuracionEmail.obtener_config_email()
        do_on_start(subFolderDate,int(month),int(year),email,tenant_id)
        do_on_start_extract_facturacion(subFolderDate,tenant_id)