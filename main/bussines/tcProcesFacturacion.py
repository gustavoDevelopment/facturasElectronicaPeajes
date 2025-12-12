from lxml import etree
import os
import re
from datetime import datetime
from plantilla.constants import Constants
import re

def extraer_datos_factura(xml_file):
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
    invoiceTypeXml= Constants.FACTURA.value[0]
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

    # Nota Credito Factura Relacionada
    relatedInvoice= factura_root.findtext('.//cbc:ReferenceID', namespaces=invoice_ns)
    if relatedInvoice is None:
        relatedInvoice="00000"

    # Crear las líneas de ítems para la salida
    lineas = []
    l,l2 = [],[]
    peaje=""
    peaje1=""
    placa=""
    placa1 = ""

    l,peaje,placa=(procesar_items(items, invoice_ns, incluir_referencia=True))
    l2,peaje1,placa1=(procesar_items(notaCredito, invoice_ns, incluir_referencia=True))
    
    nombre_peaje=peaje
    numero_placa=placa

    nombre_peaje=peaje1
    numero_placa=placa1
    lineas.extend(l)
    lineas.extend(l2)

    for item in items:
        descripcion = item.findtext('.//cbc:Description', namespaces=invoice_ns)
        nombre_peaje, numero_placa=extraer_datos_peaje(descripcion)
        referenciaItem = item.findtext('.//cac:SellersItemIdentification/cbc:ID', namespaces=invoice_ns)
        cantidad = item.findtext('cbc:InvoicedQuantity', namespaces=invoice_ns)
        precio = item.findtext('.//cbc:PriceAmount', namespaces=invoice_ns)
        lineas.append(f"| Referencia:{referenciaItem} |Item: {descripcion} | Cantidad: {cantidad} | Precio: {precio}")
    
    for item in notaCredito:    
        descripcion = item.findtext('.//cbc:Description', namespaces=invoice_ns)
        nombre_peaje, numero_placa=extraer_datos_peaje(descripcion)
        referenciaItem = item.findtext('.//cac:SellersItemIdentification/cbc:ID', namespaces=invoice_ns)
        cantidad = item.findtext('cbc:InvoicedQuantity', namespaces=invoice_ns)
        precio = item.findtext('.//cbc:PriceAmount', namespaces=invoice_ns)
        lineas.append(f" - {descripcion} | Cantidad: {cantidad} | Precio: {precio}")

    refs = [e.text for e in item.findall('.//cbc:ReferenceID', namespaces=invoice_ns)]  
    fecha_convertida = datetime.strptime(fecha_emision, "%Y-%m-%d").strftime("%d/%m/%Y")
    letras = re.match(r"[A-Za-z]+", factura_id).group()
    numeros = re.search(r"\d+", factura_id).group()

    if letras == Constants.FACTURA_CABECERA_NOTA_CREDITO.value[0]:
        invoiceTypeXml= Constants.NOTA_CREDITO.value[0]

    fila = {
        "InvoiceType": str(invoiceTypeXml),
        "FacturaID": factura_id,
        "FacturaCabecera": str(letras),
        "FacturaNumero": numeros,
        "FechaEmision": fecha_convertida,
        "ValorTotal": limpiar_decimal(valor_total),
        "Moneda": moneda,
        "ProveedorNombre": proveedor_nombre,
        "ProveedorNIT": proveedor_nit,
        "ClienteNombre": cliente_nombre,
        "ClienteNIT": cliente_nit,
        "NombrePeaje": nombre_peaje,
        "NumeroPlaca": numero_placa,
        "Items": lineas,
        "FacturaRelacionada" : re.search(r"\d+", relatedInvoice).group(),
        "xml": xml_file
    }
   
    return factura_id, fila

def limpiar_decimal(valor):
    if float(valor).is_integer():
        return str(int(float(valor)))
    else:
        return str(valor)

def extraer_datos_peaje(descripcion):
    # Expresión regular para extraer el nombre del peaje y el número de placa
    # Asumimos que el nombre del peaje es la última palabra antes del número de placa
    # y el número de placa es una cadena alfanumérica
    patron = r"(\D+)\s([A-Za-z0-9]+)\s\d+"  # (\D+) -> Nombre del peaje, ([A-Za-z0-9]+) -> Placa
    
    # Buscar el patrón en la descripción
    resultado = re.search(patron, descripcion)
    
    if resultado:
        nombre_peaje =extraer_name_peaje(resultado.group(1).strip())  # Nombre del peaje (antes de la placa)
        nombre_peaje= str(Constants.PEAJE.value[0])+str(" ") + str(nombre_peaje)
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

def obtener_valor(node, path, ns):
    """Devuelve el texto del nodo encontrado o 'N/A' si no existe"""
    result = node.find(path, namespaces=ns)
    return result.text if result is not None else 'N/A'

def procesar_items(items, ns, incluir_referencia=True):
    lineas = []
    nombre_peaje =""
    numero_placa =""
    for item in items:
        descripcion = obtener_valor(item, './/cbc:Description', ns)
        nombre_peaje, numero_placa = extraer_datos_peaje(descripcion)

        cantidad = obtener_valor(item, 'cbc:InvoicedQuantity', ns)
        precio = obtener_valor(item, './/cbc:PriceAmount', ns)

        if incluir_referencia:
            referencia = obtener_valor(item, './/cac:SellersItemIdentification/cbc:ID', ns)
            linea = f"| Referencia: {referencia} | Item: {descripcion} | Cantidad: {cantidad} | Precio: {precio} |"
        else:
            linea = f"- {descripcion} | Cantidad: {cantidad} | Precio: {precio} |"

fileXml = os.path.join(os.getcwd(), "testXml","ad090047025200025008b3bb8.xml")
factura_id, texto_factura = extraer_datos_factura(fileXml)
print(texto_factura)
'''


