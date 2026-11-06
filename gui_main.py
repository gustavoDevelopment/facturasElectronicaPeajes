"""Punto de entrada de la interfaz gráfica: python gui_main.py  (--check para autoprueba)"""
import os
import sys
from pathlib import Path

# Sin consola (aplicación empaquetada en Windows) stdout/stderr pueden ser None
for _nombre in ("stdout", "stderr"):
    if getattr(sys, _nombre) is None:
        setattr(sys, _nombre, open(os.devnull, "w"))

raiz = Path(__file__).parent
for ruta in (raiz, raiz / "main"):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

from interfaz.app import autotest, run  # noqa: E402

if __name__ == "__main__":
    if "--check" in sys.argv:
        print(autotest())
    else:
        run()
