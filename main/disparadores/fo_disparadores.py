from bussines.tcEmail import do_on_start, contar_zips
from bussines.paths import tenant_work_dir
from bussines.reporter import ConsoleReporter
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
from objects.fo_obj_email import ConfiguracionEmail
from config import tenant_email_path

def do_on_facture_optimus(tenants,tenant_path):
    tenant_id = input("Ingrese el ID del tenant a ejecutar: ").strip()
    if(tenant_id== "0"):
        return
    tenant_file = tenant_email_path(tenant_id)
    configuracionEmail = ConfiguracionEmail(tenant_file)
    configuracionEmail.cargar_configuracion()
    if(configuracionEmail.find is False):
        return
    else:
        try:
            month = int(input("Ingrese el MES: "))
            year = int(input("Ingrese el YEAR : "))
        except ValueError:
            print("❌ El mes y el año deben ser números.")
            return
        subFolderDate = f"{month}_{year}"
        email = configuracionEmail.obtener_config_email()
        reporter = ConsoleReporter()

        # La pregunta al usuario vive aquí; el núcleo solo recibe la decisión.
        zips = contar_zips(str(tenant_work_dir(tenant_id) / "zip" / subFolderDate))
        verificar = True
        if zips:
            respuesta = input(f"Ya hay {zips} ZIP descargados. ¿Verificar y descargar faltantes? (s/n): ")
            verificar = respuesta.strip().lower() == "s"

        do_on_start(subFolderDate, month, year, email, tenant_id, reporter, verificar)
        do_on_start_extract_facturacion(subFolderDate, tenant_id, reporter)
