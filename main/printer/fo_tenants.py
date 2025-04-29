import json
import os
import uuid

# Definimos el archivo donde se guardan los tenants
TENANTS_FILE = "tenants.json"

# Cargar tenants desde archivo
def load_tenants(tenant_path):
    if not os.path.exists(tenant_path):
        print(f"Archivo {tenant_path} no encontrado. Se creará uno nuevo al guardar.")
        return {}
    try:
        with open(tenant_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {tenant_path} está dañado o vacío. Se usará un archivo nuevo.")
        return {}

# Guardar tenants en archivo
def save_tenants(tenants,tenant_path):
    if not os.path.exists(tenant_path):
        print(f"Creando nuevo archivo {tenant_path}...")
    with open(tenant_path, "w", encoding="utf-8") as f:
        json.dump(tenants, f, indent=4)
    print("Tenants guardados exitosamente.")

# Mostrar tenants
def list_tenants(tenants):
    base_dir= os.path.dirname(os.path.abspath(__file__))
    if not tenants:
        print("\nNo hay tenants registrados.\n")
        return
    print("\nTenants:")
    for tenant_id, tenant_data in tenants.items():
        print(f"ID: {tenant_id}")
        print(f"  Nombre: {tenant_data['name']}")
        print(f"  Almacenamiento: {tenant_data['storage']}")
        print(f"  Plantilla Email: {tenant_data['email_template']}\n")

# Agregar un tenant
def add_tenant(tenants,tenant_path):
    tenant_id = str(uuid.uuid4())    
    name = input("Ingrese el nombre del tenant: ").strip()
    storage = choose_storage()
    email_template = input("Ingrese la plantilla de email: ").strip()
    
    tenants[tenant_id] = {
        "name": name,
        "storage": storage,
        "email_template": email_template
    }
    save_tenants(tenants,tenant_path)
    print("Tenant agregado exitosamente.\n")

# Editar un tenant
def edit_tenant(tenants,tenant_path):
    tenant_id = input("Ingrese el ID del tenant a editar: ").strip()
    if tenant_id not in tenants:
        print("Tenant no encontrado.")
        return
    
    print("\nDeje vacío el campo que no desee cambiar.\n")
    
    name = input(f"Nuevo nombre ({tenants[tenant_id]['name']}): ").strip()
    storage = input(f"Nuevo almacenamiento actual ({tenants[tenant_id]['storage']}), presione Enter para cambiar o 'no' para dejar igual: ").strip().lower()
    email_template = input(f"Nueva plantilla de email ({tenants[tenant_id]['email_template']}): ").strip()
    
    if name:
        tenants[tenant_id]['name'] = name
    if storage and storage != "no":
        tenants[tenant_id]['storage'] = choose_storage()
    if email_template:
        tenants[tenant_id]['email_template'] = email_template
    
    save_tenants(tenants,tenant_path)
    print("Tenant editado exitosamente.\n")

# Eliminar tenant
def delete_tenant(tenants,tenant_path):
    tenant_id = input("Ingrese el ID del tenant a eliminar: ").strip()
    if tenant_id not in tenants:
        print("Tenant no encontrado.")
        return
    del tenants[tenant_id]
    save_tenants(tenants)
    print("Tenant eliminado exitosamente.\n")

# Elegir tipo de almacenamiento
def choose_storage():
    print("\nSeleccione tipo de almacenamiento:")
    print("1. Drive")
    print("2. AWS")
    print("3. Ruta Física")
    choice = input("Opción: ").strip()
    
    if choice == "1":
        return "drive"
    elif choice == "2":
        return "aws"
    elif choice == "3":
        path = input("Ingrese la ruta física: ").strip()
        if not os.path.exists(path):
            print("Advertencia: La ruta no existe, se guardará igual.")
        return path
    else:
        print("Opción no válida. Se seleccionará 'drive' por defecto.")
        return "drive"

