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

## Estructura del Proyecto

### Dominio (domain/)
- Entidades del negocio (`entities/`)
- Casos de uso (`use_cases/`)
- Interfaces de repositorios (`repositories/`)

### Aplicación (application/)
- Servicios de aplicación (`services/`)
- Transfer Objects (`dtos/`)

### Adaptadores de Interfaz (interface_adapters/)
- Controladores (`controllers/`)
- Presentadores (`presenters/`)

### Infraestructura (infrastructure/)
- Implementaciones concretas de repositorios
- Implementaciones de correo
- Implementaciones de impresión

## Uso

1. Configurar las variables de entorno:
   ```bash
cp .env.example .env
# Editar .env con las configuraciones necesarias
```

2. Ejecutar la aplicación:
   ```bash
python src/main.py
```

## Contribución

1. Fork del repositorio
2. Crear una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.
