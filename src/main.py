"""
Archivo principal de la aplicación Facturae Optimus.
"""
import logging
from src.config.settings import EMAIL_CONFIG, STORAGE_CONFIG
from src.infrastructure.dependencies import configure_dependencies
from src.infrastructure.email.email_repository import IMAPEmailRepository
from src.domain.use_cases.email_processor import EmailProcessor
from src.interface_adapters.controllers.email_controller import EmailController
from src.interface_adapters.controllers.invoice_controller import InvoiceController

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Punto de entrada principal de la aplicación."""
    try:
        logger.info("Iniciando Facturae Optimus")
        
        # Configurar dependencias
        dependencies = configure_dependencies()
        
        # Configurar repositorio de correo
        email_repo = IMAPEmailRepository(EMAIL_CONFIG)
        
        # Crear procesador de correo
        email_processor = EmailProcessor(EMAIL_CONFIG)
        
        # Crear controladores
        email_controller = EmailController(email_processor, email_repo)
        invoice_controller = InvoiceController(dependencies["invoice_use_case"])
        
        # Procesar correos y facturas
        process_emails(email_controller, STORAGE_CONFIG["invoice_storage"])
        
    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {str(e)}")
        raise

def process_emails(controller: EmailController, download_path: str):
    """
    Procesa los correos entrantes y sus adjuntos.
    
    Args:
        controller: Controlador de correo
        download_path: Ruta donde guardar los adjuntos
    """
    try:
        result = controller.process_incoming_emails(EMAIL_CONFIG, download_path)
        if result["success"]:
            logger.info(f"Procesados {result['processed_count']} correos")
            
            # Procesar facturas encontradas
            for email_data in result["emails"]:
                for attachment in email_data["attachments"]:
                    if attachment["filename"].lower().endswith('.xml'):
                        with open(attachment["filepath"], 'r') as f:
                            xml_content = f.read()
                            invoice_result = invoice_controller.handle_invoice_upload(xml_content)
                            if invoice_result["success"]:
                                logger.info(f"Factura procesada: {invoice_result['invoice_id']}")
                            else:
                                logger.error(f"Error procesando factura: {invoice_result['error']}")
        else:
            logger.error(f"Error procesando correos: {result['error']}")
            
    except Exception as e:
        logger.error(f"Error procesando correos: {str(e)}")
        raise

if __name__ == "__main__":
    main()
