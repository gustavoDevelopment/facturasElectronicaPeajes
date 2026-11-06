"""
Módulo de configuración para Facturae Optimus.

Este módulo carga la configuración desde variables de entorno y proporciona
valores por defecto para la aplicación.
"""
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
try:
    from settings import user_data_dir
except ImportError:  # importado como paquete main.config
    from main.settings import user_data_dir

# Cargar variables de entorno desde .env si existe
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Constantes de la aplicación
APP_NAME = "Facturae Optimus"
VERSION = "1.0.0"
DEFAULT_ENCODING = "utf-8"

# Configuración de directorios
BASE_DIR = Path(__file__).parent.parent
# Tenants y logs viven en la carpeta de datos del usuario (ver settings.py),
# no junto al código, para que funcione igual en una aplicación empaquetada.
TENANTS_DIR = Path(os.getenv("TENANTS_DIR") or user_data_dir() / "tenants")
LOG_DIR = Path(os.getenv("LOG_DIR") or user_data_dir() / "logs")

# Primer arranque: copiar el tenants.json que trae el repositorio
# (empaquetado con PyInstaller, los recursos están en sys._MEIPASS)
_RECURSOS = Path(getattr(sys, "_MEIPASS", BASE_DIR))
_incluido = _RECURSOS / "build" / "tenant" / "tenants.json"
if not (TENANTS_DIR / "tenants.json").exists() and _incluido.exists():
    TENANTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(_incluido, TENANTS_DIR / "tenants.json")

# Secretos por tenant (email.json, gmail_token.json), fuera del repositorio
SECRETS_DIR = Path(
    os.getenv("SECRETS_DIR", Path.home() / ".facturae_optimus" / "secrets")
).expanduser()


def tenant_secrets_dir(tenant_id: str) -> Path:
    """Directorio de secretos de un tenant (fuera del repo)."""
    return SECRETS_DIR / tenant_id


def tenant_email_path(tenant_id: str) -> str:
    """Ruta del email.json de un tenant."""
    return str(tenant_secrets_dir(tenant_id) / "email.json")

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv(
    "LOG_FORMAT", 
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOG_FILE = LOG_DIR / os.getenv("LOG_FILE", "facturae_optimus.log")

# Configuración de la aplicación
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Asegurar que los directorios existan
for directory in [TENANTS_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def get_version() -> str:
    """Devuelve la versión de la aplicación."""
    return f"{APP_NAME} v{VERSION}"

def get_config() -> Dict[str, Any]:
    """
    Devuelve la configuración actual como un diccionario.
    
    Returns:
        Dict[str, Any]: Diccionario con la configuración actual.
    """
    return {
        "app_name": APP_NAME,
        "version": VERSION,
        "debug": DEBUG,
        "tenants_dir": str(TENANTS_DIR),
        "log_dir": str(LOG_DIR),
        "log_level": LOG_LEVEL,
    }

# Configuración específica para el procesamiento de facturas
PROCESSING_CONFIG = {
    "xml_encoding": DEFAULT_ENCODING,
    "date_format": "%Y-%m-%d",
    "display_date_format": "%d/%m/%Y",
    "max_retries": 3,
    "timeout_seconds": 30,
}
