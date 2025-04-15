from lxml import etree
import os
import re
from datetime import datetime
from plantilla.constants import Constants
import re

def extraer_datos_factura(subFolder,xml_file):
    print("Source xml read: ",xml_file)
    # 1. Leer el XML principal (AttachedDocument)
    with open(xml_file, "rb") as f:
        tree = etree.parse(f)

    # 2. Extraer el contenido de <cbc:Description> (factura embebida)
    nsmap = {
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    }

    description_elem = tree.find('.//cac:Attachment/cac:ExternalReference/cbc:Description', namespaces=nsmap)
    if description_elem is None:
        raise Exception("No se encontró el contenido de la factura.")

    factura_str = description_elem.text.strip()

    # 3. Convertir el string de la factura a XML
    factura_root = etree.fromstring(factura_str.encode('utf-8'))

    invoice_ns = {
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
    }

    # 4. Extraer datos clave de la factura
    factura_id = factura_root.findtext('cbc:ID', namespaces=invoice_ns)
    fecha_emision = factura_root.findtext('cbc:IssueDate', namespaces=invoice_ns)
    moneda = factura_root.findtext('cbc:DocumentCurrencyCode', namespaces=invoice_ns)
    valor_total = factura_root.findtext('.//cbc:PayableAmount', namespaces=invoice_ns)

    # Proveedor
    proveedor_nombre = factura_root.findtext('.//cac:AccountingSupplierParty//cbc:RegistrationName', namespaces=invoice_ns)
    proveedor_nit = factura_root.findtext('.//cac:AccountingSupplierParty//cbc:CompanyID', namespaces=invoice_ns)

    # Cliente
    cliente_nombre = factura_root.findtext('.//cac:AccountingCustomerParty//cbc:RegistrationName', namespaces=invoice_ns)
    cliente_nit = factura_root.findtext('.//cac:AccountingCustomerParty//cbc:CompanyID', namespaces=invoice_ns)

    # Ítems
    items = factura_root.findall('.//cac:InvoiceLine', namespaces=invoice_ns)
    notaCredito = factura_root.findall('.//cac:CreditNoteLine', namespaces=invoice_ns)

    # Crear las líneas de ítems para la salida
    lineas = []
    for item in items:
        descripcion = item.findtext('.//cbc:Description', namespaces=invoice_ns)
        nombre_peaje, numero_placa=extraer_datos_peaje(descripcion)
        cantidad = item.findtext('cbc:InvoicedQuantity', namespaces=invoice_ns)
        precio = item.findtext('.//cbc:PriceAmount', namespaces=invoice_ns)
        lineas.append(f" - {descripcion} | Cantidad: {cantidad} | Precio: {precio}")
    
    for item in notaCredito:
        descripcion = item.findtext('.//cbc:Description', namespaces=invoice_ns)
        nombre_peaje, numero_placa=extraer_datos_peaje(descripcion)
        cantidad = item.findtext('cbc:InvoicedQuantity', namespaces=invoice_ns)
        precio = item.findtext('.//cbc:PriceAmount', namespaces=invoice_ns)
        lineas.append(f" - {descripcion} | Cantidad: {cantidad} | Precio: {precio}")
    
    fecha_convertida = datetime.strptime(fecha_emision, "%Y-%m-%d").strftime("%d/%m/%Y")
    letras = re.match(r"[A-Za-z]+", factura_id).group()
    numeros = re.search(r"\d+", factura_id).group()
    fila = {
        "FacturaID": factura_id,
        "FacturaCabecera": letras,
        "FacturaNumero": numeros,
        "FechaEmision": fecha_convertida,
        "ValorTotal": valor_total,
        "Moneda": moneda,
        "ProveedorNombre": proveedor_nombre,
        "ProveedorNIT": proveedor_nit,
        "ClienteNombre": cliente_nombre,
        "ClienteNIT": cliente_nit,
        "NombrePeaje": str(Constants.PEAJE.value[0])+str(" ") + str(nombre_peaje),
        "NumeroPlaca": numero_placa,
        "Items": lineas,
        "xml": xml_file
    }
   
    return factura_id, fila

def extraer_datos_peaje(descripcion):
    # Expresión regular para extraer el nombre del peaje y el número de placa
    # Asumimos que el nombre del peaje es la última palabra antes del número de placa
    # y el número de placa es una cadena alfanumérica
    patron = r"(\D+)\s([A-Za-z0-9]+)\s\d+"  # (\D+) -> Nombre del peaje, ([A-Za-z0-9]+) -> Placa
    
    # Buscar el patrón en la descripción
    resultado = re.search(patron, descripcion)
    
    if resultado:
        nombre_peaje =extraer_name_peaje(resultado.group(1).strip())  # Nombre del peaje (antes de la placa)
        numero_placa = resultado.group(2).strip()  # Número de placa
        
        return nombre_peaje, numero_placa
    else:
        nombre_peaje = "---"  # Establecer valor predeterminado
        numero_placa = "---"  # Establecer valor predeterminado
    
    return nombre_peaje, numero_placa  # En caso de que no se encuentre el patrón

def extraer_name_peaje(descripcion):
    # Expresión regular para extraer el nombre del peaje (última palabra en la descripción)
    patron = r"\s([A-Za-z]+)$"  # Busca la última palabra al final de la cadena
    
    # Buscar el patrón en la descripción
    resultado = re.search(patron, descripcion)
    
    if resultado:
        nombre_peaje = resultado.group(1).strip()  # Última palabra como nombre del peaje
        return nombre_peaje
    else:
        return None  # Si no se encuentra el nombre del peaje


# Ejemplo de uso
'''
fileXml = os.path.join(os.getcwd(), "testXml","ad090047025200025008b3f11.xml")
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)

fileXml = os.path.join(os.getcwd(), "testXml","ad090047025200025008b3bb8.xml")
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)
'''
