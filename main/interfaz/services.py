"""
Operaciones que usa la interfaz gráfica. No dependen de ninguna librería de
ventanas, así que se pueden probar sin pantalla.
"""
import json
import os
import subprocess
import sys
from datetime import date

from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
from config import TENANTS_DIR, SECRETS_DIR, tenant_email_path, tenant_secrets_dir
from objects.fo_gmail_oauth import obtener_credenciales
from objects.fo_obj_email import ConfiguracionEmail


class ConfiguracionIncompleta(Exception):
    """Falta configurar el correo del tenant."""


def listar_tenants() -> list:
    """Tenants conocidos: los de tenants.json y los que ya tienen correo configurado."""
    nombres = set()
    try:
        with open(TENANTS_DIR / "tenants.json", encoding="utf-8") as f:
            nombres.update(t.get("name") for t in json.load(f).values() if t.get("name"))
    except (OSError, ValueError):
        pass
    if SECRETS_DIR.is_dir():
        nombres.update(d.name for d in SECRETS_DIR.iterdir() if (d / "email.json").exists())
    return sorted(nombres)


def mes_anterior(hoy=None):
    """(mes, año) del mes anterior: el que normalmente se procesa."""
    hoy = hoy or date.today()
    return (12, hoy.year - 1) if hoy.month == 1 else (hoy.month - 1, hoy.year)


def cargar_email(tenant_id: str) -> dict:
    cfg = ConfiguracionEmail(tenant_email_path(tenant_id))
    cfg.cargar_configuracion()
    email = cfg.obtener_config_email() if getattr(cfg, "find", False) else None
    if not email:
        raise ConfiguracionIncompleta(f"El tenant '{tenant_id}' no tiene el correo configurado (pestaña Correo).")
    return email


def ejecutar_proceso(tenant_id: str, mes: int, anio: int, reporter, reverificar: bool = True):
    """Descarga los ZIP del mes y genera el Excel. Devuelve ResultadoProceso."""
    email = cargar_email(tenant_id)
    sub = f"{mes}_{anio}"
    do_on_start(sub, mes, anio, email, tenant_id, reporter, reverificar)
    return do_on_start_extract_facturacion(sub, tenant_id, reporter)


def _guardar(tenant_id: str, actualizar) -> str:
    ruta = tenant_email_path(tenant_id)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    cfg = ConfiguracionEmail(ruta)
    cfg.config = {}
    if os.path.exists(ruta):
        cfg.cargar_configuracion()
    actualizar(cfg)
    cfg.guardar_configuracion()
    return ruta


def guardar_email_password(tenant_id, imap_server, usuario, password) -> str:
    return _guardar(tenant_id, lambda c: c.actualizar_config_email(imap_server, usuario, password))


def guardar_email_oauth(tenant_id, imap_server, usuario, client_secrets) -> str:
    """Autoriza con Google (abre el navegador) y guarda el token fuera del repo."""
    client_secrets = os.path.expanduser(client_secrets)
    token = os.path.join(str(tenant_secrets_dir(tenant_id)), "gmail_token.json")
    obtener_credenciales(client_secrets, token)
    return _guardar(tenant_id, lambda c: c.actualizar_config_email_oauth2(imap_server, usuario, client_secrets, token))


def abrir_ruta(ruta: str) -> None:
    """Abre un archivo o carpeta con la aplicación del sistema."""
    if sys.platform == "win32":
        os.startfile(ruta)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", ruta], check=False)
    else:
        subprocess.run(["xdg-open", ruta], check=False)
