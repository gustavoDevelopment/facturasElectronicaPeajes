"""La ayuda de la aplicación debe cubrir los pasos clave y tener enlaces válidos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "main"))

from interfaz.ayuda import AYUDA, ENLACES  # noqa: E402


def test_ayuda_cubre_los_pasos_clave():
    for clave in ("client_secret.json", "Gmail API", "Aplicación de escritorio",
                  "Guardar / Vincular", "7 días", "Contraseña de aplicación"):
        assert clave in AYUDA


def test_enlaces_son_https_de_google():
    assert ENLACES
    for texto, url in ENLACES:
        assert texto and url.startswith("https://")
        assert "google.com" in url
