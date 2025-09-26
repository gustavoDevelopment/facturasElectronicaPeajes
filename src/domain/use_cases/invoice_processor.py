"""
Casos de uso para el procesamiento de facturas.
"""
from src.domain.entities.invoice import Invoice
from src.domain.repositories.invoice_repository import InvoiceRepository
from src.domain.exceptions import InvoiceProcessingError
from typing import Dict, Any
import logging
from datetime import datetime
import re
import xml.etree.ElementTree as etree

# Configuración del logger
logger = logging.getLogger(__name__)

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
    
    def __init__(self, repository: InvoiceRepository):
        """Inicializa el procesador de facturas."""
        self.repository = repository
    
    def process_invoice(self, xml_content: str) -> Invoice:
        """
        Procesa una factura XML y la guarda.
        
        Args:
            xml_content: Contenido XML de la factura
            
        Returns:
            Invoice: Entidad de la factura procesada
            
        Raises:
            InvoiceProcessingError: Si hay errores en el procesamiento
        """
        try:
            # 1. Validar el XML
            tree = self._parse_xml(xml_content)
            root = tree.getroot()
            
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
            
            # 7. Crear y guardar la entidad
            invoice = Invoice(
                id=invoice_data['invoice_id'],
                prefix=invoice_data['invoice_prefix'],
                number=invoice_data['invoice_number'],
                issue_date=invoice_data['issue_date'],
                currency=invoice_data['currency'],
                total_amount=invoice_data['total_amount'],
                items=invoice_data['items'],
                toll_name=invoice_data.get('toll_name'),
                plate_number=invoice_data.get('plate_number'),
                related_invoice=invoice_data.get('related_invoice')
            )
            
            self.repository.save_invoice(invoice)
            
            logger.info(f"Factura {invoice.id} procesada exitosamente")
            return invoice
            
        except Exception as e:
            error_msg = f"Error al procesar la factura: {str(e)}"
            logger.error(error_msg)
            if isinstance(e, InvoiceProcessingError):
                raise
            raise InvoiceProcessingError(error_msg) from e
    
    def _parse_xml(self, xml_content: str) -> etree._ElementTree:
        """Parsea el contenido XML."""
        try:
            return etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise InvoiceFormatError(f"Error de sintaxis XML: {str(e)}") from e
    
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
                namespaces={'cac': 'urn:un:unece:uncefact:documentation:2', 'cbc': 'urn:un:unece:uncefact:documentation:2'}
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
            related_invoice = self._get_element_text(
                invoice_root, './/cbc:ReferenceID'
            )
            
        # Extraer moneda
        currency = self._get_element_text(invoice_root, 'cbc:DocumentCurrencyCode')
        if not currency:
            raise InvoiceDataError("La factura no tiene código de moneda")
        
        # Extraer monto total
        total_amount = self._get_element_text(invoice_root, './/cbc:PayableAmount')
        if not total_amount:
            raise InvoiceDataError("La factura no tiene monto total")
            
        return {
            'invoice_id': invoice_id,
            'invoice_prefix': prefix,
            'invoice_number': number,
            'issue_date': issue_date_dt,
            'formatted_issue_date': formatted_date,
            'currency': currency,
            'total_amount': float(total_amount),
            'items': [],
            'toll_name': None,
            'plate_number': None,
            'related_invoice': related_invoice if is_credit_note else None
        }
    
    def _get_element_text(self, root: etree._Element, path: str) -> str:
        """Extrae el texto de un elemento."""
        elem = root.find(path, namespaces={'cac': 'urn:un:unece:uncefact:documentation:2', 'cbc': 'urn:un:unece:uncefact:documentation:2'})
        return elem.text if elem is not None else None
    
    def _extract_invoice_parts(self, invoice_id: str) -> (str, str):
        """Extrae el prefijo y número de la factura."""
        match = INVOICE_ID_PATTERN.match(invoice_id)
        if match:
            return match.group('prefix'), match.group('number')
        raise InvoiceDataError("La factura no tiene un ID válido")
    
    def _extract_parties_data(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]):
        """Extrae datos del proveedor y cliente."""
        # Extraer datos del proveedor
        supplier_party = invoice_root.find('.//cac:AccountingSupplierParty', namespaces={'cac': 'urn:un:unece:uncefact:documentation:2'})
        if supplier_party is not None:
            # Extraer nombre del proveedor
            supplier_name = self._get_element_text(supplier_party, 'cac:PartyName/cbc:Name')
            if supplier_name:
                invoice_data['supplier_name'] = supplier_name
                
            # Extraer dirección del proveedor
            supplier_address = supplier_party.find('cac:PostalAddress', namespaces={'cac': 'urn:un:unece:uncefact:documentation:2'})
            if supplier_address is not None:
                street = self._get_element_text(supplier_address, 'cbc:StreetName')
                city = self._get_element_text(supplier_address, 'cbc:CityName')
                postal_code = self._get_element_text(supplier_address, 'cbc:PostalZone')
                if street and city and postal_code:
                    invoice_data['supplier_address'] = f"{street}, {city} {postal_code}"
        
        # Extraer datos del cliente
        customer_party = invoice_root.find('.//cac:AccountingCustomerParty', namespaces={'cac': 'urn:un:unece:uncefact:documentation:2'})
        if customer_party is not None:
            # Extraer nombre del cliente
            customer_name = self._get_element_text(customer_party, 'cac:PartyName/cbc:Name')
            if customer_name:
                invoice_data['customer_name'] = customer_name
                
            # Extraer dirección del cliente
            customer_address = customer_party.find('cac:PostalAddress', namespaces={'cac': 'urn:un:unece:uncefact:documentation:2'})
            if customer_address is not None:
                street = self._get_element_text(customer_address, 'cbc:StreetName')
                city = self._get_element_text(customer_address, 'cbc:CityName')
                postal_code = self._get_element_text(customer_address, 'cbc:PostalZone')
                if street and city and postal_code:
                    invoice_data['customer_address'] = f"{street}, {city} {postal_code}"
    
    def _process_invoice_items(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]):
        """Procesa los ítems de la factura."""
        # Extraer ítems de la factura
        invoice_items = invoice_root.findall('.//cac:InvoiceLine', namespaces={'cac': 'urn:un:unece:uncefact:documentation:2'})
        for item in invoice_items:
            # Extraer descripción del ítem
            description = self._get_element_text(item, 'cbc:Description')
            if description:
                invoice_data['items'].append({
                    'description': description,
                    'quantity': float(self._get_element_text(item, 'cbc:InvoicedQuantity')),
                    'unit_price': float(self._get_element_text(item, 'cbc:LineExtensionAmount')),
                    'total_price': float(self._get_element_text(item, 'cbc:LineExtensionAmount'))
                })
    
    def _process_additional_data(self, invoice_root: etree._Element, invoice_data: Dict[str, Any]):
        """Procesa datos adicionales de la factura."""
        # Extraer datos de peaje
        toll_data = self._get_element_text(invoice_root, './/cbc:Note')
        if toll_data:
            match = TOLL_DATA_PATTERN.match(toll_data)
            if match:
                invoice_data['toll_name'] = match.group('peaje')
                invoice_data['plate_number'] = match.group('placa')
                
        # Extraer datos de la factura relacionada
        related_invoice = self._get_element_text(invoice_root, './/cbc:ReferenceID')
        if related_invoice:
            invoice_data['related_invoice'] = related_invoice

class InvoiceProcessingUseCase:
    """Casos de uso para el procesamiento de facturas."""
    
    def __init__(self, repository: InvoiceRepository):
        """Inicializa el caso de uso con el repositorio."""
        self.repository = repository
        self.processor = InvoiceProcessor(repository)
    
    def process_invoice(self, xml_content: str) -> Invoice:
        """
        Procesa una factura XML y la guarda.
        
        Args:
            xml_content: Contenido XML de la factura
            
        Returns:
            Invoice: Entidad de la factura procesada
            
        Raises:
            InvoiceProcessingError: Si hay errores en el procesamiento
        """
        return self.processor.process_invoice(xml_content)
