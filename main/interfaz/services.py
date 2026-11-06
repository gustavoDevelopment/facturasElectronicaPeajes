"""
Operaciones que usa la interfaz gráfica. No dependen de ninguna librería de
ventanas, así que se pueden probar sin pantalla.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from typing import Optional

from bussines.paths import plantilla_path
from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
from config import TENANTS_DIR, SECRETS_DIR, tenant_email_path, tenant_secrets_dir
from objects.fo_gmail_oauth import obtener_credenciales
from objects.fo_obj_email import ConfiguracionEmail


MAX_MESES = 24


@dataclass
class ResumenProceso:
    """Datos de un mes procesado, para mostrar en el panel de resumen."""
    correos: int = 0
    descargados: int = 0
    zips: int = 0
    facturas: int = 0
    excel: str = ""


@dataclass
class ResultadoMes:
    mes: int
    anio: int
    ok: bool
    resultado: Optional[object] = None
    error: str = ""


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


def rango_meses(desde: tuple, hasta: tuple) -> list:
    """Lista de (mes, año) desde el primero hasta el último, ambos incluidos."""
    for mes, _ in (desde, hasta):
        if not 1 <= mes <= 12:
            raise ValueError("El mes debe estar entre 1 y 12.")
    inicio, fin = desde[1] * 12 + desde[0] - 1, hasta[1] * 12 + hasta[0] - 1
    if fin < inicio:
        raise ValueError("El mes final no puede ser anterior al inicial.")
    if fin - inicio + 1 > MAX_MESES:
        raise ValueError(f"Máximo {MAX_MESES} meses por ejecución.")
    return [(k % 12 + 1, k // 12) for k in range(inicio, fin + 1)]


def cargar_email(tenant_id: str) -> dict:
    cfg = ConfiguracionEmail(tenant_email_path(tenant_id))
    cfg.cargar_configuracion()
    email = cfg.obtener_config_email() if getattr(cfg, "find", False) else None
    if not email:
        raise ConfiguracionIncompleta(f"El tenant '{tenant_id}' no tiene el correo configurado (pestaña Correo).")
    return email


def ejecutar_proceso(tenant_id: str, mes: int, anio: int, reporter, reverificar: bool = True):
    """Descarga los ZIP del mes y genera el Excel. Devuelve un ResumenProceso."""
    email = cargar_email(tenant_id)
    sub = f"{mes}_{anio}"
    descarga = do_on_start(sub, mes, anio, email, tenant_id, reporter, reverificar)
    proceso = do_on_start_extract_facturacion(sub, tenant_id, reporter)
    return ResumenProceso(descarga.correos, descarga.descargados, proceso.zips, proceso.facturas, proceso.excel)


def ejecutar_varios(tenant_id: str, meses: list, crear_reporter, reverificar: bool = True,
                    simultaneos: int = 3, al_terminar=None) -> list:
    """
    Procesa varios meses a la vez (cada mes usa sus propias carpetas y Excel).

    crear_reporter(clave) devuelve el Reporter de ese mes; al_terminar(ResultadoMes)
    se llama cuando termina cada mes. Un mes que falla no detiene a los demás.
    Devuelve los resultados en el orden de `meses`.
    """
    cargar_email(tenant_id)      # falla rápido si falta configurar el correo
    plantilla_path(tenant_id)    # copia la plantilla una sola vez, antes de los hilos

    def uno(mes, anio):
        try:
            res = ejecutar_proceso(tenant_id, mes, anio, crear_reporter(f"{mes:02d}/{anio}"), reverificar)
            return ResultadoMes(mes, anio, True, res)
        except Exception as e:  # un mes con error no debe detener a los demás
            return ResultadoMes(mes, anio, False, error=str(e))

    resultados = {}
    with ThreadPoolExecutor(max_workers=max(1, min(simultaneos, len(meses)))) as pool:
        futuros = {pool.submit(uno, m, a): (m, a) for m, a in meses}
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            resultados[futuros[futuro]] = resultado
            if al_terminar:
                al_terminar(resultado)
    return [resultados[k] for k in meses]


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
