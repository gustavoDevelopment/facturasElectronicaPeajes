"""
Módulo para la gestión de tenants en Facturae Optimus.

Este módulo proporciona funcionalidades para cargar, guardar, listar, agregar, editar y eliminar
configuraciones de tenants, así como para gestionar sus almacenamientos asociados.
"""
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from config import DEBUG
from logger import get_logger
from utils import normalizar_texto, crear_directorio_si_no_existe

# Configuración del logger
logger = get_logger(__name__)

# Constantes
TENANTS_FILE = "tenants.json"
STORAGE_TYPES = {
    "1": "drive",
    "2": "aws",
    "3": "ruta_fisica"
}
STORAGE_NAMES = {
    "drive": "Google Drive",
    "aws": "Amazon Web Services (S3)",
    "ruta_fisica": "Ruta Física Local"
}

# Excepciones personalizadas
class TenantError(Exception):
    """Excepción base para errores relacionados con tenants."""
    pass

class TenantNotFoundError(TenantError):
    """Se lanza cuando no se encuentra un tenant."""
    pass

class TenantValidationError(TenantError):
    """Se lanza cuando falla la validación de datos del tenant."""
    pass

def load_tenants(tenant_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Carga los tenants desde un archivo JSON.
    
    Args:
        tenant_path: Ruta al archivo de configuración de tenants.
        
    Returns:
        Dict con los tenants cargados o un diccionario vacío si hay un error.
    """
    try:
        path = Path(tenant_path)
        if not path.exists():
            logger.warning(f"Archivo {tenant_path} no encontrado. Se creará uno nuevo al guardar.")
            return {}
            
        with open(path, "r", encoding="utf-8") as f:
            tenants = json.load(f)
            logger.debug(f"Cargados {len(tenants)} tenants desde {tenant_path}")
            return tenants
            
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar el archivo {tenant_path}: {str(e)}")
        raise TenantError("El archivo de configuración de tenants está dañado o tiene un formato incorrecto.")
    except Exception as e:
        logger.error(f"Error inesperado al cargar tenants: {str(e)}")
        if DEBUG:
            logger.exception("Detalles del error:")
        raise TenantError("No se pudieron cargar los tenants. Por favor, verifique el archivo de configuración.")

def save_tenants(tenants: Dict[str, Dict[str, Any]], tenant_path: str) -> None:
    """
    Guarda los tenants en un archivo JSON.
    
    Args:
        tenants: Diccionario con los datos de los tenants.
        tenant_path: Ruta donde se guardará el archivo.
        
    Raises:
        TenantError: Si ocurre un error al guardar los datos.
    """
    try:
        path = Path(tenant_path)
        # Asegurar que el directorio existe
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tenants, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Configuración de {len(tenants)} tenants guardada en {tenant_path}")
        
    except (IOError, OSError) as e:
        error_msg = f"Error de E/S al guardar los tenants: {str(e)}"
        logger.error(error_msg)
        raise TenantError(error_msg)
    except Exception as e:
        error_msg = f"Error inesperado al guardar los tenants: {str(e)}"
        logger.error(error_msg)
        if DEBUG:
            logger.exception("Detalles del error:")
        raise TenantError("No se pudieron guardar los cambios. Por favor, intente nuevamente.")

def list_tenants(tenants: Dict[str, Dict[str, Any]]) -> None:
    """
    Muestra la lista de tenants registrados.
    
    Args:
        tenants: Diccionario con los datos de los tenants.
    """
    if not tenants:
        print("\nNo hay tenants registrados.")
        return
    
    print("\n" + "=" * 80)
    print(f"{'ID':<38} | {'NOMBRE':<20} | {'ALMACENAMIENTO':<15} | PLANTILLA EMAIL")
    print("-" * 80)
    
    for tenant_id, data in tenants.items():
        storage_name = STORAGE_NAMES.get(data.get('storage', ''), 'Desconocido')
        print(f"{tenant_id} | {data.get('name', '')[:20]:<20} | {storage_name:<15} | {data.get('email_template', '')}")
    
    print("=" * 80 + "\n")

def add_tenant(tenants: Dict[str, Dict[str, Any]], tenant_path: str) -> None:
    """
    Agrega un nuevo tenant.
    
    Args:
        tenants: Diccionario con los datos de los tenants.
        tenant_path: Ruta al archivo de configuración de tenants.
    """
    try:
        print("\n" + "=" * 50)
        print("  AGREGAR NUEVO TENANT")
        print("=" * 50)
        
        # Validar nombre
        while True:
            name = input("\nNombre del tenant: ").strip()
            if not name:
                print("❌ El nombre no puede estar vacío. Intente nuevamente.")
                continue
            if any(t['name'].lower() == name.lower() for t in tenants.values()):
                print("❌ Ya existe un tenant con ese nombre. Intente con otro.")
                continue
            break
            
        # Seleccionar almacenamiento
        storage = choose_storage()
        
        # Validar plantilla de correo
        while True:
            email_template = input("\nPlantilla de email: ").strip()
            if not email_template:
                print("❌ La plantilla de email es obligatoria.")
                continue
            if '@' not in email_template:
                print("❌ La plantilla debe ser una dirección de correo electrónico válida.")
                continue
            break
        
        # Crear el tenant
        tenant_id = str(uuid.uuid4())
        tenants[tenant_id] = {
            'name': name,
            'storage': storage,
            'email_template': email_template,
            'created_at': str(uuid.uuid1())
        }
        
        # Guardar los cambios
        save_tenants(tenants, tenant_path)
        print(f"\n✅ Tenant '{name}' agregado exitosamente con ID: {tenant_id}")
        
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        logger.error(f"Error al agregar tenant: {str(e)}")
        if DEBUG:
            logger.exception("Detalles del error:")
        print("\n❌ No se pudo agregar el tenant. Por favor, intente nuevamente.")

def edit_tenant(tenants: Dict[str, Dict[str, Any]], tenant_path: str) -> None:
    """
    Edita un tenant existente.
    
    Args:
        tenants: Diccionario con los datos de los tenants.
        tenant_path: Ruta al archivo de configuración de tenants.
    """
    if not tenants:
        print("\nNo hay tenants registrados para editar.")
        return
    
    try:
        # Mostrar lista de tenants para facilitar la selección
        list_tenants(tenants)
        
        while True:
            tenant_id = input("\nIngrese el ID del tenant a editar (o 'q' para cancelar): ").strip()
            
            if tenant_id.lower() == 'q':
                print("Operación cancelada.")
                return
                
            if tenant_id not in tenants:
                print("❌ ID de tenant no válido. Intente nuevamente o presione 'q' para cancelar.")
                continue
                
            tenant = tenants[tenant_id]
            print(f"\nEditando tenant: {tenant.get('name', 'Sin nombre')} (ID: {tenant_id})")
            print("Deje el campo en blanco para mantener el valor actual.\n")
            
            # Editar nombre
            while True:
                new_name = input(f"Nuevo nombre ({tenant.get('name', 'Sin nombre')}): ").strip()
                if not new_name:  # Mantener valor actual
                    new_name = tenant.get('name')
                    break
                    
                # Validar que el nombre no esté en uso por otro tenant
                if any(t['name'].lower() == new_name.lower() and tid != tenant_id 
                      for tid, t in tenants.items()):
                    print("❌ Ya existe otro tenant con ese nombre. Intente con otro.")
                    continue
                break
            
            # Preguntar si se desea cambiar el almacenamiento
            change_storage = input(f"\n¿Desea cambiar el almacenamiento actual ({tenant.get('storage', 'No definido')})? (s/n): ").strip().lower()
            new_storage = choose_storage() if change_storage == 's' else tenant.get('storage')
            
            # Editar plantilla de correo
            while True:
                new_email = input(f"\nNueva plantilla de email ({tenant.get('email_template', 'No definida')}): ").strip()
                if not new_email:  # Mantener valor actual
                    new_email = tenant.get('email_template')
                    break
                    
                if '@' not in new_email:
                    print("❌ La plantilla debe ser una dirección de correo electrónico válida.")
                    continue
                break
            
            # Confirmar cambios
            print("\nResumen de cambios:")
            print(f"  Nombre: {tenant.get('name')} → {new_name}")
            print(f"  Almacenamiento: {tenant.get('storage')} → {new_storage}")
            print(f"  Plantilla de email: {tenant.get('email_template')} → {new_email}")
            
            confirm = input("\n¿Desea guardar los cambios? (s/n): ").strip().lower()
            if confirm != 's':
                print("Operación cancelada. No se realizaron cambios.")
                return
            
            # Actualizar datos del tenant
            tenant['name'] = new_name
            tenant['storage'] = new_storage
            tenant['email_template'] = new_email
            tenant['updated_at'] = str(uuid.uuid1())
            
            # Guardar cambios
            save_tenants(tenants, tenant_path)
            print("\n✅ Cambios guardados exitosamente.")
            break
            
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        logger.error(f"Error al editar tenant: {str(e)}")
        if DEBUG:
            logger.exception("Detalles del error:")
        print("\n❌ No se pudo editar el tenant. Por favor, intente nuevamente.")

def delete_tenant(tenants: Dict[str, Dict[str, Any]], tenant_path: str) -> None:
    """
    Elimina un tenant existente.
    
    Args:
        tenants: Diccionario con los datos de los tenants.
        tenant_path: Ruta al archivo de configuración de tenants.
    """
    if not tenants:
        print("\nNo hay tenants registrados para eliminar.")
        return
    
    try:
        # Mostrar lista de tenants para facilitar la selección
        list_tenants(tenants)
        
        while True:
            tenant_id = input("\nIngrese el ID del tenant a eliminar (o 'q' para cancelar): ").strip()
            
            if tenant_id.lower() == 'q':
                print("Operación cancelada.")
                return
                
            if tenant_id not in tenants:
                print("❌ ID de tenant no válido. Intente nuevamente o presione 'q' para cancelar.")
                continue
                
            tenant_name = tenants[tenant_id].get('name', 'Sin nombre')
            confirm = input(f"\n⚠️  ¿Está seguro de eliminar el tenant '{tenant_name}'? Esta acción no se puede deshacer. (s/n): ").strip().lower()
            
            if confirm != 's':
                print("Operación cancelada. No se eliminó ningún tenant.")
                return
            
            # Eliminar tenant
            del tenants[tenant_id]
            
            # Guardar cambios
            save_tenants(tenants, tenant_path)
            print(f"\n✅ Tenant '{tenant_name}' eliminado exitosamente.")
            break
            
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        logger.error(f"Error al eliminar tenant: {str(e)}")
        if DEBUG:
            logger.exception("Detalles del error:")
        print("\n❌ No se pudo eliminar el tenant. Por favor, intente nuevamente.")

def choose_storage() -> str:
    """
    Muestra un menú para seleccionar el tipo de almacenamiento.
    
    Returns:
        str: Tipo de almacenamiento seleccionado.
    """
    while True:
        print("\nTipos de almacenamiento disponibles:")
        for key, value in STORAGE_NAMES.items():
            print(f"  {key}: {value}")
        
        choice = input("\nSeleccione el tipo de almacenamiento (1-3): ").strip()
        
        if choice in STORAGE_TYPES:
            storage_type = STORAGE_TYPES[choice]
            
            # Si es ruta física, pedir la ruta
            if storage_type == "ruta_fisica":
                while True:
                    path = input("\nIngrese la ruta física para el almacenamiento: ").strip()
                    if not path:
                        print("❌ La ruta no puede estar vacía.")
                        continue
                        
                    path = os.path.expanduser(path)  # Expandir ~ a la ruta del usuario
                    
                    # Verificar si la ruta existe
                    if not os.path.exists(path):
                        create = input("⚠️  La ruta no existe. ¿Desea crearla? (s/n): ").strip().lower()
                        if create == 's':
                            try:
                                os.makedirs(path, exist_ok=True)
                                print(f"✅ Directorio creado exitosamente en: {path}")
                            except Exception as e:
                                print(f"❌ Error al crear el directorio: {str(e)}")
                                continue
                        else:
                            print("Se usará la ruta sin verificación.")
                    
                    return f"ruta_fisica:{path}"
            
            return storage_type
        else:
            print("❌ Opción no válida. Por favor, seleccione un número del 1 al 3.")
