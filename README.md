# Causa Peajes

Aplicación de escritorio (macOS y Windows) que automatiza la gestión de **facturas electrónicas de peajes**: descarga desde el correo los ZIP con las facturas del mes, extrae los datos de los XML y genera el Excel listo para causar.

[![Build apps](https://github.com/gustavoDevelopment/facturasElectronicaPeajes/actions/workflows/build.yml/badge.svg)](https://github.com/gustavoDevelopment/facturasElectronicaPeajes/actions/workflows/build.yml)

## Contenido

- [Qué hace](#qué-hace)
- [Instalación para usuarios](#instalación-para-usuarios)
- [Primer uso en un equipo nuevo](#primer-uso-en-un-equipo-nuevo-sin-nada-configurado)
- [Uso de la interfaz gráfica](#uso-de-la-interfaz-gráfica)
- [Configuración](#configuración)
- [Generar los instaladores (macOS y Windows)](#generar-los-instaladores-macos-y-windows)
- [Desarrollo](#desarrollo)
- [Arquitectura](#arquitectura)
- [Solución de problemas](#solución-de-problemas)
- [Seguridad](#seguridad)
- [Contribuir](#contribuir)

## Qué hace

1. **Descarga** los correos del mes (remitente `notificaciones@int.lafactura.co`) por IMAP y guarda los ZIP adjuntos, sin repetir los que ya existen.
2. **Descomprime** los ZIP y lee los XML (facturas y notas crédito UBL).
3. **Genera** un voucher de texto por factura y un **Excel** con las columnas de la plantilla del tenant.
4. Soporta **varios tenants** (empresas), cada uno con su correo, su plantilla y su carpeta de trabajo.

El correo puede autenticarse con **Google (OAuth2, recomendado)** o con **contraseña de aplicación**.

## Instalación para usuarios

No hace falta tener Python. Descarga la última versión desde la sección **[Releases](https://github.com/gustavoDevelopment/facturasElectronicaPeajes/releases)**:

| Sistema | Archivo | Cómo abrirlo |
|---|---|---|
| macOS | `CausaPeajes-macos.zip` | Descomprimir, mover `Causa Peajes.app` a *Aplicaciones* y abrir |
| Windows | `CausaPeajes-windows.zip` | Descomprimir **toda** la carpeta y ejecutar `CausaPeajes.exe` |

La aplicación **no está firmada digitalmente**, por lo que el sistema avisa la primera vez:

- **macOS:** clic derecho sobre la app → **Abrir** → **Abrir**. Si dice que está dañada:
  ```bash
  xattr -cr "/Applications/Causa Peajes.app"
  ```
- **Windows:** en SmartScreen pulsar **Más información** → **Ejecutar de todas formas**. No muevas el `.exe` fuera de su carpeta: necesita los archivos que lo acompañan.

Las credenciales de correo **no viajan con la aplicación**: hay que configurarlas en cada equipo (ver [Uso](#uso-de-la-interfaz-gráfica)).

## Primer uso en un equipo nuevo (sin nada configurado)

En un equipo limpio no existe el `email.json` ni el token de Google: **la propia aplicación los crea** desde la pestaña **Correo**. No hay que copiar ni editar archivos a mano.

1. Instala y abre la aplicación (ver [Instalación para usuarios](#instalación-para-usuarios)).
2. Elige cómo autenticar el correo:
   - **Contraseña de aplicación** (lo más rápido, no caduca): en la cuenta de Google activa la verificación en dos pasos, crea una *contraseña de aplicación* y úsala en la pestaña **Correo**. Salta al paso 4.
   - **Google (OAuth2)**: sigue el paso 3 una sola vez para obtener el archivo `client_secret.json`.
3. **Crear el `client_secret.json` en Google Cloud Console** (solo con OAuth2):
   1. Entra a <https://console.cloud.google.com/> y crea un proyecto (por ejemplo `facturae-optimus`).
   2. **APIs y servicios → Biblioteca**: busca **Gmail API** y pulsa **Habilitar**.
   3. **APIs y servicios → Pantalla de consentimiento de OAuth**: tipo **Externo**, completa nombre y correo de contacto y, en *Usuarios de prueba*, agrega la cuenta de Gmail que recibe las facturas.
   4. **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**, tipo de aplicación **Aplicación de escritorio**.
   5. Descarga el JSON (**Descargar JSON**) y guárdalo **fuera del repositorio** (por ejemplo en `Documentos`).

   > Mientras la pantalla de consentimiento esté en estado **Prueba**, Google caduca el token a los **7 días** y habrá que volver a vincular. Para que no caduque, pulsa **Publicar aplicación** en esa pantalla (para uso propio basta con aceptar el aviso de "app no verificada") o usa la contraseña de aplicación.
4. En la pestaña **Correo** de la app:
   1. **Tenant:** el nombre de la empresa, por ejemplo `turboCarga` (es el mismo nombre que luego eliges en *Procesar*).
   2. **Servidor IMAP:** `imap.gmail.com`. **Correo:** la cuenta que recibe las facturas.
   3. Marca **Google (OAuth2)**, elige el `client_secret.json` con *Elegir…* y pulsa **Guardar / Vincular**; se abre el navegador, inicia sesión y acepta los permisos. Con contraseña de aplicación, escríbela y pulsa **Guardar / Vincular**.
5. Al ver `✅ Guardado en …` ya existen, creados por la app, el `email.json` y (con OAuth2) el `gmail_token.json` en la carpeta de credenciales (ver [Configuración](#configuración)). El tenant aparece en la lista de la pestaña **Procesar**.
6. En **Procesar** elige tenant, mes, año y la **carpeta de salida**, y pulsa **Descargar y procesar**.

Esto se hace **una sola vez por tenant y por equipo**; las siguientes veces solo se usa la pestaña **Procesar**.

## Uso de la interfaz gráfica

### 1. Administrar empresas

Pestaña **Empresas** (equivale al menú de tenants de la terminal): lista las empresas con su
estado de correo y de plantilla, y permite **Agregar**, **Editar**, **Eliminar** y
**Configurar correo**.

- Al **agregar** una empresa se elige su plantilla de Excel: copiar la de otra empresa, importar un
  `plantilla.json` o dejarla para más tarde (sin plantilla no se puede procesar).
- El nombre identifica a la empresa (carpetas, credenciales y plantilla), por eso no se puede cambiar.
- Al **eliminar** se quita de la lista y se borra su plantilla; los ZIP, vouchers y Excel ya generados
  no se tocan, y las credenciales solo se borran si lo confirmas.
- El selector de empresa de **Procesar** muestra estas empresas.

### 2. Configurar el correo (una sola vez por tenant)

Pestaña **Correo**:

1. Escribe el **nombre del tenant** (por ejemplo `turboCarga`), el servidor IMAP (`imap.gmail.com`) y el correo.
2. Elige el tipo de autenticación:
   - **Google (OAuth2):** selecciona el archivo `client_secret.json` y pulsa **Guardar / Vincular**; se abre el navegador para autorizar el acceso.
   - **Contraseña de aplicación:** escribe la contraseña y pulsa **Guardar / Vincular**.

> Para OAuth2 se necesita un *OAuth Client ID* de tipo **Desktop app**, creado en Google Cloud Console con la **Gmail API** habilitada. Descarga su `client_secret.json` y guárdalo **fuera del repositorio**.

### 3. Procesar un mes

Pestaña **Procesar**:

1. Elige el **tenant** y el rango **Desde / Hasta** (mes y año; por defecto, el mes anterior). Para varios meses, pon un rango (por ejemplo ene–mar 2026): cada mes se procesa por separado y se pueden correr **a la vez** (*Procesos simultáneos*, de 1 a 4; máximo 24 meses por ejecución).
2. Elige la **carpeta de salida** con *Elegir…* (una sola para todos los tenants).
3. Pulsa **Descargar y procesar**. Verás la barra de progreso, el **panel de resumen** (una fila por mes con estado, correos, ZIP, facturas y botón para abrir su Excel) y el registro de descarga en vivo.
4. Un mes que falle no detiene a los demás. Al terminar usa **Abrir** en cada fila, **Abrir último Excel** o **Abrir carpeta de salida**.

Si ya hay ZIP descargados del mes, la casilla *Verificar y descargar faltantes* decide si se vuelve a consultar el correo.

### Dónde queda cada cosa

```
<carpeta de salida>/
└── <tenant>/
    ├── zip/<mes>_<año>/        ZIP descargados pendientes
    ├── openZip/<mes>_<año>/    XML descomprimidos
    ├── closedZip/<mes>_<año>/  ZIP ya procesados
    ├── voucher/<mes>_<año>/    un .txt por factura
    └── output/                 documento_<mes>_<año>.xlsx
```

## Configuración

Los datos de la aplicación viven fuera del código, en la carpeta del usuario:

| Qué | macOS | Windows |
|---|---|---|
| Tenants, plantillas, logs, `settings.json` | `~/Library/Application Support/FacturaeOptimus` | `%APPDATA%\FacturaeOptimus` |
| Credenciales de correo (por tenant) | `~/.facturae_optimus/secrets/<tenant>/` | `%USERPROFILE%\.facturae_optimus\secrets\<tenant>\` |
| Carpeta de salida por defecto | `~/Documents/Causa Peajes` | `%USERPROFILE%\Documents\Causa Peajes` |

La carpeta de datos conserva el nombre interno `FacturaeOptimus` (nombre anterior de la aplicación) para no perder la configuración existente. La plantilla de ejemplo incluida se copia a la carpeta de datos la primera vez que se usa un tenant.

Variables de entorno opcionales (también en un archivo `.env`, ver `.env.example`):

| Variable | Efecto |
|---|---|
| `FACTURAE_HOME` | Cambia la carpeta de datos de la aplicación |
| `OUTPUT_DIR` | Fuerza la carpeta de salida (prevalece sobre `settings.json`) |
| `SECRETS_DIR` | Cambia la carpeta de credenciales |
| `TENANTS_DIR`, `LOG_DIR` | Cambian la ubicación de tenants y logs |
| `LOG_LEVEL`, `DEBUG` | Nivel de logs y modo depuración |

## Generar los instaladores (macOS y Windows)

Los instaladores se construyen con **PyInstaller** a partir de `causa_peajes.spec`. **PyInstaller no compila de un sistema a otro**: el `.app` se construye en un Mac y el `.exe` en un Windows. Por eso la vía recomendada es el workflow de GitHub Actions, que construye ambos.

Los binarios **no se guardan en git**; se publican como *artifacts* del workflow o en **Releases**.

### Opción A — Publicar una versión con GitHub Actions (recomendada)

Genera los dos instaladores y los deja descargables en **Releases**.

1. Deja `master` actualizada y con las pruebas en verde:
   ```bash
   git switch master && git pull
   python -m pytest tests -q
   ```
2. Crea y sube un tag que empiece con `v`:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. En GitHub abre **Actions → Build apps** y espera a que terminen los trabajos `macos-latest`, `windows-latest` y `release` (unos minutos).
4. Descarga `CausaPeajes-macos.zip` y `CausaPeajes-windows.zip` desde **Releases → v1.0.0**.

Cada trabajo instala dependencias, corre las pruebas, construye, ejecuta una **autoprueba del binario** (`--check`) y empaqueta. Si algo falla no se crea la release: revisa el log del paso en rojo.

Para rehacer un número de versión, borra primero la release y el tag (`git push origin --delete v1.0.0`) y vuelve a crearlo.

Si el repositorio restringe los permisos, activa *Read and write permissions* en **Settings → Actions → General → Workflow permissions**.

### Opción B — Solo probar el build, sin publicar

**Actions → Build apps → Run workflow** (rama `master`). Los zips quedan como **Artifacts** al final de la ejecución, sin crear release.

### Opción C — Construir en tu propio equipo

Requisitos: Python 3.9 o superior con Tk (incluido en los instaladores oficiales de python.org y en `python-tk` de Homebrew).

#### macOS → `Causa Peajes.app`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt pyinstaller

python -m pytest tests -q
python -m PyInstaller causa_peajes.spec --noconfirm

"dist/Causa Peajes.app/Contents/MacOS/CausaPeajes" --check   # debe imprimir OK
ditto -c -k --keepParent "dist/Causa Peajes.app" CausaPeajes-macos.zip
```

Usa `ditto` para el zip: el `zip` normal puede dañar los permisos del `.app`.

#### Windows → `CausaPeajes.exe`

En PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt pyinstaller

python -m pytest tests -q
python -m PyInstaller causa_peajes.spec --noconfirm

.\dist\CausaPeajes\CausaPeajes.exe --check   # debe imprimir OK
Compress-Archive -Path dist\CausaPeajes -DestinationPath CausaPeajes-windows.zip
```

Si PowerShell bloquea la activación del entorno, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

El resultado en Windows es una **carpeta** (`dist\CausaPeajes\`) que debe distribuirse completa.

### Qué incluye el build

`causa_peajes.spec` empaqueta la interfaz (`gui_main.py`), los recursos de `customtkinter`, el `tenants.json` y las plantillas `plantilla.json` de ejemplo. La opción `--check` abre y cierra la ventana y comprueba que esos recursos están presentes.

## Desarrollo

### Ejecutar desde el código

```bash
git clone https://github.com/gustavoDevelopment/facturasElectronicaPeajes.git
cd facturasElectronicaPeajes

python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

python gui_main.py                   # interfaz gráfica
python __main__.py                   # menú de consola
```

Para probar sin tocar tus datos reales: `FACTURAE_HOME=/tmp/prueba python gui_main.py`.

### Pruebas

```bash
python -m pytest tests -q
```

Cubren la extracción de datos de los XML, la descarga por IMAP (simulada), la generación del Excel, los ajustes portables y los servicios de la interfaz.

### Dependencias

- `requirements.txt`: lo necesario para ejecutar (lxml, openpyxl, python-dotenv, google-auth, google-auth-oauthlib, customtkinter).
- `requirements-dev.txt`: añade pytest, black, pylint y sphinx.

## Arquitectura

```
.
├── gui_main.py              Punto de entrada de la interfaz gráfica
├── __main__.py              Punto de entrada del menú de consola
├── causa_peajes.spec        Configuración de PyInstaller
├── assets/                  Logo e íconos (.svg, .png, .icns, .ico)
├── main/
│   ├── interfaz/            Ventana (CustomTkinter) y servicios sin dependencia de UI
│   ├── bussines/            Núcleo: descarga, extracción, Excel, rutas y Reporter
│   ├── printer/             Menú de consola y administración de tenants
│   ├── objects/             Configuración de correo, OAuth2 y plantillas
│   ├── plantilla/           Cabeceras y constantes del Excel
│   ├── settings.py          Carpetas de datos y carpeta de salida
│   └── config.py            Variables de entorno y configuración
├── tests/                   Pruebas automáticas
└── .github/workflows/       Build de instaladores y publicación de releases
```

El núcleo (`main/bussines/`) **no usa `input()` ni `print()`**: recibe parámetros, devuelve resultados (`ResultadoDescarga`, `ResultadoProceso`) y reporta eventos a un `Reporter`. La consola usa `ConsoleReporter` y la ventana usa un reporter propio; así ambas interfaces comparten la misma lógica.

## Solución de problemas

| Síntoma | Causa y solución |
|---|---|
| `ModuleNotFoundError: No module named 'dotenv'` (u otro módulo) | Se ejecuta con un Python distinto al del entorno virtual. Activa `.venv` o ejecuta `.venv/bin/python …` |
| `No module named '_tkinter'` | Falta Tk. macOS: `brew install python-tk@3.12` (según tu versión). Windows: reinstala Python marcando *tcl/tk* |
| macOS: «la app está dañada» | Ejecuta `xattr -cr "/Applications/Causa Peajes.app"` |
| Windows: SmartScreen bloquea el `.exe` | *Más información* → *Ejecutar de todas formas* |
| «El tenant … no tiene el correo configurado» | Configúralo en la pestaña **Correo** |
| Gmail rechaza el acceso | Con OAuth2, vuelve a pulsar **Guardar / Vincular**; con contraseña, usa una **contraseña de aplicación**, no la de la cuenta |
| El workflow no crea la release | Revisa los permisos de Actions (*Read and write*) y el log del paso que falló |

## Seguridad

- Las credenciales (`email.json`, `gmail_token.json`, `client_secret*.json`) **nunca** deben commitearse: viven fuera del repositorio y están en `.gitignore`.
- La aplicación no imprime contraseñas ni tokens en consola ni en logs.
- Las facturas pueden contener datos de terceros: no subas XML ni PDF reales al repositorio.

## Contribuir

1. Crea una rama desde `master`: `feature/<descripción>`, `fix/<descripción>` o `hotfix/<descripción>`.
2. Mantén los cambios pequeños (idealmente menos de 400 líneas) y con pruebas.
3. Título de commit y PR en el formato `tipo: descripción corta` (máximo 72 caracteres). Tipos válidos: `feat`, `fix`, `hotfix`, `docs`, `test`, `refactor`.
4. Verifica `python -m pytest tests -q` antes de abrir el Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT.
