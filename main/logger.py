"""
Módulo de logging personalizado para Facturae Optimus.

Proporciona una configuración centralizada para el logging de la aplicación.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from main.config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, DEBUG

# Niveles de log válidos
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

class ColoredFormatter(logging.Formatter):
    """Formateador de logs con colores para la consola."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarillo
        'ERROR': '\033[31m',     # Rojo
        'CRITICAL': '\033[31;1m', # Rojo brillante
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Formatea el mensaje de log con colores."""
        log_message = super().format(record)
        if record.levelname in self.COLORS and sys.stderr.isatty():
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message

def setup_logger(name: str = None, log_level: str = None) -> logging.Logger:
    """
    Configura y devuelve un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger. Si es None, se usa el nombre del módulo.
        log_level: Nivel de log deseado. Si es None, se usa el nivel por defecto.
        
    Returns:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger(name or __name__)
    
    # Evitar configuraciones múltiples
    if logger.handlers:
        return logger
    
    # Configurar nivel de log
    level = LOG_LEVELS.get((log_level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(level)
    
    # Formateador
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Manejador para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # Manejador para archivo
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        logger.warning(f"No se pudo configurar el log en archivo: {e}")
    
    # En modo debug, mostrar más información
    if DEBUG:
        logger.debug("Modo depuración activado")
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger. Si es None, se usa el nombre del módulo.
        
    Returns:
        logging.Logger: Logger configurado.
    """
    return setup_logger(name)
