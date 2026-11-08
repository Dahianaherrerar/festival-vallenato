# Sistema Web de Votaciones — Festival de la Leyenda Vallenata

Aplicación web para organizar las votaciones del público del Festival de la Leyenda Vallenata. Está hecha con **Python, Django y MySQL** y sigue el patrón **MVT** (Modelo, Vista y Plantilla) de Django.

> Proyecto académico — Desarrollo Web (grupo 61), Fundación Universitaria del Área Andina.

## Contenido

1. [¿Qué hace el sistema?](#1-qué-hace-el-sistema)
2. [Tecnologías](#2-tecnologías)
3. [Programas que necesitas instalar](#3-programas-que-necesitas-instalar)
4. [Instalación paso a paso](#4-instalación-paso-a-paso)
5. [Primeros pasos dentro de la aplicación](#5-primeros-pasos-dentro-de-la-aplicación)
6. [Correo para recuperar la contraseña (Gmail)](#6-correo-para-recuperar-la-contraseña-gmail)
7. [Pruebas automáticas](#7-pruebas-automáticas)
8. [Ver los datos en MySQL (Workbench)](#8-ver-los-datos-en-mysql-workbench)
9. [Si ya tenías el proyecto: cómo actualizarlo](#9-si-ya-tenías-el-proyecto-cómo-actualizarlo)
10. [Problemas frecuentes y cómo resolverlos](#10-problemas-frecuentes-y-cómo-resolverlos)
11. [Páginas de la aplicación](#11-páginas-de-la-aplicación)
12. [Estructura del proyecto](#12-estructura-del-proyecto)
13. [Seguridad](#13-seguridad)
14. [Equipo](#14-equipo)

---

## 1. ¿Qué hace el sistema?

La información se organiza así:

```text
Edición (2027)
└── Concurso (Piquería)
    └── Categoría (Piquería Infantil)
        └── Votación (Votación del público, con fecha de inicio y de fin)
            └── Participantes (Opción A, Opción B, Opción C)
```

**Para el público:**

- Registrarse, iniciar sesión y cerrar sesión.
- Recuperar la contraseña con «¿Olvidaste tu contraseña?»: llega un correo con un enlace para crear una nueva.
- Ver los concursos y sus categorías.
- Votar por un participante, con una pantalla de confirmación antes de guardar el voto.
- **Un solo voto por categoría.** Ejemplo: quien votó en Piquería Infantil puede votar en Piquería Mayor, pero no otra vez en Piquería Infantil.
- Ver los resultados cuando termina la votación.

**Para los administradores**, tres secciones en el menú:

| Sección | Qué permite |
|---|---|
| **Administración** | Crear, editar, activar o desactivar y eliminar ediciones, concursos, categorías, votaciones y participantes. Lo que ya tiene votos no se puede eliminar, solo desactivar. |
| **Usuarios** | Ver los usuarios registrados con su correo. Enviarles un enlace para restablecer la contraseña. Activar o desactivar cuentas. |
| **Informes** | Tablero de resultados por concurso, categoría y participante, con porcentajes y ganador. Descarga de un informe **CSV** (abre en Excel) con el detalle de cada voto, para auditoría. |

También está el panel de Django Admin en `/admin/`.

---

## 2. Tecnologías

| Componente | Versión |
|---|---|
| Python | 3.13 |
| Django | 5.2.18 |
| MySQL Community Server | 8.4 LTS |
| mysqlclient (conector entre Django y MySQL) | 2.3.0 |
| python-dotenv (lee el archivo `.env`) | 1.2.4 |
| Bootstrap e íconos (se cargan por internet) | 5.3.3 |

---

## 3. Programas que necesitas instalar

Solo se hace una vez por computador. Si ya tienes alguno, verifica la versión con el comando indicado y salta al siguiente.

> Todos los comandos de este README se escriben en **PowerShell** o en la **terminal de VS Code** (menú *Terminal → Nueva terminal*).

### 3.1. Git

1. Descárgalo de https://git-scm.com/downloads/win e instálalo con las opciones por defecto.
2. Cierra y vuelve a abrir la terminal, y verifica:

```powershell
git --version
```

### 3.2. Python 3.13

1. Descárgalo de https://www.python.org/downloads/windows/ (elige una versión **3.13.x**).
2. En la primera pantalla del instalador **marca la casilla «Add python.exe to PATH»** y luego pulsa *Install Now*.
3. Cierra y vuelve a abrir la terminal, y verifica:

```powershell
py --version
```

Debe decir `Python 3.13.x`. Si escribes `python` y se abre la Microsoft Store, usa `py` en su lugar (más detalles en la [sección 10](#10-problemas-frecuentes-y-cómo-resolverlos)).

### 3.3. MySQL 8.4 y MySQL Workbench

1. Descarga **MySQL Community Server 8.4 LTS** de https://dev.mysql.com/downloads/mysql/ (Windows, instalador MSI).
2. Durante la instalación:
   - Deja el puerto **3306**.
   - Escribe una contraseña para el usuario **root** y **guárdala solo para ti**: no va en el repositorio ni en ningún documento.
   - Deja marcada la opción para que MySQL se ejecute como **servicio de Windows** al iniciar el computador.
3. Opcional, pero recomendado: instala **MySQL Workbench** desde https://dev.mysql.com/downloads/workbench/ para ver las tablas con una interfaz gráfica.

### 3.4. Visual Studio Code (opcional)

Editor recomendado: https://code.visualstudio.com/

---

## 4. Instalación paso a paso

Sigue los pasos **en orden**. Al terminar tendrás la aplicación funcionando en `http://127.0.0.1:8000/`.

### Paso 1. Descargar el proyecto (clonar)

Elige una carpeta **fuera de OneDrive** (por ejemplo `C:\dev`). OneDrive bloquea archivos del entorno virtual y de Git.

```powershell
mkdir C:\dev
cd C:\dev
git clone https://github.com/Dahianaherrerar/festival-vallenato.git
cd festival-vallenato
```

Desde aquí, **todos los comandos se ejecutan dentro de la carpeta `festival-vallenato`**. Si abres VS Code, usa *Archivo → Abrir carpeta* y elige esa carpeta.

### Paso 2. Crear y activar el entorno virtual

El entorno virtual (`.venv`) es una carpeta donde se instalan las librerías **solo para este proyecto**.

```powershell
py -3.13 -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

Sabrás que quedó activo porque la línea de la terminal empieza con **`(.venv)`**.

> **Cada vez** que abras una terminal nueva para trabajar en el proyecto, vuelve a activar el entorno con `.\.venv\Scripts\Activate.ps1`.

Si PowerShell muestra un error rojo que menciona *«la ejecución de scripts está deshabilitada»*, ejecuta esto una sola vez, responde `S` y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Paso 3. Instalar las librerías

Con el entorno activo `(.venv)`:

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.txt
```

Para comprobar que Django quedó instalado:

```powershell
python -m django --version
```

Debe decir `5.2.18`.

### Paso 4. Crear la base de datos en MySQL

La aplicación necesita una base de datos y un usuario propio de MySQL; no se usa `root` en la aplicación.

1. Abre **MySQL Workbench**, conéctate a *Local instance* con tu usuario `root` y abre una pestaña de consultas (ícono **SQL+**).
   *(También puedes usar el programa «MySQL 8.4 Command Line Client» del menú Inicio.)*
2. Copia el siguiente código. **Cambia `EscribeAquiTuClave` por una contraseña inventada por ti** (es solo para tu computador).
3. Ejecútalo con el ícono del **rayo** ⚡.

```sql
CREATE DATABASE festival_vallenato CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'festival_app'@'localhost' IDENTIFIED BY 'EscribeAquiTuClave';

GRANT ALL PRIVILEGES ON festival_vallenato.* TO 'festival_app'@'localhost';
GRANT ALL PRIVILEGES ON test_festival_vallenato.* TO 'festival_app'@'localhost';

FLUSH PRIVILEGES;
```

- La primera línea crea la base de datos con soporte para tildes, ñ y emojis.
- `festival_app` es el usuario que usará Django.
- El permiso sobre `test_festival_vallenato` es para las **pruebas automáticas**: Django crea esa base temporal al ejecutarlas y la borra al terminar.

### Paso 5. Crear el archivo `.env`

El archivo `.env` guarda las claves **solo en tu computador**. Git lo ignora, así que **nunca se sube a GitHub**.

1. Copia la plantilla:

```powershell
Copy-Item .env.example .env
```

2. Genera una clave secreta para Django:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

3. Abre el archivo `.env` en VS Code y complétalo así:

```text
DJANGO_SECRET_KEY=pega-aqui-la-clave-que-generaste
DB_NAME=festival_vallenato
DB_USER=festival_app
DB_PASSWORD=EscribeAquiTuClave
DB_HOST=127.0.0.1
DB_PORT=3306
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

| Variable | Qué poner |
|---|---|
| `DJANGO_SECRET_KEY` | La clave que generaste en el punto 2. |
| `DB_NAME` | `festival_vallenato` (la base del paso 4). |
| `DB_USER` | `festival_app` (el usuario del paso 4). |
| `DB_PASSWORD` | La contraseña que escribiste en el paso 4 en lugar de `EscribeAquiTuClave`. |
| `DB_HOST` y `DB_PORT` | Déjalos como están. |
| `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` | Puedes dejarlos vacíos por ahora. Ver la [sección 6](#6-correo-para-recuperar-la-contraseña-gmail). |

Reglas del archivo `.env`: sin espacios alrededor del `=`, sin comillas, una variable por línea.

### Paso 6. Crear las tablas (migraciones)

```powershell
python manage.py migrate
```

Django crea todas las tablas en MySQL. Debe terminar con varias líneas `Applying ... OK`. Si quieres, compruébalo en Workbench: en el esquema `festival_vallenato` aparecen tablas como `votaciones_edicion` y `votaciones_voto` (si no las ves, pulsa el botón de actualizar).

### Paso 7. Crear tu usuario administrador

```powershell
python manage.py createsuperuser
```

Te pedirá nombre de usuario, correo y contraseña dos veces. **Mientras escribes la contraseña no se ve nada en pantalla; es normal**. Si es muy corta o muy común, Django te avisa y puedes escribir otra.

Este usuario puede entrar a **Administración**, **Usuarios**, **Informes** y a `/admin/`.

### Paso 8. Encender el servidor

```powershell
python manage.py runserver
```

Abre en el navegador: **http://127.0.0.1:8000/**

- Para apagar el servidor: `Ctrl + C` en la terminal.
- Mientras el servidor esté encendido, esa terminal queda ocupada. Para otros comandos abre una terminal nueva y activa otra vez el entorno.

**¡Listo!** La próxima vez solo necesitas:

```powershell
cd C:\dev\festival-vallenato
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

---

## 5. Primeros pasos dentro de la aplicación

La base de datos empieza **vacía**. Para ver el sistema funcionando, crea un ejemplo:

1. Entra a http://127.0.0.1:8000/login/ con el administrador del paso 7.
2. En el menú, pulsa **Administración** y crea, en este orden (cada elemento pide elegir el anterior):
   1. **Edición:** año `2027`, marcada como **activa**.
   2. **Concurso:** por ejemplo `Piquería`, de la edición 2027.
   3. **Categoría:** por ejemplo `Piquería Infantil`, del concurso Piquería.
   4. **Votación:** de la categoría Piquería Infantil, con una **fecha de inicio anterior a hoy** y una **fecha de fin posterior a hoy**, y marcada como **abierta**.
   5. **Participantes:** por ejemplo `Opción A`, `Opción B` y `Opción C`, de esa votación.
3. Para votar como público, abre una **ventana de incógnito** (`Ctrl + Shift + N`), entra a http://127.0.0.1:8000/registro/ y crea un usuario normal.
4. Con ese usuario ve a **Concursos → Piquería Infantil**, elige un participante y confirma el voto.
5. Vuelve a la ventana del administrador y abre **Informes**: el voto ya aparece en el tablero y en el CSV.

**Cuándo aparece una votación para el público.** Deben cumplirse las cinco condiciones:

- La edición está activa.
- El concurso está activo.
- La categoría está activa.
- La votación está abierta.
- La fecha actual está entre la fecha de inicio y la de fin.

Los resultados públicos se ven cuando pasa la fecha de fin. Los administradores los ven en todo momento en **Informes**.

> Los nombres de concursos, categorías y participantes de los ejemplos son **datos de prueba**, no información oficial del Festival.

---

## 6. Correo para recuperar la contraseña (Gmail)

Dos funciones envían correos:

- **«¿Olvidaste tu contraseña?»**, en la página de inicio de sesión.
- **«Enviar enlace»**, en la sección **Usuarios**.

El correo trae un enlace que sirve **una sola vez** y **vence en 1 hora**.

**Opción A: sin configurar nada.** Si en el `.env` dejas vacías `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`, el correo **no se envía**: aparece completo en la terminal donde corre `runserver`. Copia el enlace desde ahí y ábrelo en el navegador. Sirve para probar.

**Opción B: con Gmail (correos reales).** Completa estas dos líneas en tu `.env`:

```text
EMAIL_HOST_USER=tucorreo@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

- `EMAIL_HOST_PASSWORD` **no es la contraseña normal de Gmail**. Es una **contraseña de aplicación** de 16 letras, sin espacios, que se crea en https://myaccount.google.com/apppasswords. Para que aparezca esa opción, la cuenta debe tener activa la **verificación en 2 pasos**.
- El equipo usa una **cuenta de Gmail creada solo para pruebas**. Sus datos se comparten por un canal privado: **nunca se escriben en el README, en `.env.example` ni en ningún archivo del repositorio**.
- Después de cambiar el `.env`, apaga y vuelve a encender el servidor.

Para comprobar que Gmail funciona (envía un correo de prueba a la dirección que escribas):

```powershell
python manage.py sendtestemail tucorreo@gmail.com
```

---

## 7. Pruebas automáticas

Con el entorno activo:

```powershell
python manage.py test
```

Ejecuta todas las pruebas (más de 100) de las apps `votaciones` y `panel`. Tarda unos minutos y debe terminar con **`OK`**.

- Django crea una base temporal `test_festival_vallenato` y la borra al final; **tus datos no se tocan**.
- Si te pregunta *«Type 'yes' if you would like to try deleting the test database»*, es porque una ejecución anterior se interrumpió: escribe `yes`. Para evitar la pregunta, usa `python manage.py test --noinput`.

| Archivo | Qué prueba |
|---|---|
| `votaciones/tests/test_vistas.py` | Quién puede votar, cuándo se ven los resultados, validaciones de fechas y opciones, abrir y cerrar votaciones. |
| `votaciones/tests/test_votar.py` | Flujo de votación y confirmación del voto. |
| `votaciones/tests/test_unicidad.py` | Un solo voto por usuario y categoría. |
| `votaciones/tests/test_concurrencia.py` | Dos votos al mismo tiempo no generan duplicados (requiere MySQL). |
| `votaciones/tests/test_concurso.py` | Modelo Concurso y agrupación por concurso. |
| `votaciones/tests/test_recuperar_clave.py` | Recuperación de contraseña por correo. |
| `votaciones/tests/test_base_datos.py` | Que los datos queden guardados en **MySQL**: consulta las tablas directamente con SQL después de registrarse, votar y crear datos en Administración. También comprueba que MySQL rechaza un voto repetido y no deja borrar un participante con votos. |
| `panel/tests/test_administracion.py` | Sección Administración. |
| `panel/tests/test_usuarios.py` | Sección Usuarios. |
| `panel/tests/test_informes.py` | Sección Informes y descarga CSV. |

Para ejecutar solo un archivo, por ejemplo: `python manage.py test panel.tests.test_informes`.

Para ver solo las pruebas de la base de datos, con el nombre de cada una:

```powershell
python manage.py test votaciones.tests.test_base_datos -v 2
```

---

## 8. Ver los datos en MySQL (Workbench)

Todo lo que se hace en la aplicación (registrarse, votar, crear concursos) queda guardado en las tablas de MySQL. Con estas consultas puedes comprobarlo en **MySQL Workbench**:

1. Abre Workbench, conéctate a *Local instance* y abre una pestaña de consultas (ícono **SQL+**).
2. Copia una consulta, haz clic dentro de ella y ejecútala con el **rayo con cursor** ⚡ (ejecuta solo la consulta donde está el cursor) o con `Ctrl + Enter`.
3. El resultado aparece abajo, en la pestaña *Result Grid*.

**Primero, elige la base de datos.** Usa el nombre que tienes en `DB_NAME` de tu `.env`; si seguiste este README, es `festival_vallenato`:

```sql
USE festival_vallenato;
```

**Tablas que creó Django.** Las de la aplicación empiezan con `votaciones_`; los usuarios están en `auth_user`.

```sql
SHOW TABLES;
```

**Usuarios registrados.** La contraseña se ve como un texto cifrado (empieza por `pbkdf2_sha256$`), nunca como la escribió el usuario. Si empieza por `!`, el usuario no tiene una contraseña con la que pueda iniciar sesión.

```sql
SELECT id, username, email,
       LEFT(password, 25) AS contrasena_cifrada,
       is_staff AS administrador,
       date_joined AS fecha_registro
FROM auth_user
ORDER BY id;
```

**Edición → Concurso → Categoría → Votación → Participante.** Muestra cómo quedan unidos en la base de datos los datos creados en Administración.

```sql
SELECT e.anio AS edicion, co.nombre AS concurso, ca.nombre AS categoria,
       v.titulo AS votacion, o.nombre AS participante, o.activo
FROM votaciones_opcion o
JOIN votaciones_votacion v   ON v.id = o.votacion_id
JOIN votaciones_categoria ca ON ca.id = v.categoria_id
JOIN votaciones_concurso co  ON co.id = ca.concurso_id
JOIN votaciones_edicion e    ON e.id = co.edicion_id
ORDER BY e.anio, co.nombre, ca.nombre, v.titulo, o.nombre;
```

**Cada voto registrado**, del más reciente al más antiguo:

```sql
SELECT vo.id AS voto,
       CONVERT_TZ(vo.fecha_creacion, '+00:00', '-05:00') AS fecha_hora_colombia,
       u.username AS usuario,
       co.nombre AS concurso, ca.nombre AS categoria, o.nombre AS participante
FROM votaciones_voto vo
JOIN auth_user u             ON u.id = vo.usuario_id
JOIN votaciones_categoria ca ON ca.id = vo.categoria_id
JOIN votaciones_concurso co  ON co.id = ca.concurso_id
JOIN votaciones_opcion o     ON o.id = vo.opcion_id
ORDER BY vo.fecha_creacion DESC;
```

> **Sobre la hora:** Django guarda las fechas en hora universal (UTC), que va 5 horas adelante de Colombia. Por eso la consulta usa `CONVERT_TZ(..., '+00:00', '-05:00')`. Si miras la tabla `votaciones_voto` directamente, verás la hora 5 horas adelante: es normal.

**Votos por participante.** Los números deben coincidir con los de la sección **Informes** de la aplicación.

```sql
SELECT co.nombre AS concurso, ca.nombre AS categoria, o.nombre AS participante,
       COUNT(vo.id) AS votos
FROM votaciones_opcion o
JOIN votaciones_votacion v   ON v.id = o.votacion_id
JOIN votaciones_categoria ca ON ca.id = v.categoria_id
JOIN votaciones_concurso co  ON co.id = ca.concurso_id
LEFT JOIN votaciones_voto vo ON vo.opcion_id = o.id
GROUP BY co.nombre, ca.nombre, o.id, o.nombre
ORDER BY co.nombre, ca.nombre, votos DESC;
```

**Comprobar la regla de un voto por categoría.** Esta consulta busca usuarios con más de un voto en la misma categoría. **Debe salir vacía.**

```sql
SELECT usuario_id, categoria_id, COUNT(*) AS votos
FROM votaciones_voto
GROUP BY usuario_id, categoria_id, edicion_id
HAVING COUNT(*) > 1;
```

**Ejercicio para comprobarlo tú mismo:**

1. Ejecuta la consulta de votos y anota cuántas filas salen.
2. En la aplicación, vota con un usuario en una categoría donde todavía no haya votado.
3. Vuelve a Workbench y ejecuta otra vez la misma consulta (o pulsa el botón de actualizar del resultado): aparece una fila nueva con tu usuario, el participante y la hora.

Haz lo mismo creando un concurso en **Administración** y ejecutando la consulta de la jerarquía.

> Estas consultas solo **leen** datos. No uses `INSERT`, `UPDATE` ni `DELETE` en Workbench: los cambios se hacen desde la aplicación, que es la que aplica las reglas.

---

## 9. Si ya tenías el proyecto: cómo actualizarlo

Cuando un compañero suba cambios nuevos a `main`:

```powershell
cd C:\dev\festival-vallenato
.\.venv\Scripts\Activate.ps1
git switch main
git pull
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py test
```

- `git pull` trae los cambios de GitHub. Si avisa que tienes cambios sin guardar, primero haz commit de tu trabajo o pregunta al equipo.
- `pip install` instala librerías nuevas, si las hay.
- `migrate` aplica los cambios de las tablas. **Si lo olvidas, aparecen errores como «Unknown column» o «Table doesn't exist».**
- Revisa también si `.env.example` tiene variables nuevas y cópialas a tu `.env`.

---

## 10. Problemas frecuentes y cómo resolverlos

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| Al escribir `python` se abre la Microsoft Store | Alias de Windows | Usa `py` en lugar de `python` para crear el entorno. Una vez activo `(.venv)`, `python` ya funciona. También puedes desactivar los alias en *Configuración → Aplicaciones → Configuración avanzada de aplicaciones → Alias de ejecución de aplicaciones*. |
| `py -3.13` dice que no encuentra esa versión | Python 3.13 no está instalado | Instálalo (paso 3.2). |
| *«la ejecución de scripts está deshabilitada en este sistema»* | Política de PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y responde `S`. |
| `No module named 'django'` | El entorno virtual no está activo | `.\.venv\Scripts\Activate.ps1` y verifica que aparezca `(.venv)`. |
| Error al instalar `mysqlclient` (*Microsoft Visual C++…* o *mysql_config not found*) | Se está usando una versión de Python sin instalador listo para mysqlclient | Usa Python **3.13**: borra la carpeta `.venv`, créala de nuevo con `py -3.13 -m venv .venv` y repite el paso 3. |
| `KeyError: 'DJANGO_SECRET_KEY'` | Falta el archivo `.env` o no está en la carpeta correcta | Crea `.env` en la carpeta principal, al lado de `manage.py` (paso 5). |
| `Access denied for user 'festival_app'@'localhost'` | Usuario o contraseña de MySQL incorrectos en el `.env` | Revisa `DB_USER` y `DB_PASSWORD`; deben ser los del paso 4. |
| `Unknown database 'festival_vallenato'` | No se creó la base de datos | Ejecuta el `CREATE DATABASE` del paso 4. |
| `Can't connect to MySQL server on '127.0.0.1'` | El servicio de MySQL está apagado | Abre *Servicios* de Windows (`Win + R`, escribe `services.msc`), busca **MySQL84** y pulsa *Iniciar*. |
| `Unknown column ...` o `Table ... doesn't exist` | Faltan migraciones | `python manage.py migrate`. |
| Las pruebas fallan con *«Access denied … database 'test_festival_vallenato'»* | Falta el permiso para la base de pruebas | Ejecuta en Workbench la línea `GRANT ALL PRIVILEGES ON test_festival_vallenato.* ...` del paso 4. |
| `Error: That port is already in use` | Ya hay otro servidor encendido | Ciérralo con `Ctrl + C` en su terminal, o usa otro puerto: `python manage.py runserver 8001`. |
| No aparece el menú Administración, Usuarios ni Informes | El usuario no es administrador | Inicia sesión con el usuario creado con `createsuperuser`. |
| Una votación no aparece en la lista | No cumple alguna condición | Revisa las condiciones de la [sección 5](#5-primeros-pasos-dentro-de-la-aplicación). |
| El correo de recuperación no llega | Gmail no configurado o clave incorrecta | Revisa la [sección 6](#6-correo-para-recuperar-la-contraseña-gmail) y prueba con `sendtestemail`. Revisa también la carpeta de spam. |
| La página se ve sin estilos ni íconos | No hay internet (Bootstrap se carga desde internet) | Conéctate a internet y recarga con `Ctrl + F5`. |

---

## 11. Páginas de la aplicación

| Dirección | Página | Quién puede entrar |
|---|---|---|
| `/` | Inicio | Todos |
| `/registro/` | Crear cuenta | Todos |
| `/login/` | Iniciar sesión | Todos |
| `/recuperar-clave/` | ¿Olvidaste tu contraseña? | Todos |
| `/categorias/` | Concursos y sus categorías | Todos |
| `/votaciones/` | Votaciones disponibles hoy | Todos |
| `/votaciones/<id>/votar/` | Votar y confirmar | Usuarios con sesión iniciada |
| `/votaciones/<id>/resultados/` | Resultados de una votación terminada | Todos |
| `/administracion/` | Sección Administración | Administradores |
| `/usuarios/` | Sección Usuarios | Administradores |
| `/informes/` | Sección Informes y descarga CSV | Administradores |
| `/admin/` | Django Admin | Administradores |

---

## 12. Estructura del proyecto

```text
festival-vallenato/
├── config/                 # Configuración del proyecto Django
│   ├── settings.py         # Lee las claves del archivo .env
│   └── urls.py             # Une las rutas de las apps
├── votaciones/             # App principal (parte pública)
│   ├── migrations/         # Historial de cambios de las tablas
│   ├── tests/              # Pruebas automáticas
│   ├── admin.py            # Configuración de Django Admin
│   ├── forms.py            # Registro, voto y recuperación de contraseña
│   ├── models.py           # Edición, Concurso, Categoría, Votación, Opción y Voto
│   ├── urls.py             # Rutas públicas
│   └── views.py            # Lógica de las páginas públicas
├── panel/                  # App de las secciones para administradores
│   ├── tests/              # Pruebas de Administración, Usuarios e Informes
│   ├── forms.py            # Formularios de Administración
│   ├── informes.py         # Sección Informes (tablero y CSV)
│   ├── permisos.py         # Solo deja entrar a administradores
│   ├── urls.py             # Rutas /administracion/, /usuarios/ e /informes/
│   ├── usuarios.py         # Sección Usuarios
│   └── views.py            # Sección Administración
├── templates/              # Plantillas HTML
│   ├── base.html           # Diseño común: menú, mensajes y pie de página
│   ├── votaciones/         # Páginas públicas y correos
│   └── panel/              # Páginas de las secciones de administrador
├── static/css/             # Estilos: festival.css (sitio) y panel.css (secciones)
├── .env.example            # Plantilla de variables (sin claves reales)
├── .gitignore              # Archivos que Git no sube (.env, .venv, etc.)
├── manage.py               # Comandos de Django
├── requirements.txt        # Librerías del proyecto
└── README.md
```

**Patrón MVT de Django en este proyecto:**

- **Modelo:** `models.py` define las tablas de MySQL.
- **Vista:** `views.py`, `usuarios.py` e `informes.py` consultan los datos y eligen qué plantilla mostrar.
- **Plantilla:** los archivos de `templates/` son el HTML que ve el usuario.

---

## 13. Seguridad

- Las contraseñas de los usuarios se guardan **cifradas** por Django. Nadie puede verlas, ni siquiera un administrador: solo se puede enviar un enlace para crear una nueva.
- Las claves (Django, MySQL y Gmail) viven **solo en el archivo `.env`**, que Git ignora. **Nunca subas el `.env`, ni pegues claves en el código, el README, capturas de pantalla, el PDF o el video.**
- Las secciones de administrador verifican en el servidor que el usuario sea administrador; si no lo es, responden «Acceso denegado».
- Votar, activar, desactivar y eliminar solo funcionan con formularios protegidos contra CSRF.
- Las reglas de votación (un voto por categoría, fechas, estados activos) se validan en el servidor y en la base de datos.
- Esta configuración es para **desarrollo local** (`DEBUG = True`). No está preparada para publicarse en internet.

---

## 14. Equipo

Proyecto académico del curso Desarrollo Web (grupo 61), Fundación Universitaria del Área Andina.

- Sebastian David Baracaldo Marín
- Fernando Coronell Molina
- Javik Trujillo Mateus
- Dahiana Herrera Ramírez

Proyecto académico sin licencia de distribución especificada.
