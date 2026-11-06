# Facturae Optimus

Sistema de gestión de facturas electrónicas para peajes.

## Estructura del Proyecto

```
.
├── main/
│   ├── bussines/         # Lógica de negocio
│   ├── config.py         # Configuración
│   ├── disparadores/     # Triggers y eventos
│   ├── fo_start.py       # Punto de entrada
│   ├── logger.py         # Manejo de logs
│   ├── objects/          # Definición de objetos
│   ├── plantilla/        # Plantillas
│   ├── printer/          # Módulo de impresión
```

## Características

- Procesamiento automático de facturas XML
- Manejo de correo electrónico para recepción de facturas
- Generación de plantillas Excel para reportes
- Sistema de impresión de facturas

## Requisitos

- Python 3.8+
- pip

## Instalación

1. Clonar el repositorio:
   ```bash
git clone https://github.com/gustavoDevelopment/facturasElectronicaPeajes.git
cd facturasElectronicaPeajes
```

2. Crear y activar entorno virtual:
   ```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
   ```bash
pip install -r requirements.txt
```

## Arquitectura del núcleo

La lógica de `main/bussines/` no usa `input()` ni `print()`: recibe parámetros,
devuelve resultados (`ResultadoDescarga`, `ResultadoProceso`) y reporta eventos a
un `Reporter` (`bussines/reporter.py`). El menú de consola usa `ConsoleReporter` y
hace las preguntas al usuario; otra interfaz (por ejemplo gráfica) solo debe
heredar de `Reporter` y llamar a las mismas funciones.

Los datos de trabajo (ZIPs, vouchers, Excel de salida) se guardan en una **carpeta
de salida global**, con una subcarpeta por tenant (`<salida>/<tenant>/{zip,voucher,output,...}`).
Se define con `OUTPUT_DIR` o `settings.json` (`set_output_dir`); si no, se usa
`~/Documents/Facturae_Optimus`.

Tenants, plantillas, logs y `settings.json` viven en la carpeta de datos del usuario
(`~/Library/Application Support/FacturaeOptimus` en macOS, `%APPDATA%\FacturaeOptimus`
en Windows), configurable con `FACTURAE_HOME`. La plantilla incluida en el repositorio
se copia ahí la primera vez que se usa un tenant.

## Interfaz gráfica

```bash
python gui_main.py
```

- **Procesar:** elige tenant, mes y año (por defecto el mes anterior) y la carpeta de
  salida; muestra el progreso y el registro, y permite abrir el Excel o la carpeta.
- **Correo:** configura el correo del tenant sin editar archivos: Google (OAuth2, con
  selector del `client_secret.json` y navegador para autorizar) o contraseña de aplicación.

Requiere `customtkinter` (incluido en `requirements.txt`).

## Instaladores (macOS y Windows)

El workflow `.github/workflows/build.yml` genera la aplicación sin necesidad de
instalar Python: `FacturaeOptimus-macos.zip` (`.app`) y `FacturaeOptimus-windows.zip`
(carpeta con `FacturaeOptimus.exe`). Se ejecuta a mano (Actions > Build apps > Run
workflow) o al crear un tag `v*`, y deja los archivos como artefactos. Cada build corre
las pruebas y una autoprueba del binario (`--check`).

Para publicar una versión descargable (sección **Releases** del repositorio):
`git tag v1.0.0 && git push origin v1.0.0`. El workflow construye ambos sistemas y
adjunta `FacturaeOptimus-macos.zip` y `FacturaeOptimus-windows.zip` a esa release.

Localmente: `pip install pyinstaller && pyinstaller facturae.spec`.

Primer arranque sin firma digital:
- **macOS:** clic derecho sobre la app > Abrir (y confirmar). Si dice que está dañada:
  `xattr -cr FacturaeOptimus.app`.
- **Windows:** SmartScreen > "Más información" > "Ejecutar de todas formas".

## Uso

1. Configurar las variables de entorno:
   ```bash
cp .env.example .env
# Editar .env con las configuraciones necesarias
```

2. Ejecutar la aplicación:
   ```bash
python __main__.py
```

## Configuración del correo (secretos)

Las credenciales de correo **no viven en el repositorio**. Se guardan por tenant en:

```
~/.facturae_optimus/secrets/<tenant_id>/
├── email.json         # servidor IMAP, usuario y tipo de autenticación
└── gmail_token.json   # refresh token OAuth2 (solo si usas OAuth2)
```

La ruta base se puede cambiar con `SECRETS_DIR` en el `.env`.

### En una máquina nueva

1. Instalar dependencias: `python -m pip install -r requirements.txt` (dentro de un venv).
2. Copiar `.env.example` a `.env` (opcional: definir `SECRETS_DIR`).
3. Ejecutar la app y usar la **opción 6 del menú (configurar email del tenant)**. El asistente crea el `email.json` en la carpeta de secretos y permite elegir:
   - **Password de aplicación** (legacy).
   - **OAuth 2.0 para Gmail** (recomendado): requiere un OAuth Client ID tipo *Desktop app* creado en Google Cloud Console, con la Gmail API habilitada, y el `client_secret*.json` descargado (guárdalo fuera del repo). El asistente abre el navegador para autorizar y guarda el token.

Alternativa: copiar la carpeta `<tenant_id>/` desde otra máquina a `SECRETS_DIR`. Si usa OAuth2, hay que corregir las rutas absolutas `oauth_client_secrets` y `oauth_token` dentro del `email.json`.

Nunca commitees `email.json`, `gmail_token.json` ni `client_secret*.json`.

## Contribución

1. Fork del repositorio
2. Crear una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.
