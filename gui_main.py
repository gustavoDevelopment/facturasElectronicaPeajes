"""Punto de entrada de la interfaz gráfica: python gui_main.py"""
import sys
from pathlib import Path

raiz = Path(__file__).parent
for ruta in (raiz, raiz / "main"):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

from interfaz.app import run  # noqa: E402

if __name__ == "__main__":
    run()
