"""Pruebas de ajustes portables: carpeta de datos, carpeta de salida y plantillas."""
import sys
from pathlib import Path

MAIN_DIR = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(MAIN_DIR))

import settings  # noqa: E402
from bussines import paths  # noqa: E402


def test_carpeta_de_datos_se_puede_mover(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))
    assert settings.user_data_dir() == tmp_path / "home"


def test_carpeta_de_salida_se_guarda_y_se_lee(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OUTPUT_DIR", raising=False)

    ruta = settings.set_output_dir(tmp_path / "salida")

    assert ruta.is_dir()
    assert settings.get_output_dir() == tmp_path / "salida"


def test_variable_de_entorno_gana_sobre_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))
    settings.set_output_dir(tmp_path / "guardada")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "entorno"))

    assert settings.get_output_dir() == tmp_path / "entorno"


def test_cada_tenant_usa_subcarpeta_con_su_nombre(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    settings.set_output_dir(tmp_path / "salida")

    assert paths.tenant_work_dir("turboCarga") == tmp_path / "salida" / "turboCarga"


def test_plantilla_se_copia_a_la_carpeta_del_usuario(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))

    ruta = paths.plantilla_path("test")

    assert ruta == tmp_path / "home" / "tenants" / "test" / "plantilla.json"
    assert ruta.exists()
