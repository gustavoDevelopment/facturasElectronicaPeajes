import json
import os
import uuid
from printer.fo_tenants import load_tenants
from printer.fo_tenants import list_tenants
from printer.fo_tenants import add_tenant
from printer.fo_tenants import edit_tenant
from printer.fo_tenants import delete_tenant
from printer.fo_tenants import TENANTS_FILE
from disparadores.fo_disparadores import do_on_facture_optimus


# Menú principal
def main_menu():
    tenant_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"build","tenant",TENANTS_FILE)
    tenants = load_tenants(tenant_path)
    
    while True:
        mostrar_menu()        
        choice = input("Seleccione una opción: ").strip()
        
        if choice == "1":
            list_tenants(tenants)
        elif choice == "2":
            add_tenant(tenants,tenant_path)
        elif choice == "3":
            edit_tenant(tenants,tenant_path)
        elif choice == "4":
            delete_tenant(tenants,tenant_path)
        elif choice == "5":
            do_on_facture_optimus(tenants,tenant_path)
        elif choice == "0":
            print("Saliendo...")
            break
        else:
            print("Opción inválida. Intente de nuevo.")

def mostrar_menu():
    print("\n" + "="*45)
    print("         📄 Facturae Optimus 📄")
    print("="*45)
    print(" [1] Listar tenants")
    print(" [2] Agregar tenant")
    print(" [3] Editar tenant")
    print(" [4] Eliminar tenant")
    print(" [5] Ejecutar Facturae Optimus")
    print(" [0] Salir")
    print("="*45)



