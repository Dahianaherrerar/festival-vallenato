# Sistema de votaciones del Festival de la Leyenda Vallenata

Proyecto Django con una API REST existente y administración para ediciones, categorías, votaciones, opciones y votos.

## Requisitos

- Python 3.12 o superior
- MySQL 8.0.11 o superior

El proyecto usa Django 5.2 para mantener compatibilidad con MySQL 8.0; Django 6 requiere MySQL 8.4 o superior.

## Instalación local

En PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Crea la base de datos en MySQL Workbench:

```sql
CREATE DATABASE festival_votaciones CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Completa los valores locales de MySQL en `.env`. No compartas ni subas ese archivo.

## Migraciones

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La migración `0003_edicion_y_ajustes_de_modelos` agrega el modelo Edición y asigna las categorías existentes a la edición 2027. Antes de modificar el esquema, comprueba si los registros antiguos contienen duplicados que violarían las restricciones nuevas; si encuentra alguno, se detiene sin aplicar cambios para que puedan corregirse primero. La API previa se conserva en esta propuesta.

## Rutas

- `/admin/`: administración de los cinco modelos.
- `/api/`: API REST existente.
- `/api-auth/`: autenticación de sesiones para la API navegable.

Las páginas HTML de registro y votaciones públicas no forman parte de esta integración; quedan pendientes para las partes correspondientes.
