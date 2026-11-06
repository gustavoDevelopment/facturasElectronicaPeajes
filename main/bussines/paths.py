"""Rutas de trabajo de la aplicación (descargas, ZIPs, vouchers, salida)."""
import os
from pathlib import Path

from plantilla.constants import Constants

MAIN_DIR = Path(__file__).resolve().parents[1]

# Carpeta que contiene Facturae_Optimus/<tenant>/..., dos niveles sobre main/
# (misma ubicación que usaba el código anterior). Se puede cambiar con DATA_DIR.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    return Path(os.getenv("DATA_DIR", DEFAULT_DATA_DIR)).expanduser()


def resolve_base_dir(base_dir=None) -> Path:
    return Path(base_dir) if base_dir else data_dir()


def tenant_work_dir(tenant_id: str, base_dir=None) -> Path:
    return resolve_base_dir(base_dir) / Constants.APLICATION_NAME.value[0] / tenant_id


def plantilla_path(tenant_id: str) -> Path:
    return MAIN_DIR / "build" / "tenant" / tenant_id / "plantilla.json"
