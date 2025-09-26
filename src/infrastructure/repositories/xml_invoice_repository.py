"""
Implementación concreta del repositorio de facturas usando XML.
"""
from src.domain.repositories.invoice_repository import InvoiceRepository
from src.domain.entities.invoice import Invoice
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional

class XMLInvoiceRepository(InvoiceRepository):
    """Implementación del repositorio usando archivos XML."""
    
    def __init__(self, storage_path: str):
        """Inicializa el repositorio con la ruta de almacenamiento."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_invoice(self, invoice: Invoice) -> None:
        """
        Guarda una factura en formato XML.
        
        Args:
            invoice: Entidad de la factura a guardar
        """
        # Crear el XML raíz
        root = ET.Element('Invoice')
        
        # Agregar elementos básicos
        ET.SubElement(root, 'ID').text = invoice.id
        ET.SubElement(root, 'Prefix').text = invoice.prefix
        ET.SubElement(root, 'Number').text = invoice.number
        ET.SubElement(root, 'IssueDate').text = invoice.issue_date.strftime('%Y-%m-%d')
        ET.SubElement(root, 'Currency').text = invoice.currency
        ET.SubElement(root, 'TotalAmount').text = str(invoice.total_amount)
        
        # Agregar items
        items = ET.SubElement(root, 'Items')
        for item in invoice.items:
            item_elem = ET.SubElement(items, 'Item')
            ET.SubElement(item_elem, 'Description').text = item.get('description')
            ET.SubElement(item_elem, 'Quantity').text = str(item.get('quantity', 0))
            ET.SubElement(item_elem, 'UnitPrice').text = str(item.get('unit_price', 0))
            ET.SubElement(item_elem, 'TotalPrice').text = str(item.get('total_price', 0))
        
        # Agregar datos adicionales
        if invoice.toll_name:
            ET.SubElement(root, 'TollName').text = invoice.toll_name
        if invoice.plate_number:
            ET.SubElement(root, 'PlateNumber').text = invoice.plate_number
        if invoice.related_invoice:
            ET.SubElement(root, 'RelatedInvoice').text = invoice.related_invoice
        
        # Crear el archivo XML
        tree = ET.ElementTree(root)
        xml_path = self.storage_path / f"{invoice.id}.xml"
        tree.write(str(xml_path), encoding='utf-8', xml_declaration=True)
    
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """
        Obtiene una factura por su ID.
        
        Args:
            invoice_id: ID de la factura a recuperar
            
        Returns:
            Invoice: Entidad de la factura si existe, None si no
        """
        xml_path = self.storage_path / f"{invoice_id}.xml"
        if not xml_path.exists():
            return None
            
        try:
            tree = ET.parse(str(xml_path))
            root = tree.getroot()
            
            # Extraer datos básicos
            invoice = Invoice(
                id=root.find('ID').text,
                prefix=root.find('Prefix').text,
                number=root.find('Number').text,
                issue_date=datetime.strptime(root.find('IssueDate').text, '%Y-%m-%d'),
                currency=root.find('Currency').text,
                total_amount=float(root.find('TotalAmount').text),
                items=[],
                toll_name=root.find('TollName').text if root.find('TollName') is not None else None,
                plate_number=root.find('PlateNumber').text if root.find('PlateNumber') is not None else None,
                related_invoice=root.find('RelatedInvoice').text if root.find('RelatedInvoice') is not None else None
            )
            
            # Extraer items
            items_elem = root.find('Items')
            if items_elem is not None:
                for item_elem in items_elem.findall('Item'):
                    invoice.items.append({
                        'description': item_elem.find('Description').text,
                        'quantity': float(item_elem.find('Quantity').text),
                        'unit_price': float(item_elem.find('UnitPrice').text),
                        'total_price': float(item_elem.find('TotalPrice').text)
                    })
            
            return invoice
            
        except Exception as e:
            print(f"Error al leer la factura: {str(e)}")
            return None
