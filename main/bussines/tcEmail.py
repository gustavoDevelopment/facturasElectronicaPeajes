import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime,timedelta
import base64
import calendar
from plantilla.constants import Constants

def limpiar_texto(texto):
    return "".join(c for c in texto if c.isalnum() or c in (" ", ".", "_", "-"))

def primer_dia_del_mes(mes, annio):
    # Devuelve el primer día del mes especificado
    return datetime(annio, mes, 1).strftime("%d-%b-%Y")

def primer_dia_del_siguiente_mes(mes, annio):
    # Devuelve el primer día del mes especificado
    return (datetime(annio, mes, 1) + timedelta(days=32)).replace(day=1).strftime("%d-%b-%Y")

def ultimo_dia_del_mes(mes, annio):
    # Devuelve el último día del mes especificado
    ultimo_dia = calendar.monthrange(annio, mes)[1]
    return datetime(annio, mes, ultimo_dia).strftime("%d-%b-%Y")

def conectar_y_descargar(mes, annio,folderDownload,folderProcess,emailConfig):

    inicio_mes = primer_dia_del_mes(mes, annio)
    fin_mes = primer_dia_del_siguiente_mes(mes, annio)

    # Conectar a Gmail
    mail = imaplib.IMAP4_SSL(emailConfig["imap_server"])
    mail.login(emailConfig["user"], emailConfig["password"])
    mail.select("inbox")

    # Buscar correos del día con el asunto específico
    print("Find Facturas desde ",inicio_mes," hasta ",fin_mes)
    estado, mensajes = mail.search(None, f'(SENTSINCE {inicio_mes} BEFORE {fin_mes} FROM "notificaciones@int.lafactura.co")')
    if estado != "OK":
        print("❌ Error al buscar correos.")
        return

    ids = mensajes[0].split()
    print(f"🔍 Correos encontrados {inicio_mes} hasta {fin_mes}: {len(ids)}")

    
    for num in ids:
        estado, datos = mail.fetch(num, "(RFC822)")
        if estado != "OK":
            continue

        mensaje = email.message_from_bytes(datos[0][1])
        asunto, codificacion = decode_header(mensaje["Subject"])[0]
        if isinstance(asunto, bytes):
            asunto = asunto.decode(codificacion or "utf-8")

        print(f"📨 Procesando correo: {asunto}")

        for parte in mensaje.walk():
            if parte.get_content_maintype() == "multipart":
                continue
            if parte.get("Content-Disposition") is None:
                continue

            nombre_archivo = parte.get_filename()
            if nombre_archivo and nombre_archivo.endswith(".zip"):
                nombre_archivo = limpiar_texto(nombre_archivo)
                ruta_completa = os.path.join(folderDownload, nombre_archivo)
                ruta_process = os.path.join(folderProcess, nombre_archivo)

                if os.path.exists(ruta_completa) or os.path.exists(ruta_process):
                    print(f"✅ Ya descargado o procesado: {nombre_archivo}\n")
                    continue

                # Descargar archivo
                with open(ruta_completa, "wb") as f:
                    f.write(parte.get_payload(decode=True))
                print(f"💾 Descargando: {nombre_archivo}\n")
    
    mail.logout()

def do_on_start(subFolder,month,year,emailConfig,tenant_id):
    print("Conect Email with config: ",emailConfig)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.dirname(os.path.dirname(base_dir))
    print("Folder Base: ",base_dir)
    downloadZIPS = os.path.join(base_dir,Constants.APLICATION_NAME.value[0],tenant_id, "zip",subFolder)
    processZIPS = os.path.join(base_dir,Constants.APLICATION_NAME.value[0],tenant_id, "closedZip",subFolder)   
    print("Folder download email: ",downloadZIPS) 
    os.makedirs(downloadZIPS, exist_ok=True)
    conectar_y_descargar(month,year,downloadZIPS,processZIPS,emailConfig)
