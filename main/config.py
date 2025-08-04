"""
Módulo de configuración para Facturae Optimus.

Este módulo carga la configuración desde variables de entorno y proporciona
valores por defecto para la aplicación.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

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
TENANTS_DIR = BASE_DIR / os.getenv("TENANTS_DIR", "build/tenant")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

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
