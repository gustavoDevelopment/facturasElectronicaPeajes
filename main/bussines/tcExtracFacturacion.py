import os
import shutil
import zipfile
from lxml import etree
from bussines.tcCausar import agregar_filas_al_excel
from bussines.tcCausar import crear_archivo_excel_con_cabecera
from bussines.tcProcesFacturacion import extraer_datos_factura

# Namespaces UBL
ns = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
}

def descomprimir_y_procesar_zip(subFolder,zipPath,zipName,processDir,closedDir):  
    print(f"descomprimir_y_procesar_zip: {zipPath} | subFolder: {subFolder} | zipName: {zipName}")
    carpeta_destino = os.path.join(processDir,subFolder, zipName)
    os.makedirs(carpeta_destino, exist_ok=True)
    print(f"📁 Carpeta destino para descomprimir: {carpeta_destino}")

    # Extraer todo el contenido
    with zipfile.ZipFile(zipPath, "r") as zip_ref:
        nombres_archivos = zip_ref.namelist()
        archivos_xml = [nombre for nombre in nombres_archivos if nombre.lower().endswith('.xml')]
        
        print("🧾 Archivos XML encontrados en el ZIP:")
        for xml in archivos_xml:
            print(f" - {xml}")
            
        zip_ref.extractall(carpeta_destino)

    print(f"📁 ZIP descomprimido en: {carpeta_destino}")

    # Mover el ZIP a la carpeta 'closed'
    os.makedirs(closedDir, exist_ok=True)
    destino_zip = os.path.join(closedDir, os.path.basename(zipPath))
    shutil.move(zipPath, destino_zip)

    print(f"📦 ZIP movido a: {destino_zip}\n")
    return carpeta_destino,archivos_xml;

def do_on_create_voucher(factura_id, texto_factura,voucherDir):
    
    # Crear la carpeta 'voucherPeaje' si no existe
    if not os.path.exists(voucherDir):
        os.makedirs(voucherDir)
    
    # Crear el nombre del archivo con el factura_id
    file_name = f"{factura_id}.txt"
    file_path = os.path.join(voucherDir, file_name)
    
    # Guardar el texto de la factura en el archivo .txt
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(texto_factura)
    
    print(f"Factura guardada en: {file_path}")

# ---------- Ejecutar ----------
def do_on_start_extract_facturacion(subFolder):
    base_dir = os.getcwd()
    base_dir = os.path.dirname(base_dir)
    base_facturas = os.path.join(base_dir, "zip",subFolder)
    voucherDir = os.path.join(base_dir, "voucher",subFolder)
    processDir = os.path.join(base_dir, "openZip",subFolder)
    closedDir = os.path.join(base_dir, "closedZip",subFolder)
    print("📂 Directorio Base:", base_dir)
    print("📂 Directorio base_facturas:", base_facturas)
    print("📂 Directorio voucherDir:", voucherDir)
    print("📂 Directorio processDir:", processDir)
    print("📂 Directorio closedDir:", closedDir)
    
    # Crear carpetas si no existen
    os.makedirs(voucherDir, exist_ok=True)
    os.makedirs(processDir, exist_ok=True)
    os.makedirs(closedDir, exist_ok=True)

    print("🔎 Buscando zip facturas in path...",base_facturas)
    lista_peajes = []
    for filename in os.listdir(base_facturas):
        path = os.path.join(base_facturas, filename)
        if filename.endswith(".zip") and not filename.endswith(".crdownload"):
            if filename.lower().endswith(".zip"):
                print(f"📦 ZIP detectado: {filename}")
                pathFileFac,archivos_xml= descomprimir_y_procesar_zip(subFolder,path,filename,processDir,closedDir)
                for fileNameXml in archivos_xml:
                    ruta_completa = os.path.join(pathFileFac, fileNameXml)
                    factura_id, texto_factura = extraer_datos_factura(subFolder,ruta_completa)
                    do_on_create_voucher(str(factura_id),str(texto_factura),voucherDir)
                    lista_peajes.append(texto_factura)
        else :
            print(f"📦 ZIP detectado in download not process {filename}")
            
    print("🔎 Generando plantilla...")
    path_plantilla=crear_archivo_excel_con_cabecera(subFolder)
    agregar_filas_al_excel(path_plantilla,lista_peajes)
    print("\n✅ Proceso completado.")
