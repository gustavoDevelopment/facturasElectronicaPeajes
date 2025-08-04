"""
Configuración de pytest para las pruebas unitarias.
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno para pruebas
os.environ["DEBUG"] = "True"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["TENANTS_DIR"] = str(root_dir / "test_data/tenants")
