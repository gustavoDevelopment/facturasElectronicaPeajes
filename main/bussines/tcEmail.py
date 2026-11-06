import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime,timedelta
import base64
import threading
import calendar
from dataclasses import dataclass
from bussines.cancelacion import comprobar
from bussines.paths import tenant_work_dir
from bussines.reporter import Reporter
from objects.fo_gmail_oauth import obtener_credenciales, generar_auth_string

# Varios meses pueden procesarse a la vez: el token OAuth se lee/renueva de a uno
_LOCK_CREDENCIALES = threading.Lock()


def conectar_imap(emailConfig):
    """
    Abre y autentica una conexión IMAP según emailConfig["auth_type"]:
    - "oauth2": usa un token OAuth2 (Gmail) vía XOAUTH2.
    - cualquier otro valor (o ausente): usa usuario/contraseña (password de aplicación).
    """
    mail = imaplib.IMAP4_SSL(emailConfig["imap_server"])

    if emailConfig.get("auth_type") == "oauth2":
        with _LOCK_CREDENCIALES:
            creds = obtener_credenciales(
                emailConfig["oauth_client_secrets"],
                emailConfig["oauth_token"],
            )
        auth_string = generar_auth_string(emailConfig["user"], creds.token)
        mail.authenticate("XOAUTH2", lambda _: auth_string.encode())
    else:
        mail.login(emailConfig["user"], emailConfig["password"])

    mail.select("inbox")
    return mail

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

FILTRO_REMITENTE = 'FROM "notificaciones@int.lafactura.co"'


@dataclass
class ResultadoDescarga:
    correos: int = 0
    descargados: int = 0
    total_zips: int = 0


def contar_zips(carpeta):
    """Cantidad de ZIPs ya descargados en la carpeta."""
    if not os.path.exists(carpeta):
        return 0
    return len([f for f in os.listdir(carpeta) if f.endswith(".zip")])


def conectar_y_descargar(mes, annio, folderDownload, folderProcess, emailConfig,
                         reporter=None, verificar=True, cancelar=None):
    """
    Descarga los ZIP adjuntos de las facturas del mes indicado.

    verificar=False omite la descarga cuando ya hay ZIPs en folderDownload
    (la decisión de preguntar al usuario es de quien llama).
    """
    reporter = reporter or Reporter()
    inicio_mes = primer_dia_del_mes(mes, annio)
    fin_mes = primer_dia_del_siguiente_mes(mes, annio)

    existentes = contar_zips(folderDownload)
    reporter.info(f"Archivos ZIP ya descargados: {existentes}")
    if existentes and not verificar:
        reporter.info("Se continúa con los archivos ya descargados.")
        return ResultadoDescarga(total_zips=existentes)

    mail = conectar_imap(emailConfig)
    try:
        reporter.info(f"🔍 Buscando facturas desde {inicio_mes} hasta {fin_mes}")
        estado, mensajes = mail.search(None, f'(SENTSINCE {inicio_mes} BEFORE {fin_mes} {FILTRO_REMITENTE})')
        if estado != "OK":
            reporter.error("Error al buscar correos.")
            return ResultadoDescarga(total_zips=existentes)

        ids = mensajes[0].split()
        total_correos = len(ids)
        reporter.info(f"✅ Correos encontrados: {total_correos}")

        os.makedirs(folderDownload, exist_ok=True)
        descargados = 0

        for n, num in enumerate(ids, start=1):
            comprobar(cancelar)  # entre correos: nunca queda un ZIP a medio escribir
            estado, datos = mail.fetch(num, "(RFC822)")
            if estado != "OK":
                continue

            mensaje = email.message_from_bytes(datos[0][1])
            asunto, codificacion = decode_header(mensaje["Subject"])[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(codificacion or "utf-8")
            reporter.progress(n, total_correos, f"Procesando correo: {asunto}", "descarga")

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
                        reporter.info(f"   ✅ Archivo ya existe: {nombre_archivo}")
                        continue

                    try:
                        with open(ruta_completa, "wb") as f:
                            f.write(parte.get_payload(decode=True))
                        reporter.info(f"   💾 Descargado: {nombre_archivo}")
                        descargados += 1
                    except Exception as e:
                        reporter.error(f"No se pudo descargar {nombre_archivo}: {e}")
    finally:
        mail.logout()

    resultado = ResultadoDescarga(total_correos, descargados, contar_zips(folderDownload))
    reporter.info(
        f"📊 Correos: {resultado.correos} | descargados ahora: {resultado.descargados}"
        f" | total ZIPs: {resultado.total_zips}"
    )
    return resultado


def do_on_start(subFolder, month, year, emailConfig, tenant_id,
                reporter=None, verificar=True, output_dir=None, cancelar=None):
    reporter = reporter or Reporter()
    trabajo = tenant_work_dir(tenant_id, output_dir)
    downloadZIPS = str(trabajo / "zip" / subFolder)
    processZIPS = str(trabajo / "closedZip" / subFolder)
    reporter.info(f"Conectando con {emailConfig.get('user')} ({emailConfig.get('auth_type', 'password')})")
    reporter.info(f"Carpeta de descarga: {downloadZIPS}")
    os.makedirs(downloadZIPS, exist_ok=True)
    return conectar_y_descargar(month, year, downloadZIPS, processZIPS, emailConfig,
                                reporter, verificar, cancelar)
