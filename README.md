# Sistema Web de Votaciones — Festival de la Leyenda Vallenata 2027

## 1. Descripción del proyecto

El Sistema Web de Votaciones del Festival de la Leyenda Vallenata 2027 es un proyecto académico desarrollado como una aplicación web responsive. Su propósito es permitir la gestión de categorías, votaciones y opciones de participación, así como el registro de votos de los usuarios.

El sistema se desarrolla con Django y utiliza una base de datos MySQL para la persistencia de la información. La arquitectura sigue el patrón MVT (Modelo, Vista y Plantilla) de Django.

## 2. Objetivo

Desarrollar una plataforma web que permita organizar procesos de votación de manera estructurada, controlando la participación de los usuarios y la consulta de resultados según las condiciones establecidas para cada votación.

## 3. Tecnologías utilizadas

- **Python:** lenguaje de programación del backend.
- **Django 5.2.18:** framework para el desarrollo web.
- **MySQL:** sistema gestor de bases de datos configurado para el proyecto.
- **mysqlclient 2.3.0:** conector entre Django y MySQL.
- **python-dotenv 1.2.4:** lectura de variables de entorno.
- **HTML y plantillas de Django:** estructura y presentación de las páginas web.
- **Git:** control de versiones del código fuente.

## 4. Funcionalidades implementadas

- Registro de usuarios.
- Inicio y cierre de sesión.
- Consulta de categorías activas.
- Consulta de votaciones habilitadas.
- Registro de votos para usuarios autenticados.
- Validación para impedir que un usuario vote más de una vez en una misma votación.
- Validación de las opciones disponibles para cada votación.
- Control del periodo de inicio y finalización de las votaciones.
- Consulta de resultados una vez finalizado el periodo correspondiente.
- Administración de ediciones, categorías, votaciones, opciones y votos desde Django Admin.
- Acciones administrativas para abrir y cerrar votaciones.
- Pruebas automatizadas del comportamiento principal del sistema.

Las funcionalidades de presentación y los demás requisitos del proyecto deben verificarse a medida que avance su desarrollo.

## 5. Estructura del proyecto

```text
festival_vallenato/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── templates/
├── votaciones/
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── .env
├── .gitignore
├── manage.py
└── requirements.txt
```

- `config/`: configuración general del proyecto Django.
- `templates/`: plantillas HTML de la aplicación.
- `votaciones/`: modelos, formularios, vistas, rutas, administración y pruebas.
- `migrations/`: historial de cambios en los modelos de datos.
- `manage.py`: herramienta para ejecutar comandos administrativos de Django.
- `requirements.txt`: dependencias del proyecto.
- `.env`: variables de configuración y conexión; no debe publicarse en el repositorio.

## 6. Requisitos previos

Antes de ejecutar el proyecto se necesita:

- Python compatible con Django 5.2.
- MySQL Server.
- Git, si se va a clonar el repositorio.
- Un entorno virtual de Python.

## 7. Instalación y ejecución

### 7.1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd festival_vallenato
```

Reemplaza `URL_DEL_REPOSITORIO` por la dirección real del repositorio.

### 7.2. Crear y activar el entorno virtual

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 7.3. Instalar las dependencias

```powershell
python -m pip install -r requirements.txt
```

### 7.4. Configurar las variables de entorno

Crear el archivo `.env` en la carpeta principal y definir las variables que requiere `config/settings.py` para conectarse a MySQL.

No compartir ni publicar contraseñas o credenciales.

### 7.5. Aplicar las migraciones

```powershell
python manage.py migrate
```

### 7.6. Crear un usuario administrador

```powershell
python manage.py createsuperuser
```

Seguir las instrucciones que aparecen en la terminal.

### 7.7. Ejecutar el servidor de desarrollo

```powershell
python manage.py runserver
```

Abrir en el navegador:

http://127.0.0.1:8000/

El panel de administración de Django se encuentra normalmente en:

http://127.0.0.1:8000/admin/

## 8. Pruebas y validación

Las pruebas automatizadas se ejecutan mediante:

```powershell
python manage.py test votaciones
```

En la revisión realizada el 23 de octubre de 2026, las diez pruebas de la aplicación finalizaron correctamente. También se verificó que Django no reportara errores en las comprobaciones generales del proyecto.

Estos resultados corresponden al estado del código en esa fecha y pueden cambiar con futuras modificaciones.

## 9. Base de datos y seguridad

La configuración de la aplicación utiliza MySQL y variables de entorno para las credenciales de conexión.

El sistema incorpora validaciones para restringir la participación a usuarios autenticados, impedir votos duplicados y comprobar que la opción seleccionada corresponda a la votación.

Las credenciales deben mantenerse fuera del control de versiones. Las pruebas automatizadas utilizan una base de datos de pruebas separada, según la configuración de Django.

## 10. Estado del proyecto

El proyecto se encuentra en desarrollo académico. El backend y las reglas principales de votación cuentan con pruebas automatizadas. La interfaz responsive, los requisitos pendientes y la integración de los aportes del equipo deben verificarse y completarse según el alcance acordado.

## 11. Equipo de trabajo

Proyecto académico desarrollado en equipo por cuatro integrantes.

La distribución detallada de responsabilidades se documentará por separado cuando se confirme el reparto definitivo.

## 12. Licencia

Proyecto académico. No se ha especificado una licencia de distribución.
