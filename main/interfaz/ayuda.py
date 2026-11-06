"""Texto de la pestaña Ayuda y enlaces útiles (sin dependencia de la ventana)."""

URL_CONSOLA = "https://console.cloud.google.com/"
URL_GMAIL_API = "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
URL_CREDENCIALES = "https://console.cloud.google.com/apis/credentials"
URL_CLAVES_APP = "https://myaccount.google.com/apppasswords"

ENLACES = [
    ("Google Cloud Console", URL_CONSOLA),
    ("Habilitar Gmail API", URL_GMAIL_API),
    ("Credenciales OAuth", URL_CREDENCIALES),
    ("Contraseñas de aplicación", URL_CLAVES_APP),
]

AYUDA = """\
PRIMER USO EN UN EQUIPO NUEVO

En un equipo sin configurar no existe el correo del tenant. La aplicación lo crea \
desde la pestaña "Correo"; no hay que copiar ni editar archivos.

1) ELEGIR CÓMO AUTENTICAR EL CORREO
• Contraseña de aplicación (lo más rápido, no caduca): en la cuenta de Google activa \
la verificación en dos pasos y crea una contraseña de aplicación (botón "Contraseñas \
de aplicación"). Luego pasa al paso 3.
• Google (OAuth2): sigue el paso 2 una sola vez para obtener el archivo client_secret.json.

2) CREAR EL client_secret.json (solo OAuth2)
  a. Abre Google Cloud Console y crea un proyecto (por ejemplo "facturae-optimus").
  b. Habilita la Gmail API (botón "Habilitar Gmail API").
  c. Pantalla de consentimiento de OAuth: tipo Externo; completa nombre y correo de \
contacto y agrega como usuario de prueba la cuenta de Gmail que recibe las facturas.
  d. Credenciales → Crear credenciales → ID de cliente de OAuth → tipo "Aplicación de \
escritorio".
  e. Descarga el JSON y guárdalo fuera del repositorio (por ejemplo en Documentos).

Importante: mientras la pantalla de consentimiento esté en estado "Prueba", Google \
caduca el token a los 7 días y habrá que volver a vincular. Para evitarlo, pulsa \
"Publicar aplicación" en esa pantalla o usa la contraseña de aplicación.

3) AGREGAR LA EMPRESA (pestaña "Empresas") Y CONFIGURAR SU CORREO
  • En "Empresas" pulsa "Agregar", escribe el nombre y elige la plantilla de Excel \
(copiar de otra empresa o importar un archivo). Luego selecciónala y pulsa "Configurar \
correo", que abre la pestaña "Correo" con la empresa ya escrita.
  • Si en "Correo" escribes un nombre nuevo, la empresa también se agrega sola.
  • Tenant: nombre de la empresa (por ejemplo turboCarga). Es el mismo que luego eliges \
en "Procesar".
  • Servidor IMAP: imap.gmail.com. Correo: la cuenta que recibe las facturas.
  • Google (OAuth2): elige el client_secret.json con "Elegir…" y pulsa "Guardar / \
Vincular"; se abre el navegador, inicia sesión y acepta los permisos.
  • Contraseña de aplicación: escríbela y pulsa "Guardar / Vincular".
  Al ver "Guardado en …" el correo queda listo; el tenant aparece en "Procesar".

4) PROCESAR UN MES (pestaña "Procesar")
  • Elige el tenant y el mes y año (por defecto, el mes anterior).
  • Elige la carpeta de salida con "Elegir…" (una sola para todos los tenants; cada \
tenant usa una subcarpeta con su nombre).
  • Pulsa "Lanzar proceso". Puedes lanzar otro mes (u otra empresa) mientras el anterior \
sigue corriendo; hasta 4 a la vez.
  • El panel "Procesos" muestra una fila por proceso con su estado, el porcentaje de avance \
(sobre 100%), los correos, los ZIP y las facturas.
  • "Log" muestra el registro de ese proceso; cada proceso tiene el suyo.
  • "Detener" lo para en el siguiente punto seguro. No se pierde nada: los ZIP solo se \
mueven a "closedZip" cuando el Excel ya está generado, así que al relanzar ese mes se \
procesa completo.
  • "Excel" abre el archivo generado. Un proceso con error o detenido no afecta a los demás.

Esto se configura una sola vez por tenant y por equipo.

PROBLEMAS FRECUENTES
• "El tenant … no tiene el correo configurado": configúralo en la pestaña "Correo".
• Gmail rechaza el acceso: con OAuth2 vuelve a pulsar "Guardar / Vincular"; con \
contraseña usa una contraseña de aplicación, no la de la cuenta.
• Dejó de funcionar a los 7 días: el token de prueba caducó; vincula de nuevo o publica \
la aplicación en Google Cloud.
"""
