"""
Módulo para el procesamiento de facturas electrónicas en formato UBL.

Este módulo proporciona funcionalidades para extraer y procesar información
de facturas electrónicas en formato UBL (Universal Business Language).
"""
import re
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from lxml import etree
from pathlib import Path

from main.config import DEBUG
from main.logger import get_logger
from main.plantilla.constants import Constants

# Configuración del logger
logger = get_logger(__name__)

# Espacios de nombres XML
XML_NAMESPACES = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

# Expresiones regulares
INVOICE_ID_PATTERN = re.compile(r'^(?P<prefix>[A-Za-z0-9-]+?)(?P<number>\d+)$')
TOLL_DATA_PATTERN = re.compile(r'(?P<peaje>\D+?)\s+(?P<placa>[A-Za-z0-9]+)\s+\d+')
TOLL_NAME_PATTERN = re.compile(r'\s([A-Za-z]+)$')

class InvoiceProcessingError(Exception):
    """Excepción base para errores en el procesamiento de facturas."""
    pass

class InvoiceFormatError(InvoiceProcessingError):
    """Se lanza cuando el formato de la factura no es válido."""
    pass

class InvoiceDataError(InvoiceProcessingError):
    """Se lanza cuando faltan datos requeridos en la factura."""
    pass

class InvoiceProcessor:
    """Clase para procesar facturas electrónicas en formato UBL."""
    
    def __init__(self):
        """Inicializa el procesador de facturas."""
        # No es necesario instanciar Constants, ya que es una enumeración
    
    def process_invoice(self, xml_file: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa un archivo XML de factura y extrae la información relevante.
        
        Args:
            xml_file: Ruta al archivo XML de la factura.
            
        Returns:
            Una tupla con (factura_id, datos_factura) donde datos_factura es un diccionario
            con la información extraída de la factura.
            
        Raises:
            InvoiceProcessingError: Si ocurre un error al procesar la factura.
            FileNotFoundError: Si el archivo no existe.
        """
        try:
            # Validar que el archivo existe
            xml_path = Path(xml_file)
            if not xml_path.is_file():
                error_msg = f"El archivo no existe: {xml_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            logger.info(f"Procesando factura: {xml_path}")
            
            # 1. Leer y validar el XML
            try:
                tree = etree.parse(str(xml_path))
                root = tree.getroot()
            except etree.XMLSyntaxError as e:
                error_msg = f"Error de sintaxis XML en {xml_path}: {str(e)}"
                logger.error(error_msg)
                raise InvoiceFormatError(error_msg) from e
            
            # 2. Extraer la factura embebida si es necesario
            invoice_root = self._extract_embedded_invoice(root)
            
            # 3. Extraer datos básicos de la factura
            invoice_data = self._extract_basic_invoice_data(invoice_root)
            
            # 4. Extraer datos del proveedor y cliente
            self._extract_parties_data(invoice_root, invoice_data)
            
            # 5. Procesar ítems de la factura
            self._process_invoice_items(invoice_root, invoice_data)
            
            # 6. Procesar datos adicionales
            self._process_additional_data(invoice_root, invoice_data)
            
            # 7. Agregar metadatos
            invoice_data['xml_file'] = str(xml_path)
            invoice_data['processing_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"Factura {invoice_data['invoice_id']} procesada exitosamente")
            
            return invoice_data['invoice_id'], invoice_data
            
        except Exception as e:
            error_msg = f"Error al procesar la factura {xml_file}: {str(e)}"
            logger.error(error_msg)
            if DEBUG:
                logger.exception("Detalles del error:")
            
            if not isinstance(e, InvoiceProcessingError):
                raise InvoiceProcessingError(error_msg) from e
            raise
    
    def _extract_embedded_invoice(self, root: etree._Element) -> etree._Element:
        """
        Extrae la factura embebida en un documento AttachedDocument si es necesario.
        
        Args:
            root: Elemento raíz del documento XML.
            
        Returns:
            Elemento raíz de la factura.
            
        Raises:
            InvoiceFormatError: Si no se puede extraer la factura embebida.
        """
        # Si el documento es una factura directamente, devolver el mismo elemento
        if root.tag.endswith('}Invoice') or root.tag.endswith('}CreditNote'):
            return root
            
        # Intentar extraer la factura embebida de un AttachedDocument
        try:
            description_elem = root.find(
                './/cac:Attachment/cac:ExternalReference/cbc:Description', 
                namespaces=XML_NAMESPACES
            )
            
            if description_elem is None or not description_elem.text:
                raise InvoiceFormatError("No se encontró el contenido de la factura embebida.")
            
            # Obtener el texto del elemento y limpiarlo
            invoice_content = description_elem.text.strip()
            
            # Si el contenido está en CDATA, extraer el contenido interno
            if '<![CDATA[' in invoice_content and ']]>' in invoice_content:
                invoice_content = invoice_content.split('<![CDATA[')[1].split(']]>')[0].strip()
            
            # Convertir el string de la factura a XML
            try:
                return etree.fromstring(invoice_content.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                raise InvoiceFormatError(f"El contenido embebido no es un XML válido: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error al extraer factura embebida: {str(e)}")
            raise InvoiceFormatError(f"No se pudo extraer la factura embebida: {str(e)}") from e
    
    def _extract_basic_invoice_data(self, invoice_root: etree._Element) -> Dict[str, Any]:
        """
        Extrae los datos básicos de la factura.
        
        Args:
            invoice_root: Elemento raíz de la factura.
            
        Returns:
            Diccionario con los datos básicos de la factura.
        """
        # Determinar el tipo de documento
        is_credit_note = invoice_root.tag.endswith('}CreditNote')
        
        # Extraer ID de la factura
        invoice_id = self._get_element_text(invoice_root, 'cbc:ID')
        if not invoice_id:
            raise InvoiceDataError("La factura no tiene un ID válido")
        
        # Extraer fecha de emisión
        issue_date = self._get_element_text(invoice_root, 'cbc:IssueDate')
        if not issue_date:
            raise InvoiceDataError("La factura no tiene fecha de emisión")
            
        try:
            # Convertir fecha al formato DD/MM/YYYY
            issue_date_dt = datetime.strptime(issue_date, "%Y-%m-%d")
            formatted_date = issue_date_dt.strftime("%d/%m/%Y")
        except ValueError:
            formatted_date = issue_date
        
        # Extraer prefijo y número de factura
        prefix, number = self._extract_invoice_parts(invoice_id)
        
        # Para notas de crédito, extraer la factura relacionada
        related_invoice = None
        if is_credit_note:
            # Primero intentar con InvoiceDocumentReference (estándar UBL)
            related_invoice = self._get_element_text(invoice_root, 'cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID')
            # Si no se encuentra, intentar con ReferenceID (formato alternativo)
            if not related_invoice:
                related_invoice = self._get_element_text(invoice_root, 'cbc:ReferenceID')
                # Si aún no se encuentra, intentar sin namespaces
                if not related_invoice:
                    related_invoice = self._get_element_text(invoice_root, './/*[local-name()="ReferenceID"]')
            
            # Si encontramos una factura relacionada, usarla para el prefijo
            if related_invoice:
                # Guardar el ID completo de la factura relacionada
                related_invoice = related_invoice.strip()
                # Extraer el prefijo de la factura relacionada
                related_prefix, _ = self._extract_invoice_parts(related_invoice)
                if related_prefix:
                    prefix = related_prefix
                else:
                    prefix = related_invoice
                number = ''
        
        # Asegurar que el prefijo no termine con guión
        if prefix and prefix.endswith('-'):
            prefix = prefix[:-1]
        
        # Extraer moneda y monto total
        currency = self._get_element_text(invoice_root, 'cbc:DocumentCurrencyCode', default="COP")
        
        amount_path = 'cac:LegalMonetaryTotal/cbc:PayableAmount' if is_credit_note else 'cac:LegalMonetaryTotal/cbc:PayableAmount'
        total_amount = self._get_element_text(invoice_root, amount_path, default="0")
        
        # Crear el diccionario de datos de la factura
        invoice_data = {
            'invoice_type': 'CREDIT_NOTE' if is_credit_note else 'INVOICE',
            'invoice_id': invoice_id,
            'invoice_prefix': prefix,
            'invoice_number': number,
            'issue_date': issue_date,
            'formatted_issue_date': formatted_date,
            'currency': currency,
            'total_amount': self._clean_decimal(total_amount, force_int=False),
            'items': [],
            'toll_name': None,
            'plate_number': None
        }
        
        # Solo agregar related_invoice si es una nota de crédito
        if is_credit_note:
            invoice_data['related_invoice'] = related_invoice
            
        return invoice_data
    
    def _extract_parties_data(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]) -> None:
        """
        Extrae los datos del proveedor y cliente de la factura.
        
        Args:
            invoice_root: Elemento raíz de la factura.
            invoice_data: Diccionario donde se almacenarán los datos.
        """
        # Extraer datos del proveedor
        supplier_party = invoice_root.find('.//cac:AccountingSupplierParty', XML_NAMESPACES)
        if supplier_party is not None:
            invoice_data['supplier_name'] = self._get_element_text(
                supplier_party, './/cac:Party//cbc:RegistrationName'
            )
            invoice_data['supplier_tax_id'] = self._get_element_text(
                supplier_party, './/cac:Party//cbc:CompanyID'
            )
        
        # Extraer datos del cliente
        customer_party = invoice_root.find('.//cac:AccountingCustomerParty', XML_NAMESPACES)
        if customer_party is not None:
            invoice_data['customer_name'] = self._get_element_text(
                customer_party, './/cac:Party//cbc:RegistrationName'
            )
            invoice_data['customer_tax_id'] = self._get_element_text(
                customer_party, './/cac:Party//cbc:CompanyID'
            )
    
    def _process_invoice_items(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]) -> None:
        """
        Procesa los ítems de la factura.
        
        Args:
            invoice_root: Elemento raíz de la factura.
            invoice_data: Diccionario donde se almacenarán los ítems.
        """
        is_credit_note = invoice_data['invoice_type'] == 'CREDIT_NOTE'
        items_path = './/cac:CreditNoteLine' if is_credit_note else './/cac:InvoiceLine'
        
        for item in invoice_root.findall(items_path, XML_NAMESPACES):
            try:
                item_data = self._extract_item_data(item)
                if item_data:
                    invoice_data['items'].append(item_data)
                    
                    # Extraer datos de peaje si no se han extraído antes
                    if not invoice_data['toll_name'] and item_data.get('description'):
                        toll_data = self._extract_toll_data(item_data['description'])
                        if toll_data['toll_name'] and toll_data['plate_number']:
                            invoice_data['toll_name'] = toll_data['toll_name']
                            invoice_data['plate_number'] = toll_data['plate_number']
                            
            except Exception as e:
                logger.warning(f"Error al procesar ítem de factura: {str(e)}")
                if DEBUG:
                    logger.exception("Detalles del error:")
    
    def _extract_item_data(self, item: etree._Element) -> Dict[str, Any]:
        """
        Extrae los datos de un ítem de factura.
        
        Args:
            item: Elemento XML del ítem.
            
        Returns:
            Diccionario con los datos del ítem.
        """
        description = self._get_element_text(item, './/cbc:Description')
        quantity = self._get_element_text(item, 'cbc:InvoicedQuantity', default="1")
        price = self._get_element_text(item, './/cbc:PriceAmount', default="0")
        reference = self._get_element_text(item, './/cac:SellersItemIdentification/cbc:ID')
        
        return {
            'description': description,
            'quantity': self._clean_decimal(quantity, force_int=True),
            'price': self._clean_decimal(price, force_int=False),
            'reference': reference,
            'line_total': str(float(self._clean_decimal(quantity, force_int=True)) * float(self._clean_decimal(price, '0', force_int=False)))
        }
    
    def _process_additional_data(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]) -> None:
        """
        Procesa datos adicionales de la factura.
        
        Args:
            invoice_root: Elemento raíz de la factura.
            invoice_data: Diccionario donde se almacenarán los datos.
        """
        # Extraer factura relacionada (para notas crédito)
        if invoice_data['invoice_type'] == 'CREDIT_NOTE' and 'related_invoice' not in invoice_data:
            related_invoice = self._get_element_text(
                invoice_root, './/cbc:ReferenceID'
            )
            if related_invoice:
                try:
                    # Usar el ID de factura relacionada completo
                    invoice_data['related_invoice'] = related_invoice
                except Exception as e:
                    logger.warning(f"No se pudo extraer el número de factura relacionada: {str(e)}")
                    invoice_data['related_invoice'] = related_invoice
    
    @staticmethod
    def _get_element_text(root: etree._Element, path: str, default: str = '') -> str:
        """
        Obtiene el texto de un elemento XML o un valor por defecto si no existe.
        
        Args:
            root: Elemento raíz desde donde buscar.
            path: Ruta XPath del elemento.
            default: Valor por defecto si el elemento no se encuentra.
            
        Returns:
            Texto del elemento o el valor por defecto.
        """
        try:
            elem = root.find(path, XML_NAMESPACES)
            return elem.text.strip() if elem is not None and elem.text else default
        except Exception as e:
            logger.debug(f"Error al obtener texto del elemento {path}: {str(e)}")
            return default
    
    @staticmethod
    def _extract_invoice_parts(invoice_id: str) -> Tuple[str, str]:
        """
        Extrae el prefijo y número de una factura a partir de su ID.
        
        Args:
            invoice_id: ID de la factura.
            
        Returns:
            Tupla con (prefijo, número).
        """
        if not invoice_id:
            return "", ""
            
        match = INVOICE_ID_PATTERN.match(invoice_id)
        if match:
            return match.group('prefix'), match.group('number')
        return "", invoice_id
    
    @staticmethod
    def _clean_decimal(value: str, default: str = '0', force_int: bool = False) -> str:
        """
        Limpia y formatea un valor decimal.
        
        Args:
            value: Valor a limpiar.
            default: Valor por defecto si value es inválido.
            force_int: Si es True, devuelve el valor como entero si es posible.
            
        Returns:
            Cadena con el valor decimal limpio, asegurando que tenga punto decimal
            y un solo dígito después del punto, o como entero si force_int es True.
        """
        if not value:
            return default
            
        try:
            # Convertir a float
            num = float(value)
            
            # Si force_int es True y el número es entero, devolver como entero
            if force_int and num.is_integer():
                return str(int(num))
                
            # Formatear con suficientes decimales
            formatted = f"{num:.10f}"
            
            # Eliminar ceros innecesarios después del punto decimal
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
                
            # Asegurar que tenga al menos un decimal si no es entero
            if '.' not in formatted:
                formatted += '.0'
                
            return formatted
            
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _extract_toll_data(description: str) -> Dict[str, Optional[str]]:
        """
        Extrae el nombre del peaje y el número de placa de la descripción del ítem.
        
        Args:
            description: Descripción del ítem.
            
        Returns:
            Diccionario con 'toll_name' y 'plate_number'.
        """
        if not description:
            return {'toll_name': None, 'plate_number': None}
            
        # Buscar patrón de peaje y placa
        match = TOLL_DATA_PATTERN.search(description)
        if not match:
            return {'toll_name': None, 'plate_number': None}
            
        try:
            # Extraer nombre del peaje (última palabra)
            toll_name = match.group('peaje').strip()
            toll_match = TOLL_NAME_PATTERN.search(toll_name)
            if toll_match:
                toll_name = toll_match.group(1).strip()
            
            # Agregar prefijo
            toll_name = f"{Constants.PEAJE.value[0]} {toll_name}" if toll_name else None
            
            # Obtener placa si existe el grupo 'plate' o 'placa'
            plate_number = None
            if 'plate' in match.groupdict() and match.group('plate'):
                plate_number = match.group('plate').strip()
            elif 'placa' in match.groupdict() and match.group('placa'):
                plate_number = match.group('placa').strip()
            
            return {
                'toll_name': toll_name,
                'plate_number': plate_number
            }
            
        except (IndexError, AttributeError) as e:
            logger.warning(f"Error al extraer datos de peaje: {str(e)}")
            return {'toll_name': None, 'plate_number': None}
