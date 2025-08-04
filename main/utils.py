"""
Módulo de utilidades para Facturae Optimus.

Contiene funciones de utilidad utilizadas en toda la aplicación.
"""
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import DEBUG

# Expresión regular para validar NITs (formato: 123456789-0)
NIT_PATTERN = re.compile(r'^\d{1,15}(-\d|\d)$')

def normalizar_texto(texto: str) -> str:
    """
    Normaliza un texto eliminando acentos y caracteres especiales.
    
    Args:
        texto: Texto a normalizar.
        
    Returns:
        str: Texto normalizado.
    """
    if not texto:
        return ""
    
    # Normalizar a forma normalizada de Unicode (NFKD)
    texto = unicodedata.normalize('NFKD', str(texto))
    # Eliminar diacríticos (acentos)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    # Convertir a mayúsculas
    return texto.upper()

def validar_nit(nit: str) -> bool:
    """
    Valida el formato de un NIT.
    
    Args:
        nit: Número de NIT a validar.
        
    Returns:
        bool: True si el NIT es válido, False en caso contrario.
    """
    if not nit:
        return False
    
    nit = nit.strip().upper()
    
    # Validar formato básico
    if not NIT_PATTERN.match(nit):
        return False
    
    # Validar dígito de verificación
    try:
        if '-' in nit:
            numero, digito_verificador = nit.split('-')
        else:
            numero = nit[:-1]
            digito_verificador = nit[-1]
        
        # Calcular dígito de verificación
        factores = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        suma = 0
        
        # Asegurar que el número tenga 14 dígitos
        numero = numero.zfill(14)
        
        for i in range(14):
            suma += int(numero[13 - i]) * factores[i]
        
        residuo = suma % 11
        if residuo in (0, 1):
            digito_calculado = residuo
        else:
            digito_calculado = 11 - residuo
        
        return str(digito_verificador) == str(digito_calculado)
    except (ValueError, IndexError):
        return False

def crear_directorio_si_no_existe(ruta: Union[str, Path]) -> bool:
    """
    Crea un directorio si no existe.
    
    Args:
        ruta: Ruta del directorio a crear.
        
    Returns:
        bool: True si el directorio existe o se creó correctamente, False en caso contrario.
    """
    try:
        path = Path(ruta)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        if DEBUG:
            import traceback
            traceback.print_exc()
        return False

def limpiar_cadena(cadena: str) -> str:
    """
    Limpia una cadena de texto eliminando espacios extras y caracteres no deseados.
    
    Args:
        cadena: Cadena a limpiar.
        
    Returns:
        str: Cadena limpia.
    """
    if not cadena:
        return ""
    
    # Eliminar espacios al inicio y al final
    cadena = cadena.strip()
    # Reemplazar múltiples espacios por uno solo
    cadena = ' '.join(cadena.split())
    return cadena

def formatear_monto(monto: Union[str, float, int], decimales: int = 2) -> str:
    """
    Formatea un monto numérico como una cadena con separadores de miles y decimales.
    
    Args:
        monto: Valor numérico a formatear.
        decimales: Número de decimales a mostrar.
        
    Returns:
        str: Cadena formateada.
    """
    try:
        # Convertir a float y luego formatear
        valor = float(monto)
        return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(monto)

class Singleton(type):
    """
    Metaclase para implementar el patrón Singleton.
    
    Uso:
        class MiClase(metaclass=Singleton):
            pass
    """
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
