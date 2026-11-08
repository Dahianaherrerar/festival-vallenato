"""Pruebas de la base de datos MySQL.

Cada prueba hace algo en la aplicación (registrarse, votar, crear datos en
Administración) y después consulta las tablas de MySQL directamente con SQL,
sin pasar por los modelos de Django, para comprobar que los datos quedaron
guardados allá. También comprueba reglas que cumple la propia base de datos.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion

Usuario = get_user_model()
CLAVE = "ClaveDePrueba-2026"


def consultar(sql, parametros=None):
    """Ejecuta una consulta SQL en MySQL y devuelve todas las filas."""
    with connection.cursor() as cursor:
        cursor.execute(sql, parametros or [])
        return cursor.fetchall()


def fecha_formulario(fecha):
    return timezone.localtime(fecha).strftime("%Y-%m-%dT%H:%M")


class ConexionMySQLTests(TestCase):
    def test_django_esta_conectado_a_mysql(self):
        version = consultar("SELECT VERSION()")[0][0]

        self.assertEqual(connection.vendor, "mysql")
        self.assertTrue(version.startswith("8."), f"Versión de MySQL: {version}")

    def test_la_conexion_usa_utf8mb4_para_tildes_y_emojis(self):
        juego = consultar("SELECT @@character_set_connection")[0][0]

        self.assertEqual(juego, "utf8mb4")

    def test_las_migraciones_crearon_las_tablas(self):
        tablas = {fila[0] for fila in consultar("SHOW TABLES")}

        for tabla in [
            "auth_user",
            "votaciones_edicion",
            "votaciones_concurso",
            "votaciones_categoria",
            "votaciones_votacion",
            "votaciones_opcion",
            "votaciones_voto",
            "django_migrations",
        ]:
            self.assertIn(tabla, tablas)


class RegistroEnMySQLTests(TestCase):
    def test_el_registro_guarda_el_usuario_con_la_contrasena_cifrada(self):
        self.client.post(
            reverse("registro"),
            {
                "username": "ana_mysql",
                "email": "ana.mysql@ejemplo.com",
                "password1": CLAVE,
                "password2": CLAVE,
            },
        )

        filas = consultar("SELECT username, email, password FROM auth_user WHERE username = %s", ["ana_mysql"])

        self.assertEqual(len(filas), 1)
        usuario, correo, contrasena = filas[0]
        self.assertEqual((usuario, correo), ("ana_mysql", "ana.mysql@ejemplo.com"))
        self.assertNotEqual(contrasena, CLAVE)  # Nunca se guarda tal cual.
        self.assertTrue(contrasena.startswith("pbkdf2_sha256$"))  # Se guarda cifrada.


class AdministracionEnMySQLTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username="admin_mysql", password=CLAVE, is_staff=True)
        self.client.force_login(self.admin)

    def crear(self, clave, datos):
        return self.client.post(reverse("panel_crear", args=[clave]), datos)

    def test_lo_creado_en_administracion_queda_relacionado_en_mysql(self):
        ahora = timezone.now()
        self.crear("ediciones", {"anio": 2027, "nombre": "Festival 2027", "activa": "on"})
        edicion_id = consultar("SELECT id FROM votaciones_edicion WHERE anio = 2027")[0][0]
        self.crear("concursos", {"edicion": edicion_id, "nombre": "Piquería", "activo": "on"})
        concurso_id = consultar("SELECT id FROM votaciones_concurso WHERE nombre = 'Piquería'")[0][0]
        self.crear("categorias", {"concurso": concurso_id, "nombre": "Piquería Infantil", "activa": "on"})
        categoria_id = consultar("SELECT id FROM votaciones_categoria WHERE nombre = 'Piquería Infantil'")[0][0]
        self.crear(
            "votaciones",
            {
                "categoria": categoria_id,
                "titulo": "Votación del público",
                "fecha_inicio": fecha_formulario(ahora - timedelta(days=1)),
                "fecha_fin": fecha_formulario(ahora + timedelta(days=1)),
                "abierta": "on",
            },
        )
        votacion_id = consultar("SELECT id FROM votaciones_votacion WHERE titulo = 'Votación del público'")[0][0]
        for nombre in ["Opción A", "Opción B", "Opción C"]:
            self.crear("participantes", {"votacion": votacion_id, "nombre": nombre, "activo": "on"})

        filas = consultar(
            """
            SELECT e.anio, co.nombre, ca.nombre, v.titulo, o.nombre
            FROM votaciones_opcion o
            JOIN votaciones_votacion v ON v.id = o.votacion_id
            JOIN votaciones_categoria ca ON ca.id = v.categoria_id
            JOIN votaciones_concurso co ON co.id = ca.concurso_id
            JOIN votaciones_edicion e ON e.id = co.edicion_id
            ORDER BY o.nombre
            """
        )

        self.assertEqual(
            filas,
            (
                (2027, "Piquería", "Piquería Infantil", "Votación del público", "Opción A"),
                (2027, "Piquería", "Piquería Infantil", "Votación del público", "Opción B"),
                (2027, "Piquería", "Piquería Infantil", "Votación del público", "Opción C"),
            ),
        )

    def test_tildes_ene_y_emojis_se_guardan_bien(self):
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027)
        nombre = "Canción Inédita · Ñandú 🎶"

        self.crear("concursos", {"edicion": edicion.pk, "nombre": nombre, "activo": "on"})

        self.assertEqual(consultar("SELECT nombre FROM votaciones_concurso")[0][0], nombre)

    def test_desactivar_y_eliminar_en_el_panel_cambia_mysql(self):
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027)
        concurso = Concurso.objects.create(edicion=edicion, nombre="Acordeón")
        categoria = Categoria.objects.create(concurso=concurso, nombre="Acordeón Juvenil")
        ahora = timezone.now()
        votacion = Votacion.objects.create(
            categoria=categoria, titulo="Votación juvenil",
            fecha_inicio=ahora - timedelta(days=1), fecha_fin=ahora + timedelta(days=1),
        )
        opcion = Opcion.objects.create(votacion=votacion, nombre="Participante 1")

        self.client.post(reverse("panel_estado", args=["concursos", concurso.pk]))
        self.client.post(reverse("panel_eliminar", args=["participantes", opcion.pk]))

        activo = consultar("SELECT activo FROM votaciones_concurso WHERE id = %s", [concurso.pk])[0][0]
        self.assertEqual(activo, 0)  # En MySQL, falso se guarda como 0.
        self.assertEqual(consultar("SELECT COUNT(*) FROM votaciones_opcion WHERE id = %s", [opcion.pk])[0][0], 0)


class VotoEnMySQLTests(TestCase):
    def setUp(self):
        self.votante = Usuario.objects.create_user(username="votante_mysql", password=CLAVE)
        self.edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, activa=True)
        self.concurso = Concurso.objects.create(edicion=self.edicion, nombre="Piquería")
        self.categoria = Categoria.objects.create(concurso=self.concurso, nombre="Piquería Infantil")
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votación del público",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        self.opcion_a = Opcion.objects.create(votacion=self.votacion, nombre="Opción A")
        self.opcion_b = Opcion.objects.create(votacion=self.votacion, nombre="Opción B")

    def votar(self, opcion):
        self.client.force_login(self.votante)
        return self.client.post(
            reverse("votar", args=[self.votacion.pk]), {"opcion": opcion.pk, "confirmar": "si"}
        )

    def insertar_voto_con_sql(self, opcion):
        consultar(
            """
            INSERT INTO votaciones_voto (usuario_id, edicion_id, categoria_id, votacion_id, opcion_id, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            [self.votante.pk, self.edicion.pk, self.categoria.pk, self.votacion.pk, opcion.pk],
        )

    def test_el_voto_queda_guardado_en_mysql_con_sus_relaciones(self):
        self.votar(self.opcion_a)

        filas = consultar(
            """
            SELECT u.username, co.nombre, ca.nombre, v.titulo, o.nombre, vo.fecha_creacion
            FROM votaciones_voto vo
            JOIN auth_user u ON u.id = vo.usuario_id
            JOIN votaciones_votacion v ON v.id = vo.votacion_id
            JOIN votaciones_categoria ca ON ca.id = vo.categoria_id
            JOIN votaciones_concurso co ON co.id = ca.concurso_id
            JOIN votaciones_opcion o ON o.id = vo.opcion_id
            """
        )

        self.assertEqual(len(filas), 1)
        self.assertEqual(
            filas[0][:5],
            ("votante_mysql", "Piquería", "Piquería Infantil", "Votación del público", "Opción A"),
        )
        self.assertIsNotNone(filas[0][5])  # Fecha y hora del voto.

    def test_mysql_rechaza_un_segundo_voto_en_la_misma_categoria(self):
        """La regla «un voto por categoría» la cumple la base de datos aunque se salte la aplicación."""
        self.insertar_voto_con_sql(self.opcion_a)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.insertar_voto_con_sql(self.opcion_b)

        self.assertEqual(consultar("SELECT COUNT(*) FROM votaciones_voto")[0][0], 1)

    def test_mysql_no_deja_borrar_un_participante_con_votos(self):
        """La llave foránea protege los votos: no quedan votos «huérfanos»."""
        self.insertar_voto_con_sql(self.opcion_a)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                consultar("DELETE FROM votaciones_opcion WHERE id = %s", [self.opcion_a.pk])

        self.assertEqual(
            consultar("SELECT COUNT(*) FROM votaciones_opcion WHERE id = %s", [self.opcion_a.pk])[0][0], 1
        )
