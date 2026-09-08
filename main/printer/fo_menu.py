"""
Módulo que maneja la interfaz de línea de comandos para Facturae Optimus.

Proporciona un menú interactivo para gestionar tenants y ejecutar operaciones.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, NoReturn

# Importaciones locales
from config import TENANTS_DIR, DEBUG, get_config
from logger import get_logger
from printer.fo_tenants import (
    load_tenants, list_tenants, add_tenant,
    edit_tenant, delete_tenant, TENANTS_FILE
)
from printer.fo_email_config import configurar_email_tenant
from disparadores.fo_disparadores import do_on_facture_optimus

# Configuración del logger
logger = get_logger(__name__)

class Menu:
    """Clase que maneja el menú principal de la aplicación."""
    
    def __init__(self):
        """Inicializa el menú con la configuración necesaria."""
        self.tenant_path = TENANTS_DIR / TENANTS_FILE
        self.tenants = {}
        self.running = True
        
        # Asegurar que el directorio de tenants existe
        self.tenant_path.parent.mkdir(parents=True, exist_ok=True)
    
    def cargar_tenants(self) -> bool:
        """
        Carga la configuración de tenants desde el archivo.
        
        Returns:
            bool: True si se cargaron los tenants correctamente, False en caso contrario.
        """
        try:
            logger.debug(f"Cargando configuración de tenants desde: {self.tenant_path}")
            self.tenants = load_tenants(str(self.tenant_path))
            return True
        except Exception as e:
            logger.error(f"Error al cargar la configuración de tenants: {str(e)}")
            if DEBUG:
                logger.exception("Detalles del error:")
            return False
    
    def mostrar_menu(self) -> None:
        """Muestra el menú principal de la aplicación."""
        menu = """
        {line}
                 📄 Facturae Optimus 📄
        {line}
         [1] Listar tenants
         [2] Agregar tenant
         [3] Editar tenant
         [4] Eliminar tenant
         [5] Ejecutar Facturae Optimus
         [6] Configurar email de tenant (password / OAuth2)
         [0] Salir
        {line}
        """.format(line="="*50)
        print(menu)
    
    def procesar_opcion(self, opcion: str) -> None:
        """
        Procesa la opción seleccionada por el usuario.
        
        Args:
            opcion: Opción seleccionada por el usuario.
        """
        try:
            if opcion == "1":
                list_tenants(self.tenants)
            elif opcion == "2":
                add_tenant(self.tenants, str(self.tenant_path))
            elif opcion == "3":
                edit_tenant(self.tenants, str(self.tenant_path))
            elif opcion == "4":
                delete_tenant(self.tenants, str(self.tenant_path))
            elif opcion == "5":
                do_on_facture_optimus(self.tenants, str(self.tenant_path))
            elif opcion == "6":
                if not self.tenants:
                    print("\nNo hay tenants registrados.")
                else:
                    list_tenants(self.tenants)
                    tenant_id = input("\nIngrese el ID del tenant a configurar: ").strip()
                    if tenant_id in self.tenants:
                        configurar_email_tenant(tenant_id)
                    else:
                        print("❌ ID de tenant no válido.")
            elif opcion == "0":
                self.salir()
            else:
                print("\n❌ Opción inválida. Por favor, intente de nuevo.")
        except Exception as e:
            logger.error(f"Error al procesar la opción {opcion}: {str(e)}")
            if DEBUG:
                logger.exception("Detalles del error:")
    
    def salir(self) -> None:
        """Finaliza la ejecución del menú."""
        logger.info("Saliendo de la aplicación...")
        self.running = False
    
    def ejecutar(self) -> None:
        """Ejecuta el bucle principal del menú."""
        if not self.cargar_tenants():
            logger.error("No se pudo cargar la configuración de tenants. Saliendo...")
            return
        
        logger.info("Menú principal iniciado")
        
        while self.running:
            try:
                self.mostrar_menu()
                opcion = input("\nSeleccione una opción: ").strip()
                self.procesar_opcion(opcion)
                
            except KeyboardInterrupt:
                print("\n\nOperación cancelada por el usuario.")
                confirmacion = input("¿Desea salir? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.salir()
            except Exception as e:
                logger.error(f"Error inesperado: {str(e)}")
                if DEBUG:
                    logger.exception("Detalles del error:")
                
                # Si hay un error crítico, preguntar si se desea continuar
                if input("¿Desea continuar? (s/n): ").strip().lower() != 's':
                    self.salir()

def main_menu() -> None:
    """
    Función principal que maneja el flujo del menú.
    
    Carga la configuración de tenants y muestra un menú interactivo
    para gestionarlos y ejecutar operaciones.
    """
    try:
        menu = Menu()
        menu.ejecutar()
    except Exception as e:
        logger.critical(f"Error crítico en el menú principal: {str(e)}", exc_info=True)
        print("\n❌ Ocurrió un error crítico. Por favor, revise los logs para más detalles.")
        sys.exit(1)
