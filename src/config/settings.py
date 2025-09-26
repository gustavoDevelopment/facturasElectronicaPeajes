"""
Configuración de la aplicación.
"""
import os
from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

# Configuración de correo
EMAIL_CONFIG = {
    "imap_server": "imap.gmail.com",
    "smtp_server": "smtp.gmail.com",
    "port": 587
}

# Configuración de almacenamiento
STORAGE_CONFIG = {
    "invoice_storage": str(STORAGE_DIR / "invoices"),
    "template_storage": str(STORAGE_DIR / "templates")
}

# Configuración de log
LOG_CONFIG = {
    "level": "DEBUG",
    "file": str(STORAGE_DIR / "logs" / "application.log")
}
