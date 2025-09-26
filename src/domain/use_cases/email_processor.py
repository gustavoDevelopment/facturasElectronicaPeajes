"""
Casos de uso para el procesamiento de correos electrónicos.
"""
from typing import Dict, Any
import logging
from datetime import datetime

# Configuración del logger
logger = logging.getLogger(__name__)

class EmailProcessingError(Exception):
    """Excepción base para errores en el procesamiento de correos."""
    pass

class EmailProcessor:
    """Procesador de correos electrónicos."""
    
    def __init__(self, email_config: Dict[str, Any]):
        """Inicializa el procesador de correos."""
        self.email_config = email_config
        
    def process_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un correo electrónico y extrae sus adjuntos.
        
        Args:
            message: Diccionario con los datos del correo
            
        Returns:
            Dict con los resultados del procesamiento
            
        Raises:
            EmailProcessingError: Si hay errores en el procesamiento
        """
        try:
            # Extraer datos básicos del correo
            email_data = self._extract_email_data(message)
            
            # Procesar adjuntos
            attachments = self._process_attachments(message)
            
            # Crear registro de procesamiento
            processing_data = {
                "email_id": email_data["id"],
                "subject": email_data["subject"],
                "sender": email_data["sender"],
                "date": email_data["date"],
                "attachments": attachments,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Correo procesado: {email_data['id']}")
            return processing_data
            
        except Exception as e:
            error_msg = f"Error procesando correo: {str(e)}"
            logger.error(error_msg)
            raise EmailProcessingError(error_msg) from e
    
    def _extract_email_data(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae los datos básicos del correo."""
        return {
            "id": message.get("id"),
            "subject": message.get("subject"),
            "sender": message.get("sender"),
            "date": message.get("date")
        }
    
    def _process_attachments(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa los adjuntos del correo."""
        attachments = []
        for attachment in message.get("attachments", []):
            try:
                # Validar tipo de archivo
                if not attachment["filename"].lower().endswith(('.xml', '.zip')):
                    continue
                    
                # Procesar archivo
                processed_file = {
                    "filename": attachment["filename"],
                    "content_type": attachment["content_type"],
                    "size": attachment["size"],
                    "processed": True
                }
                attachments.append(processed_file)
                
            except Exception as e:
                logger.warning(f"Error procesando adjunto: {str(e)}")
                continue
        
        return attachments
