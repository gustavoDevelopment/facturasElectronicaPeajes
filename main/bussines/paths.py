"""Rutas de trabajo de la aplicación (descargas, ZIPs, vouchers, salida)."""
import shutil
from pathlib import Path

from settings import get_output_dir, user_data_dir

MAIN_DIR = Path(__file__).resolve().parents[1]


def tenant_work_dir(tenant_id: str, output_dir=None) -> Path:
    """Carpeta de trabajo de un tenant: <carpeta de salida>/<tenant>."""
    base = Path(output_dir) if output_dir else get_output_dir()
    return base / tenant_id


def tenants_dir() -> Path:
    return user_data_dir() / "tenants"


def plantilla_path(tenant_id: str) -> Path:
    """
    plantilla.json del tenant en la carpeta del usuario. Si aún no existe, se
    copia la que viene con la aplicación (main/build/tenant/<tenant>/).
    """
    destino = tenants_dir() / tenant_id / "plantilla.json"
    if not destino.exists():
        incluida = MAIN_DIR / "build" / "tenant" / tenant_id / "plantilla.json"
        if incluida.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(incluida, destino)
    return destino
