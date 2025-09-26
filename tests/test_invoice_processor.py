"""
Pruebas unitarias para el procesador de facturas.
"""
import unittest
from unittest.mock import MagicMock, patch
from src.domain.entities.invoice import Invoice
from src.domain.use_cases.invoice_processor import InvoiceProcessor
from src.domain.exceptions import InvoiceProcessingError
from datetime import datetime

class TestInvoiceProcessor(unittest.TestCase):
    """Pruebas para el procesador de facturas."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.repository = MagicMock()
        self.processor = InvoiceProcessor(self.repository)
    
    def test_process_invoice_success(self):
        """Test para procesar factura exitosamente."""
        # Datos de prueba
        xml_content = """
        <Invoice>
            <cbc:ID>PP-001</cbc:ID>
            <cbc:IssueDate>2023-08-04</cbc:IssueDate>
            <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
            <cbc:PayableAmount>100000.00</cbc:PayableAmount>
        </Invoice>
        """
        
        # Ejecutar
        result = self.processor.process_invoice(xml_content)
        
        # Verificar
        self.assertIsInstance(result, Invoice)
        self.assertEqual(result.id, "PP-001")
        self.assertEqual(result.currency, "COP")
        self.assertEqual(result.total_amount, 100000.00)
        self.repository.save_invoice.assert_called_once()
    
    def test_process_invoice_invalid_xml(self):
        """Test para procesar XML inválido."""
        # Datos de prueba
        xml_content = "<InvalidXML>"  # XML inválido
        
        # Ejecutar y verificar
        with self.assertRaises(InvoiceProcessingError):
            self.processor.process_invoice(xml_content)
    
    def test_process_invoice_missing_required_fields(self):
        """Test para procesar factura con campos requeridos faltantes."""
        # Datos de prueba
        xml_content = """
        <Invoice>
            <cbc:ID>PP-001</cbc:ID>
            <!-- Falta IssueDate -->
        </Invoice>
        """
        
        # Ejecutar y verificar
        with self.assertRaises(InvoiceProcessingError):
            self.processor.process_invoice(xml_content)

if __name__ == '__main__':
    unittest.main()
