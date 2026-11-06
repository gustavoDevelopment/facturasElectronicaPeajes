"""Pruebas de los servicios de la interfaz (sin ventana)."""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

MAIN_DIR = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(MAIN_DIR))

from interfaz import empresas, services  # noqa: E402


def test_mes_anterior():
    assert services.mes_anterior(date(2026, 11, 5)) == (10, 2026)
    assert services.mes_anterior(date(2026, 1, 3)) == (12, 2025)


def test_cargar_email_sin_configurar_da_mensaje_claro(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "tenant_email_path", lambda t: str(tmp_path / t / "email.json"))
    with pytest.raises(services.ConfiguracionIncompleta, match="pestaña Correo"):
        services.cargar_email("nuevo")


def test_guardar_email_password_y_cargarlo(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "tenant_email_path", lambda t: str(tmp_path / t / "email.json"))

    services.guardar_email_password("acme", "imap.gmail.com", "a@b.co", "clave-prueba")
    email = services.cargar_email("acme")

    assert email["user"] == "a@b.co" and email["auth_type"] == "password"


def test_guardar_email_oauth_guarda_token_en_la_carpeta_de_secretos(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "tenant_email_path", lambda t: str(tmp_path / t / "email.json"))
    monkeypatch.setattr(services, "tenant_secrets_dir", lambda t: tmp_path / t)
    llamadas = []
    monkeypatch.setattr(services, "obtener_credenciales", lambda secreto, token: llamadas.append((secreto, token)))

    services.guardar_email_oauth("acme", "imap.gmail.com", "a@b.co", "/x/client_secret.json")
    email = services.cargar_email("acme")

    assert llamadas == [("/x/client_secret.json", str(tmp_path / "acme" / "gmail_token.json"))]
    assert email["auth_type"] == "oauth2" and "password" not in email


def test_listar_tenants_une_tenants_json_y_secretos(tmp_path, monkeypatch):
    tenants, secretos = tmp_path / "tenants", tmp_path / "secretos"
    tenants.mkdir()
    (tenants / "tenants.json").write_text(json.dumps({"id1": {"name": "turboCarga"}}))
    (secretos / "otro").mkdir(parents=True)
    (secretos / "otro" / "email.json").write_text("{}")
    (secretos / "vacio").mkdir()
    monkeypatch.setattr(empresas, "TENANTS_DIR", tenants)
    monkeypatch.setattr(empresas, "SECRETS_DIR", secretos)

    assert services.listar_tenants() == ["otro", "turboCarga"]
