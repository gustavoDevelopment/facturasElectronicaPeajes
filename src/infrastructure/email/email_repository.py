"""
Implementación del repositorio de correo electrónico.
"""
from src.domain.repositories.email_repository import EmailRepository
from src.domain.use_cases.email_processor import EmailProcessingError
from typing import Dict, Any, List
import imaplib
import email
from email.message import EmailMessage
import os
from pathlib import Path
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

class IMAPEmailRepository(EmailRepository):
    """Implementación del repositorio usando IMAP."""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializa el repositorio con la configuración."""
        self.config = config
        self.mail = None
    
    def connect(self) -> None:
        """Conecta al servidor IMAP."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.config["imap_server"])
            self.mail.login(self.config["user"], self.config["password"])
            logger.info("Conexión IMAP establecida exitosamente")
        except Exception as e:
            error_msg = f"Error conectando a IMAP: {str(e)}"
            logger.error(error_msg)
            raise EmailProcessingError(error_msg) from e
    
    def disconnect(self) -> None:
        """Desconecta del servidor IMAP."""
        if self.mail:
            self.mail.logout()
            logger.info("Conexión IMAP cerrada")
    
    def download_attachments(self, message_id: str, download_path: str) -> List[Dict[str, Any]]:
        """
        Descarga los adjuntos de un correo.
        
        Args:
            message_id: ID del mensaje
            download_path: Ruta donde guardar los adjuntos
            
        Returns:
            Lista de diccionarios con información de los adjuntos descargados
        """
        try:
            self.mail.select("inbox")
            _, data = self.mail.fetch(message_id, "(RFC822)")
            
            if not data[0]:
                raise EmailProcessingError("No se pudo obtener el mensaje")
                
            msg = email.message_from_bytes(data[0][1])
            attachments = []
            
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                    
                if part.get('Content-Disposition') is None:
                    continue
                    
                filename = part.get_filename()
                if filename and (filename.lower().endswith('.xml') or filename.lower().endswith('.zip')):
                    filepath = os.path.join(download_path, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                        
                    attachments.append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": os.path.getsize(filepath)
                    })
            
            return attachments
            
        except Exception as e:
            error_msg = f"Error descargando adjuntos: {str(e)}"
            logger.error(error_msg)
            raise EmailProcessingError(error_msg) from e
