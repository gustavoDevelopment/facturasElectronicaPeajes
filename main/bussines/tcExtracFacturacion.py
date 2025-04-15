import os
import shutil
import zipfile
from lxml import etree

# Configurar rutas
base_dir = None
base_facturas = None
salida_txt = None
procesadas_dir = None
zip_closed_dir = None

# Namespaces UBL
ns = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
}

def descomprimir_y_procesar_zip(subFolder,zip_path):
    """Descomprime un zip en una carpeta y procesa los XML que encuentre dentro."""
    nombre_zip = os.path.splitext(os.path.basename(zip_path))[0]
    carpeta_destino = os.path.join(procesadas_dir,subFolder, nombre_zip)
    os.makedirs(carpeta_destino, exist_ok=True)

    # Extraer todo el contenido
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        nombres_archivos = zip_ref.namelist()
        archivos_xml = [nombre for nombre in nombres_archivos if nombre.lower().endswith('.xml')]
        
        print("🧾 Archivos XML encontrados en el ZIP:")
        for xml in archivos_xml:
            print(f" - {xml}")
            
        zip_ref.extractall(carpeta_destino)

    print(f"📁 ZIP descomprimido en: {carpeta_destino}")

    # Mover el ZIP a la carpeta 'closed'
    os.makedirs(zip_closed_dir, exist_ok=True)
    destino_zip = os.path.join(zip_closed_dir, os.path.basename(zip_path))
    shutil.move(zip_path, destino_zip)

    print(f"📦 ZIP movido a: {destino_zip}\n")
    return carpeta_destino,archivos_xml;

def do_on_create_voucher(factura_id, texto_factura ):
    
    # Crear la carpeta 'voucherPeaje' si no existe
    if not os.path.exists(salida_txt):
        os.makedirs(salida_txt)
    
    # Crear el nombre del archivo con el factura_id
    file_name = f"{factura_id}.txt"
    file_path = os.path.join(salida_txt, file_name)
    
    # Guardar el texto de la factura en el archivo .txt
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(texto_factura)
    
    print(f"Factura guardada en: {file_path}")

# ---------- Ejecutar ----------
def do_on_start_extract_facturacion(subFolder):
    base_dir = os.getcwd()
    base_dir = os.path.dirname(base_dir)
    print("📂 Directorio Base:", base_dir)
    base_facturas = os.path.join(base_dir, "zip",subFolder)
    salida_txt = os.path.join(base_dir, "voucher",subFolder)
    procesadas_dir = os.path.join(base_dir, "openZip",subFolder)
    
    # Crear carpetas si no existen
    os.makedirs(salida_txt, exist_ok=True)
    os.makedirs(procesadas_dir, exist_ok=True)

    print("🔎 Buscando zip facturas in path...",base_facturas)
    lista_peajes = []
    for filename in os.listdir(base_facturas):
        path = os.path.join(base_facturas, filename)
        if filename.endswith(".zip") and not filename.endswith(".crdownload"):
            if filename.lower().endswith(".zip"):
                print(f"📦 ZIP detectado: {filename}")
                pathFileFac,archivos_xml= descomprimir_y_procesar_zip(subFolder,path)
                for fileNameXml in archivos_xml:
                    ruta_completa = os.path.join(pathFileFac, fileNameXml)
                    factura_id, texto_factura = extraer_datos_factura(subFolder,ruta_completa)
                    do_on_create_voucher(str(factura_id),str(texto_factura))
                    lista_peajes.append(texto_factura)
        else :
            print(f"📦 ZIP detectado in download not process {filename}")
            
    print("🔎 Generando plantilla...")
    path_plantilla=tcCausar.crear_archivo_excel_con_cabecera(str(month)+str("_")+str(year))
    tcCausar.agregar_filas_al_excel(path_plantilla,lista_peajes)

    print("\n✅ Proceso completado.")
