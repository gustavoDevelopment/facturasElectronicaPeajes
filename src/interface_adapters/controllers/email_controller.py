"""
Controlador para manejar las peticiones relacionadas con correo electrónico.
"""
from src.domain.use_cases.email_processor import EmailProcessor
from src.domain.repositories.email_repository import EmailRepository
from src.infrastructure.email.email_repository import IMAPEmailRepository
from typing import Dict, Any, List
import logging
from datetime import datetime

# Configuración del logger
logger = logging.getLogger(__name__)

class EmailController:
    """Controlador para manejar las peticiones de correo electrónico."""
    
    def __init__(self, email_processor: EmailProcessor, email_repo: EmailRepository):
        """Inicializa el controlador con el procesador y repositorio."""
        self.email_processor = email_processor
        self.email_repo = email_repo
    
    def process_incoming_emails(self, config: Dict[str, Any], download_path: str) -> Dict[str, Any]:
        """
        Procesa los correos entrantes y descarga sus adjuntos.
        
        Args:
            config: Configuración del correo
            download_path: Ruta donde guardar los adjuntos
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            logger.info("Iniciando procesamiento de correos entrantes")
            
            # Conectar al servidor IMAP
            self.email_repo.connect()
            
            # Buscar correos no procesados
            _, messages = self.email_repo.search_unprocessed_emails()
            
            processed_emails = []
            
            # Procesar cada mensaje
            for msg_id in messages[0].split():
                try:
                    # Descargar adjuntos
                    attachments = self.email_repo.download_attachments(msg_id, download_path)
                    
                    # Procesar correo
                    email_data = self.email_processor.process_email({
                        "id": msg_id.decode(),
                        "attachments": attachments
                    })
                    
                    processed_emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error procesando correo {msg_id}: {str(e)}")
                    continue
            
            # Desconectar del servidor
            self.email_repo.disconnect()
            
            return {
                "success": True,
                "processed_count": len(processed_emails),
                "emails": processed_emails,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error general procesando correos: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
