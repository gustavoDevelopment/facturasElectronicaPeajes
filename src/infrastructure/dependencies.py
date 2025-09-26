"""
Sistema de inyección de dependencias para la aplicación.
"""
from src.domain.repositories.invoice_repository import InvoiceRepository
from src.infrastructure.repositories.xml_invoice_repository import XMLInvoiceRepository
from src.domain.use_cases.invoice_processor import InvoiceProcessingUseCase
from src.config.settings import STORAGE_CONFIG
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

def configure_dependencies():
    """
    Configura y devuelve las dependencias necesarias para la aplicación.
    
    Returns:
        dict: Diccionario con las dependencias configuradas
    """
    try:
        # Configurar repositorio
        invoice_repo = XMLInvoiceRepository(STORAGE_CONFIG["invoice_storage"])
        
        # Configurar caso de uso
        use_case = InvoiceProcessingUseCase(invoice_repo)
        
        logger.info("Dependencias configuradas exitosamente")
        return {
            "invoice_repository": invoice_repo,
            "invoice_use_case": use_case
        }
    except Exception as e:
        logger.error(f"Error configurando dependencias: {str(e)}")
        raise
