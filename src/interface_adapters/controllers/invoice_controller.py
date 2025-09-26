"""
Controlador para manejar las peticiones relacionadas con facturas.
"""
from src.domain.use_cases.invoice_processor import InvoiceProcessingUseCase
from src.domain.entities.invoice import Invoice
from typing import Dict, Any
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

class InvoiceController:
    """Controlador para manejar las peticiones de facturas."""
    
    def __init__(self, use_case: InvoiceProcessingUseCase):
        """Inicializa el controlador con el caso de uso."""
        self.use_case = use_case
    
    def handle_invoice_upload(self, xml_content: str) -> Dict[str, Any]:
        """
        Maneja la subida de una factura XML.
        
        Args:
            xml_content: Contenido XML de la factura
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            logger.info("Iniciando procesamiento de factura")
            invoice = self.use_case.process_invoice(xml_content)
            logger.info(f"Factura procesada exitosamente: {invoice.id}")
            return {
                "success": True,
                "invoice_id": invoice.id,
                "message": "Factura procesada exitosamente",
                "data": {
                    "invoice_id": invoice.id,
                    "prefix": invoice.prefix,
                    "number": invoice.number,
                    "issue_date": invoice.issue_date.strftime('%Y-%m-%d'),
                    "currency": invoice.currency,
                    "total_amount": invoice.total_amount,
                    "items_count": len(invoice.items)
                }
            }
        except Exception as e:
            logger.error(f"Error procesando factura: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
