"""
Pruebas unitarias para el módulo de procesamiento de facturas.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Importar el procesador de facturas
from main.process.invoice_processor import InvoiceProcessor, InvoiceProcessingError, InvoiceFormatError, InvoiceDataError

# Directorio de datos de prueba
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')

class TestInvoiceProcessor(unittest.TestCase):
    """Pruebas para la clase InvoiceProcessor."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas."""
        cls.processor = InvoiceProcessor()
        
        # Crear directorio de datos de prueba si no existe
        os.makedirs(TEST_DATA_DIR, exist_ok=True)
        
        # Crear archivos XML de prueba
        cls.create_test_xml_files()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas."""
        # Eliminar archivos de prueba
        for file in Path(TEST_DATA_DIR).glob('*.xml'):
            file.unlink()
    
    @classmethod
    def create_test_xml_files(cls):
        """Crear archivos XML de prueba."""
        # Factura de ejemplo
        invoice_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>FAC001-123</cbc:ID>
            <cbc:IssueDate>2025-05-13</cbc:IssueDate>
            <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
            <cac:AccountingSupplierParty>
                <cac:Party>
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>PROVEEDOR EJEMPLO S.A.S.</cbc:RegistrationName>
                        <cbc:CompanyID>9001234567</cbc:CompanyID>
                    </cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingSupplierParty>
            <cac:AccountingCustomerParty>
                <cac:Party>
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>CLIENTE EJEMPLO S.A.S.</cbc:RegistrationName>
                        <cbc:CompanyID>8009876543</cbc:CompanyID>
                    </cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingCustomerParty>
            <cac:LegalMonetaryTotal>
                <cbc:PayableAmount currencyID="COP">1250000.00</cbc:PayableAmount>
            </cac:LegalMonetaryTotal>
            <cac:InvoiceLine>
                <cbc:ID>1</cbc:ID>
                <cbc:InvoicedQuantity unitCode="UN">1</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID="COP">1000000.00</cbc:LineExtensionAmount>
                <cac:Item>
                    <cbc:Description>PASAJE PEATONAL PEATONAL ABC123 1</cbc:Description>
                    <cac:SellersItemIdentification>
                        <cbc:ID>ITEM-001</cbc:ID>
                    </cac:SellersItemIdentification>
                </cac:Item>
                <cac:Price>
                    <cbc:PriceAmount currencyID="COP">1000000.00</cbc:PriceAmount>
                </cac:Price>
            </cac:InvoiceLine>
        </Invoice>
        """
        
        # Nota crédito de ejemplo
        credit_note_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <CreditNote xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
                  xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                  xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>NC-001-789</cbc:ID>
            <cbc:IssueDate>2025-05-13</cbc:IssueDate>
            <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
            <cbc:ReferenceID>FAC001-123</cbc:ReferenceID>
            <cac:AccountingSupplierParty>
                <cac:Party>
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>PROVEEDOR EJEMPLO S.A.S.</cbc:RegistrationName>
                        <cbc:CompanyID>9001234567</cbc:CompanyID>
                    </cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingSupplierParty>
            <cac:AccountingCustomerParty>
                <cac:Party>
                    <cac:PartyLegalEntity>
                        <cbc:RegistrationName>CLIENTE EJEMPLO S.A.S.</cbc:RegistrationName>
                        <cbc:CompanyID>8009876543</cbc:CompanyID>
                    </cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingCustomerParty>
            <cac:LegalMonetaryTotal>
                <cbc:PayableAmount currencyID="COP">-250000.00</cbc:PayableAmount>
            </cac:LegalMonetaryTotal>
            <cac:CreditNoteLine>
                <cbc:ID>1</cbc:ID>
                <cbc:CreditedQuantity unitCode="UN">1</cbc:CreditedQuantity>
                <cbc:LineExtensionAmount currencyID="COP">-250000.00</cbc:LineExtensionAmount>
                <cac:Item>
                    <cbc:Description>DESCUENTO ESPECIAL</cbc:Description>
                    <cac:SellersItemIdentification>
                        <cbc:ID>DESC-001</cbc:ID>
                    </cac:SellersItemIdentification>
                </cac:Item>
                <cac:Price>
                    <cbc:PriceAmount currencyID="COP">-250000.00</cbc:PriceAmount>
                </cac:Price>
            </cac:CreditNoteLine>
        </CreditNote>
        """
        
        # Factura embebida en AttachedDocument
        attached_doc_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <AttachedDocument xmlns="urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2"
                        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>DOC-001</cbc:ID>
            <cac:Attachment>
                <cac:ExternalReference>
                    <cbc:Description><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ID>FAC-EMB-001</cbc:ID>
    <cbc:IssueDate>2025-05-13</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>PROVEEDOR EMBEBIDO S.A.S.</cbc:RegistrationName>
                <cbc:CompanyID>9112223334</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount currencyID="COP">500000.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>]]></cbc:Description>
            </cac:ExternalReference>
        </cac:Attachment>
    </AttachedDocument>
"""
        
        # Escribir archivos de prueba
        with open(os.path.join(TEST_DATA_DIR, 'factura_ejemplo.xml'), 'w', encoding='utf-8') as f:
            f.write(invoice_xml)
            
        with open(os.path.join(TEST_DATA_DIR, 'nota_credito_ejemplo.xml'), 'w', encoding='utf-8') as f:
            f.write(credit_note_xml)
            
        with open(os.path.join(TEST_DATA_DIR, 'documento_con_factura_embebida.xml'), 'w', encoding='utf-8') as f:
            f.write(attached_doc_xml)
    
    def test_process_invoice_valid(self):
        """Probar el procesamiento de una factura válida."""
        xml_file = os.path.join(TEST_DATA_DIR, 'factura_ejemplo.xml')
        factura_id, datos = self.processor.process_invoice(xml_file)
        
        self.assertEqual(factura_id, "FAC001-123")
        self.assertEqual(datos['invoice_type'], 'INVOICE')
        self.assertEqual(datos['invoice_prefix'], 'FAC001')
        self.assertEqual(datos['invoice_number'], '123')
        self.assertEqual(datos['formatted_issue_date'], '13/05/2025')
        self.assertEqual(datos['currency'], 'COP')
        self.assertEqual(datos['total_amount'], '1250000.0')
        self.assertEqual(datos['supplier_name'], 'PROVEEDOR EJEMPLO S.A.S.')
        self.assertEqual(datos['supplier_tax_id'], '9001234567')
        self.assertEqual(datos['customer_name'], 'CLIENTE EJEMPLO S.A.S.')
        self.assertEqual(datos['customer_tax_id'], '8009876543')
        self.assertEqual(datos['toll_name'], 'PEAJE PEATONAL')
        self.assertEqual(datos['plate_number'], 'ABC123')
        self.assertEqual(len(datos['items']), 1)
        
        # Verificar ítem
        item = datos['items'][0]
        self.assertEqual(item['description'], 'PASAJE PEATONAL PEATONAL ABC123 1')
        self.assertEqual(item['quantity'], '1')
        self.assertEqual(item['price'], '1000000.0')
        self.assertEqual(item['reference'], 'ITEM-001')
    
    def test_process_credit_note(self):
        """Probar el procesamiento de una nota crédito."""
        xml_file = os.path.join(TEST_DATA_DIR, 'nota_credito_ejemplo.xml')
        factura_id, datos = self.processor.process_invoice(xml_file)
        
        self.assertEqual(factura_id, "NC-001-789")
        self.assertEqual(datos['invoice_type'], 'CREDIT_NOTE')
        self.assertEqual(datos['related_invoice'], 'FAC001-123')
        self.assertEqual(datos['total_amount'], '-250000.0')
    
    def test_extract_embedded_invoice(self):
        """Probar la extracción de una factura embebida."""
        xml_file = os.path.join(TEST_DATA_DIR, 'documento_con_factura_embebida.xml')
        factura_id, datos = self.processor.process_invoice(xml_file)
        
        self.assertEqual(factura_id, "FAC-EMB-001")
        self.assertEqual(datos['supplier_name'], 'PROVEEDOR EMBEBIDO S.A.S.')
        self.assertEqual(datos['supplier_tax_id'], '9112223334')
        self.assertEqual(datos['total_amount'], '500000.0')
    
    def test_invalid_xml_file(self):
        """Probar con un archivo XML inválido."""
        xml_file = os.path.join(TEST_DATA_DIR, 'archivo_invalido.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write("<root><invalid>xml</root>")
        
        with self.assertRaises(InvoiceFormatError):
            self.processor.process_invoice(xml_file)
    
    def test_nonexistent_file(self):
        """Probar con un archivo que no existe."""
        with self.assertRaises(InvoiceProcessingError):
            self.processor.process_invoice("ruta/inexistente.xml")
    
    def test_extract_toll_data(self):
        """Probar la extracción de datos de peaje."""
        from main.process.invoice_processor import InvoiceProcessor
        
        processor = InvoiceProcessor()
        
        # Caso estándar
        descripcion = "PASAJE PEATONAL PEATONAL ABC123 1"
        expected = {'toll_name': 'PEAJE PEATONAL', 'plate_number': 'ABC123'}
        result = processor._extract_toll_data(descripcion)
        self.assertEqual(result, expected)
        
        # Caso sin datos de peaje
        self.assertEqual(
            processor._extract_toll_data("DESCUENTO ESPECIAL"),
            {'toll_name': None, 'plate_number': None}
        )
        
        # Caso con formato inusual
        descripcion = "PASAJE PEATONAL PEATONAL X1Y2Z3 1"
        expected = {'toll_name': 'PEAJE PEATONAL', 'plate_number': 'X1Y2Z3'}
        result = processor._extract_toll_data(descripcion)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
