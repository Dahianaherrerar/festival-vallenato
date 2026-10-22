# Reparto del trabajo – Entrega 2

Este documento registra el estado de la propuesta de integración sobre el repositorio base del equipo. Los cambios de las partes 1 y 2 están en la rama `integracion-partes-1-2` para revisión; no se integran a la rama principal hasta que el equipo apruebe el pull request.

| Parte | Alcance | Estado de esta propuesta |
|---|---|---|
| 1. Coordinación, MySQL y modelos | Configuración de MySQL, Edición, relaciones y migraciones | Implementada. La nueva migración asigna a 2027 las categorías existentes del esquema anterior. |
| 2. Administración | Administración de los cinco modelos, relaciones inline y acciones de abrir/cerrar votaciones | Implementada; falta la prueba visual en `/admin/` y tomar las capturas. |
| 3. Autenticación | Registro e inicio/cierre de sesión mediante páginas HTML | Pendiente. |
| 4. Interfaz pública | Páginas HTML para ediciones, categorías y votaciones | Pendiente. |

La API REST existente se conserva en esta propuesta. Cualquier decisión de retirarla debe acordarse con la autora y el equipo antes de cambiarla.

## Verificaciones realizadas en la propuesta

- `python manage.py check`.
- Conexión y migraciones verificadas en las bases locales disponibles.
- La migración de integración debe probarse sobre una copia de la base del equipo antes de aplicarse a cualquier base compartida.

Cada integrante debe usar sus propias credenciales de MySQL en `.env`. No se deben compartir ni subir `.env`, volcados SQL, contraseñas o bases de datos locales.
