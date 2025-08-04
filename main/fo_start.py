
"""
Punto de entrada principal para la aplicación Facturae Optimus.

Este módulo inicializa la configuración, configura el logging y lanza la aplicación.
"""
import sys
from pathlib import Path

# Asegurarse de que el directorio del proyecto esté en el PATH
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importaciones locales después de configurar el PATH
from main.config import DEBUG, get_config, get_version
from main.logger import get_logger
from main.printer.fo_menu import main_menu

# Configurar logger
logger = get_logger(__name__)

def main() -> None:
    """
    Función principal que inicia la aplicación.
    
    Configura el entorno, muestra información de inicio y ejecuta el menú principal.
    """
    try:
        # Mostrar información de inicio
        config = get_config()
        logger.info("=" * 50)
        logger.info(f"Iniciando {get_version()}")
        logger.info("-" * 50)
        
        if DEBUG:
            logger.debug("Modo depuración activado")
            logger.debug(f"Configuración: {config}")
        
        # Iniciar menú principal
        main_menu()
        
    except KeyboardInterrupt:
        logger.info("\nAplicación detenida por el usuario.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Error inesperado: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Aplicación finalizada")
        logger.info("=" * 50)

if __name__ == "__main__":
    main()
