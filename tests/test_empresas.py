"""Administración de empresas (pestaña Empresas), sin ventana."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "main"))

from interfaz import empresas  # noqa: E402
from interfaz.empresas import EmpresaError  # noqa: E402

PLANTILLA = {"columns": [{"column": "Encab: Empresa", "index": 1}]}


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTURAE_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(empresas, "TENANTS_DIR", tmp_path / "tenants")
    monkeypatch.setattr(empresas, "SECRETS_DIR", tmp_path / "secretos")
    plantilla = tmp_path / "mi_plantilla.json"
    plantilla.write_text(json.dumps(PLANTILLA))
    return tmp_path, plantilla


def nombres():
    return [e["name"] for e in empresas.listar_empresas()]


def test_crear_y_listar_con_plantilla_importada(entorno):
    _, plantilla = entorno
    empresas.crear_empresa("Acme SAS", "drive", "info@acme.co", plantilla_json=str(plantilla))

    fila = empresas.listar_empresas()[0]
    assert fila["name"] == "Acme SAS" and fila["storage"] == "drive"
    assert fila["tiene_plantilla"] and not fila["tiene_correo"]


def test_crear_copiando_la_plantilla_de_otra_empresa(entorno):
    _, plantilla = entorno
    empresas.crear_empresa("Origen", plantilla_json=str(plantilla))
    empresas.crear_empresa("Copia", copiar_de="Origen")

    assert [e["tiene_plantilla"] for e in empresas.listar_empresas()] == [True, True]


@pytest.mark.parametrize("nombre", ["", "a/b", "../x", ".oculta", "x" * 51])
def test_nombre_invalido(entorno, nombre):
    with pytest.raises(EmpresaError):
        empresas.crear_empresa(nombre)


def test_no_permite_duplicados_sin_importar_mayusculas(entorno):
    empresas.crear_empresa("Acme")
    with pytest.raises(EmpresaError, match="Ya existe"):
        empresas.crear_empresa("ACME")


def test_correo_y_plantilla_invalidos(entorno):
    tmp, _ = entorno
    malo = tmp / "malo.json"
    malo.write_text("no es json")
    with pytest.raises(EmpresaError, match="correo"):
        empresas.crear_empresa("A", correo="sin-arroba")
    with pytest.raises(EmpresaError, match="plantilla"):
        empresas.crear_empresa("B", plantilla_json=str(malo))
    assert nombres() == []          # un intento fallido no deja la empresa a medias


def test_editar_cambia_almacenamiento_y_correo(entorno):
    empresas.crear_empresa("Acme", "drive", "a@acme.co")
    empresas.editar_empresa("Acme", "aws", "b@acme.co")

    fila = empresas.listar_empresas()[0]
    assert (fila["storage"], fila["email_template"]) == ("aws", "b@acme.co")


def test_empresa_con_solo_correo_aparece_y_se_registra(entorno):
    tmp, _ = entorno
    (tmp / "secretos" / "Solo").mkdir(parents=True)
    (tmp / "secretos" / "Solo" / "email.json").write_text("{}")

    assert empresas.listar_empresas()[0]["id"] is None and nombres() == ["Solo"]
    empresas.registrar_si_falta("Solo")
    assert empresas.listar_empresas()[0]["id"] is not None
    assert len(json.loads((tmp / "tenants" / "tenants.json").read_text())) == 1   # sin duplicar


def test_eliminar_conserva_credenciales_salvo_que_se_pida(entorno):
    tmp, plantilla = entorno
    empresas.crear_empresa("Acme", plantilla_json=str(plantilla))
    (tmp / "secretos" / "Acme").mkdir(parents=True)
    (tmp / "secretos" / "Acme" / "email.json").write_text("{}")

    empresas.eliminar_empresa("Acme")
    assert (tmp / "secretos" / "Acme" / "email.json").exists()      # credenciales intactas
    assert not (tmp / "home" / "tenants" / "Acme").exists()          # plantilla propia borrada

    empresas.eliminar_empresa("Acme", borrar_credenciales=True)
    assert not (tmp / "secretos" / "Acme").exists()


def test_eliminar_no_sale_de_su_carpeta(entorno):
    tmp, _ = entorno
    (tmp / "fuera").mkdir()
    (tmp / "secretos").mkdir()
    empresas.eliminar_empresa("../fuera", borrar_credenciales=True)
    assert (tmp / "fuera").exists()
