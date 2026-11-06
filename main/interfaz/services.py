"""
Operaciones que usa la interfaz gráfica. No dependen de ninguna librería de
ventanas, así que se pueden probar sin pantalla.
"""
import os
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import date
from typing import Optional

from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
from config import tenant_email_path, tenant_secrets_dir
from objects.fo_gmail_oauth import obtener_credenciales
from interfaz import empresas
from objects.fo_obj_email import ConfiguracionEmail


MAX_SIMULTANEOS = 4


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
    tenant: str = ""


class ConfiguracionIncompleta(Exception):
    """Falta configurar el correo del tenant."""


def listar_tenants() -> list:
    """Nombres de las empresas (registradas o con correo configurado)."""
    return [e["name"] for e in empresas.listar_empresas()]


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
    """Descarga los ZIP del mes y genera el Excel. Devuelve un ResumenProceso."""
    email = cargar_email(tenant_id)
    sub = f"{mes}_{anio}"
    descarga = do_on_start(sub, mes, anio, email, tenant_id, reporter, reverificar)
    proceso = do_on_start_extract_facturacion(sub, tenant_id, reporter)
    return ResumenProceso(descarga.correos, descarga.descargados, proceso.zips, proceso.facturas, proceso.excel)


class ProcesoDuplicado(Exception):
    """Ya hay un proceso en curso para ese tenant y mes."""


class DemasiadosProcesos(Exception):
    """Se alcanzó el máximo de procesos en curso a la vez."""


class Lanzador:
    """
    Lanza procesos independientes (uno por tenant y mes) en hilos propios. Se puede
    lanzar otro mientras los anteriores siguen corriendo; cada uno usa sus carpetas
    y su Excel. Un proceso que falla no afecta a los demás.
    """

    def __init__(self, max_simultaneos: int = MAX_SIMULTANEOS):
        self.max_simultaneos = max_simultaneos
        self._lock = threading.Lock()
        self._activos = set()

    @property
    def en_curso(self) -> int:
        with self._lock:
            return len(self._activos)

    def lanzar(self, tenant_id, mes, anio, reporter, al_terminar, reverificar=True):
        clave = (tenant_id, mes, anio)
        with self._lock:
            if clave in self._activos:
                raise ProcesoDuplicado(f"Ya hay un proceso en curso para {tenant_id} {mes:02d}/{anio}.")
            if len(self._activos) >= self.max_simultaneos:
                raise DemasiadosProcesos(
                    f"Ya hay {self.max_simultaneos} procesos en curso; espera a que termine alguno.")
            self._activos.add(clave)

        def trabajo():
            try:
                resultado = ResultadoMes(mes, anio, True, ejecutar_proceso(tenant_id, mes, anio, reporter, reverificar),
                                         tenant=tenant_id)
            except Exception as e:  # el error se muestra en el panel, no se pierde
                resultado = ResultadoMes(mes, anio, False, error=str(e), tenant=tenant_id)
            with self._lock:
                self._activos.discard(clave)  # antes del aviso, para poder relanzar de inmediato
            al_terminar(resultado)

        hilo = threading.Thread(target=trabajo, daemon=True)
        hilo.start()
        return hilo


def _guardar(tenant_id: str, actualizar) -> str:
    ruta = tenant_email_path(tenant_id)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    cfg = ConfiguracionEmail(ruta)
    cfg.config = {}
    if os.path.exists(ruta):
        cfg.cargar_configuracion()
    actualizar(cfg)
    cfg.guardar_configuracion()
    empresas.registrar_si_falta(tenant_id)  # una empresa nueva creada desde Correo también aparece en Empresas
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
