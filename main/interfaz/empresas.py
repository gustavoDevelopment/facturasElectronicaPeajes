"""
Administración de empresas (tenants): listar, crear, editar y eliminar.

Usa el mismo tenants.json que el menú de consola. El nombre de la empresa es su
identificador (carpetas, credenciales y plantilla), por eso no se puede renombrar.
"""
import json
import os
import re
import shutil
import uuid
from pathlib import Path

from bussines.paths import MAIN_DIR, plantilla_path, tenants_dir
from config import SECRETS_DIR, TENANTS_DIR
from objects.fo_obj_plantilla import ColumnConfig

ALMACENAMIENTOS = {
    "drive": "Google Drive",
    "aws": "Amazon Web Services (S3)",
    "ruta_fisica": "Ruta Física Local",
}
_NOMBRE_VALIDO = re.compile(r"[\w\- ]{1,50}")
_CORREO_VALIDO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class EmpresaError(Exception):
    """Dato inválido o empresa inexistente/duplicada."""


def _archivo() -> Path:
    return Path(TENANTS_DIR) / "tenants.json"


def _cargar() -> dict:
    try:
        return json.loads(_archivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _guardar(datos: dict) -> None:
    archivo = _archivo()
    archivo.parent.mkdir(parents=True, exist_ok=True)
    tmp = archivo.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, archivo)  # escritura atómica: nunca queda el archivo a medias


def _buscar(datos: dict, nombre: str):
    return next((k for k, v in datos.items() if v.get("name", "").lower() == nombre.lower()), None)


def validar_nombre(nombre: str) -> str:
    nombre = (nombre or "").strip()
    if not _NOMBRE_VALIDO.fullmatch(nombre) or nombre.startswith("."):
        raise EmpresaError("El nombre solo puede tener letras, números, espacios, guion y guion bajo (máx. 50).")
    return nombre


def _validar_correo(correo: str) -> str:
    correo = (correo or "").strip()
    if correo and not _CORREO_VALIDO.fullmatch(correo):
        raise EmpresaError("El correo de la empresa no es una dirección válida.")
    return correo


def listar_empresas() -> list:
    """Empresas registradas más las que solo tienen correo configurado (id None)."""
    datos = _cargar()
    filas = {}
    for id_, d in datos.items():
        if d.get("name"):
            filas[d["name"].lower()] = {"id": id_, "name": d["name"], "storage": d.get("storage", ""),
                                        "email_template": d.get("email_template", "")}
    secretos = Path(SECRETS_DIR)
    if secretos.is_dir():
        for carpeta in secretos.iterdir():
            if (carpeta / "email.json").exists() and carpeta.name.lower() not in filas:
                filas[carpeta.name.lower()] = {"id": None, "name": carpeta.name, "storage": "", "email_template": ""}
    for f in filas.values():
        f["tiene_correo"] = (Path(SECRETS_DIR) / f["name"] / "email.json").exists()
        f["tiene_plantilla"] = tiene_plantilla(f["name"])
    return sorted(filas.values(), key=lambda f: f["name"].lower())


def tiene_plantilla(nombre: str) -> bool:
    """Sin efectos: no copia nada, solo mira si hay plantilla propia o incluida."""
    return ((tenants_dir() / nombre / "plantilla.json").exists()
            or (MAIN_DIR / "build" / "tenant" / nombre / "plantilla.json").exists())


def plantilla_valida(ruta: str) -> str:
    """Devuelve el texto de la plantilla si es un JSON con columnas; si no, EmpresaError."""
    try:
        texto = Path(ruta).expanduser().read_text(encoding="utf-8")
        if not ColumnConfig.from_json(texto).columns:
            raise ValueError("sin columnas")
    except (OSError, ValueError, TypeError, KeyError) as e:
        raise EmpresaError(f"La plantilla no es válida: {e}") from e
    return texto


def _instalar_plantilla(nombre: str, copiar_de=None, plantilla_json=None) -> None:
    if copiar_de:
        origen = plantilla_path(copiar_de)
        if not origen.exists():
            raise EmpresaError(f"'{copiar_de}' no tiene plantilla para copiar.")
        texto = origen.read_text(encoding="utf-8")
    elif plantilla_json:
        texto = plantilla_valida(plantilla_json)
    else:
        return
    destino = tenants_dir() / nombre / "plantilla.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")


def crear_empresa(nombre, almacenamiento="", correo="", copiar_de=None, plantilla_json=None) -> str:
    nombre, correo = validar_nombre(nombre), _validar_correo(correo)
    datos = _cargar()
    if _buscar(datos, nombre):
        raise EmpresaError(f"Ya existe una empresa llamada '{nombre}'.")
    _instalar_plantilla(nombre, copiar_de, plantilla_json)
    id_ = str(uuid.uuid4())
    datos[id_] = {"name": nombre, "storage": almacenamiento, "email_template": correo, "created_at": str(uuid.uuid1())}
    _guardar(datos)
    return id_


def editar_empresa(nombre, almacenamiento="", correo="") -> None:
    correo = _validar_correo(correo)
    datos = _cargar()
    id_ = _buscar(datos, nombre)
    if id_ is None:  # empresa que solo tenía correo: se registra al editarla
        id_ = str(uuid.uuid4())
        datos[id_] = {"name": validar_nombre(nombre), "created_at": str(uuid.uuid1())}
    datos[id_].update({"storage": almacenamiento, "email_template": correo})
    _guardar(datos)


def registrar_si_falta(nombre: str) -> None:
    """Registra la empresa si aún no está en tenants.json (p. ej. creada desde la pestaña Correo)."""
    datos = _cargar()
    if _buscar(datos, nombre) is None:
        datos[str(uuid.uuid4())] = {"name": validar_nombre(nombre), "storage": "", "email_template": "",
                                    "created_at": str(uuid.uuid1())}
        _guardar(datos)


def _borrar_dentro_de(base: Path, nombre: str) -> None:
    objetivo = (base / nombre).resolve()
    if objetivo.is_dir() and base.resolve() in objetivo.parents:
        shutil.rmtree(objetivo)


def eliminar_empresa(nombre, borrar_credenciales=False) -> None:
    """
    Quita la empresa y su plantilla. Las credenciales de correo solo se borran si se pide.
    Nunca borra la carpeta de salida (ZIPs, vouchers y Excel ya generados).
    """
    datos = _cargar()
    id_ = _buscar(datos, nombre)
    if id_ is not None:
        del datos[id_]
        _guardar(datos)
    _borrar_dentro_de(tenants_dir(), nombre)
    if borrar_credenciales:
        _borrar_dentro_de(Path(SECRETS_DIR), nombre)
