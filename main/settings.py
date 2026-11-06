"""
Ajustes de usuario y carpetas de datos, iguales en macOS, Windows y Linux.

- user_data_dir(): tenants, plantillas, logs y settings.json de la aplicación.
  Se puede cambiar con la variable de entorno FACTURAE_HOME.
- Carpeta de salida (ZIPs, vouchers, Excel): una sola para todos los tenants;
  cada tenant usa una subcarpeta con su nombre.
"""
import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "FacturaeOptimus"
SETTINGS_FILENAME = "settings.json"


def user_data_dir() -> Path:
    override = os.getenv("FACTURAE_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_DIR_NAME


def settings_path() -> Path:
    return user_data_dir() / SETTINGS_FILENAME


def load_settings() -> dict:
    try:
        return json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(data: dict) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def default_output_dir() -> Path:
    """Carpeta previa si ya existe (compatibilidad); si no, Documentos del usuario."""
    legacy = Path(__file__).resolve().parents[2] / "Facturae_Optimus"
    if not getattr(sys, "frozen", False) and legacy.is_dir():
        return legacy
    return Path.home() / "Documents" / "Facturae_Optimus"


def get_output_dir() -> Path:
    """Orden: variable OUTPUT_DIR, settings.json, valor por defecto."""
    elegido = os.getenv("OUTPUT_DIR") or load_settings().get("output_dir")
    return Path(elegido).expanduser() if elegido else default_output_dir()


def set_output_dir(carpeta) -> Path:
    """Guarda la carpeta de salida (la crea si no existe) y la devuelve."""
    ruta = Path(carpeta).expanduser()
    ruta.mkdir(parents=True, exist_ok=True)
    datos = load_settings()
    datos["output_dir"] = str(ruta)
    save_settings(datos)
    return ruta
