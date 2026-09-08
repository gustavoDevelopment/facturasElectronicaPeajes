"""
Asistente de configuración de correo (email.json) para un tenant.

Permite elegir entre autenticación por password de aplicación (legacy) o
OAuth 2.0 (recomendado para Gmail), y guarda build/tenant/<id>/email.json.
"""
import os

from objects.fo_obj_email import ConfiguracionEmail
from objects.fo_gmail_oauth import obtener_credenciales
from logger import get_logger

logger = get_logger(__name__)


def _tenant_email_path(tenant_id: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "build", "tenant", tenant_id, "email.json")


def configurar_email_tenant(tenant_id: str) -> None:
    """Menú interactivo para (re)configurar el email de un tenant."""
    tenant_file = _tenant_email_path(tenant_id)
    configuracion = ConfiguracionEmail(tenant_file)

    if os.path.exists(tenant_file):
        configuracion.cargar_configuracion()
    else:
        configuracion.config = {}

    print("\n" + "=" * 50)
    print("  CONFIGURAR EMAIL DEL TENANT")
    print("=" * 50)
    print(" [1] Password de aplicación (legacy)")
    print(" [2] OAuth 2.0 (recomendado, Gmail)")
    opcion = input("\nSeleccione el tipo de autenticación: ").strip()

    imap_server = input("Servidor IMAP (ej. imap.gmail.com): ").strip() or "imap.gmail.com"
    user = input("Correo (usuario IMAP): ").strip()

    if opcion == "2":
        print("\nPara OAuth2 necesitas un OAuth Client ID tipo 'Desktop app'")
        print("creado en Google Cloud Console, con la Gmail API habilitada,")
        print("y el archivo client_secret.json descargado.\n")
        client_secrets = input("Ruta al archivo client_secret.json: ").strip()
        client_secrets = os.path.expanduser(client_secrets)

        if not os.path.exists(client_secrets):
            print(f"❌ No se encontró el archivo: {client_secrets}")
            return

        tenant_dir = os.path.dirname(tenant_file)
        os.makedirs(tenant_dir, exist_ok=True)
        oauth_token = os.path.join(tenant_dir, "gmail_token.json")

        print("\n🔐 Se abrirá el navegador para autorizar el acceso a Gmail...")
        try:
            obtener_credenciales(client_secrets, oauth_token)
        except Exception as e:
            logger.error(f"Error al autorizar OAuth2: {str(e)}")
            print(f"❌ No se pudo completar la autorización: {str(e)}")
            return

        configuracion.actualizar_config_email_oauth2(imap_server, user, client_secrets, oauth_token)
        print("✅ Autorización completada y token guardado.")
    else:
        password = input("Password de aplicación: ").strip()
        configuracion.actualizar_config_email(imap_server, user, password)

    configuracion.guardar_configuracion()
    print(f"\n✅ Configuración de email guardada en: {tenant_file}")
