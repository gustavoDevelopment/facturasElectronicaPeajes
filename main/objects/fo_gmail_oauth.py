"""
Helper para autenticación OAuth 2.0 (flujo "Desktop app") contra IMAP de Gmail.

Requiere que el usuario haya creado un OAuth Client ID de tipo "Desktop app"
en Google Cloud Console (con la Gmail API habilitada) y haya descargado el
archivo client_secret.json correspondiente.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scope necesario para leer correo por IMAP.
SCOPES = ["https://mail.google.com/"]


def obtener_credenciales(client_secrets_path: str, token_path: str) -> Credentials:
    """
    Obtiene credenciales OAuth2 válidas, reutilizando el token guardado en
    `token_path` y renovándolo o solicitando autorización (abriendo el
    navegador) cuando sea necesario.
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError(
                    f"No se encontró el archivo de credenciales OAuth: {client_secrets_path}. "
                    "Descárgalo desde Google Cloud Console (OAuth Client ID tipo 'Desktop app')."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def generar_auth_string(user: str, access_token: str) -> str:
    """Construye la cadena SASL XOAUTH2 requerida por imaplib.authenticate."""
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01"
