import os
import shutil
import zipfile
from lxml import etree
from bussines.tcCausar import agregar_filas_al_excel
from bussines.tcCausar import crear_archivo_excel_con_cabecera
from bussines.tcProcesFacturacion import extraer_datos_factura
from dataclasses import dataclass
from bussines.paths import tenant_work_dir, plantilla_path
from bussines.reporter import Reporter
from objects.fo_obj_plantilla import do_on_get_columns

# Namespaces UBL
ns = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
}

@dataclass
class ResultadoProceso:
    zips: int = 0
    facturas: int = 0
    excel: str = ""


def descomprimir_y_procesar_zip(subFolder, zipPath, zipName, processDir, closedDir, reporter=None):
    reporter = reporter or Reporter()
    carpeta_destino = os.path.join(processDir, subFolder, zipName)
    os.makedirs(carpeta_destino, exist_ok=True)

    with zipfile.ZipFile(zipPath, "r") as zip_ref:
        archivos_xml = [n for n in zip_ref.namelist() if n.lower().endswith('.xml')]
        zip_ref.extractall(carpeta_destino)
    reporter.info(f"📁 {zipName}: {len(archivos_xml)} XML descomprimidos en {carpeta_destino}")

    # Mover el ZIP a la carpeta 'closed'
    os.makedirs(closedDir, exist_ok=True)
    shutil.move(zipPath, os.path.join(closedDir, os.path.basename(zipPath)))
    return carpeta_destino, archivos_xml


def do_on_create_voucher(factura_id, texto_factura, voucherDir, reporter=None):
    reporter = reporter or Reporter()
    os.makedirs(voucherDir, exist_ok=True)
    file_path = os.path.join(voucherDir, f"{factura_id}.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(texto_factura)
    reporter.info(f"Factura guardada en: {file_path}")


def do_on_start_extract_facturacion(subFolder, tenant_id, reporter=None, output_dir=None):
    reporter = reporter or Reporter()
    trabajo = tenant_work_dir(tenant_id, output_dir)
    base_facturas = str(trabajo / "zip" / subFolder)
    voucher_dir = str(trabajo / "voucher" / subFolder)
    process_dir = str(trabajo / "openZip" / subFolder)
    closed_dir = str(trabajo / "closedZip" / subFolder)

    for carpeta in (voucher_dir, process_dir, closed_dir):
        os.makedirs(carpeta, exist_ok=True)

    reporter.info(f"🔎 Buscando ZIP de facturas en {base_facturas}")
    zips = sorted(f for f in os.listdir(base_facturas) if f.lower().endswith(".zip"))
    pendientes = [f for f in os.listdir(base_facturas) if f.endswith(".crdownload")]
    for f in pendientes:
        reporter.warn(f"Descarga incompleta, se omite: {f}")

    lista_peajes = []
    for n, filename in enumerate(zips, start=1):
        reporter.progress(n, len(zips), f"ZIP: {filename}")
        path = os.path.join(base_facturas, filename)
        pathFileFac, archivos_xml = descomprimir_y_procesar_zip(
            subFolder, path, filename, process_dir, closed_dir, reporter)
        for fileNameXml in archivos_xml:
            ruta_completa = os.path.join(pathFileFac, fileNameXml)
            factura_id, texto_factura = extraer_datos_factura(ruta_completa)
            do_on_create_voucher(str(factura_id), str(texto_factura), voucher_dir, reporter)
            lista_peajes.append(texto_factura)

    reporter.info("🔎 Generando plantilla...")
    cabeceras = do_on_get_columns(str(plantilla_path(tenant_id)))
    path_plantilla = crear_archivo_excel_con_cabecera(
        str(trabajo), subFolder, cabeceras, reporter)
    agregar_filas_al_excel(path_plantilla, lista_peajes, reporter)
    reporter.info("✅ Proceso completado.")
    return ResultadoProceso(len(zips), len(lista_peajes), path_plantilla)
