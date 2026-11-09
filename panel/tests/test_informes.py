"""Pruebas de la sección Informes (tablero y descarga CSV para auditoría)."""

import csv
import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion, Voto

Usuario = get_user_model()
CLAVE = "ClaveDePrueba-2026"


class BaseInformesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username="admin_informes", password=CLAVE, is_staff=True)
        self.edicion = Edicion.objects.create(nombre="Festival 2026", anio=2026, activa=True)
        self.piqueria = Concurso.objects.create(edicion=self.edicion, nombre="Piquería")
        self.acordeon = Concurso.objects.create(edicion=self.edicion, nombre="Acordeón")
        self.infantil = Categoria.objects.create(concurso=self.piqueria, nombre="Piquería Infantil")
        self.profesional = Categoria.objects.create(concurso=self.acordeon, nombre="Acordeón Profesional")

        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.infantil,
            titulo="Votación del público infantil",
            fecha_inicio=ahora - timedelta(days=2),
            fecha_fin=ahora + timedelta(days=2),
            abierta=True,
        )
        self.opcion_a = Opcion.objects.create(votacion=self.votacion, nombre="Opción A")
        self.opcion_b = Opcion.objects.create(votacion=self.votacion, nombre="Opción B")
        self.opcion_c = Opcion.objects.create(votacion=self.votacion, nombre="Opción C")

        self.votacion_acordeon = Votacion.objects.create(
            categoria=self.profesional,
            titulo="Votación acordeón profesional",
            fecha_inicio=ahora - timedelta(days=5),
            fecha_fin=ahora - timedelta(days=1),
        )
        self.acordeonero = Opcion.objects.create(votacion=self.votacion_acordeon, nombre="Participante 1")

        # Opción A: 2 votos, Opción B: 1 voto, Opción C: 0; Acordeón: 1 voto.
        self.votantes = [
            Usuario.objects.create_user(username=f"votante{n}", password=CLAVE) for n in range(1, 4)
        ]
        self.votar(self.votantes[0], self.votacion, self.opcion_a)
        self.votar(self.votantes[1], self.votacion, self.opcion_a)
        self.votar(self.votantes[2], self.votacion, self.opcion_b)
        self.votar(self.votantes[0], self.votacion_acordeon, self.acordeonero)

    def votar(self, usuario, votacion, opcion):
        return Voto.objects.create(
            usuario=usuario,
            edicion=votacion.categoria.edicion,
            categoria=votacion.categoria,
            votacion=votacion,
            opcion=opcion,
        )

    def entrar_como_admin(self):
        self.client.force_login(self.admin)

    def leer_csv(self, respuesta):
        texto = respuesta.content.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(texto), delimiter=";"))


class AccesoInformesTests(BaseInformesTests):
    def test_sin_sesion_redirige_al_login(self):
        for nombre in ["informes_tablero", "informes_descargar"]:
            url = reverse(nombre)
            respuesta = self.client.get(url)
            self.assertRedirects(respuesta, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

    def test_votante_recibe_acceso_denegado(self):
        self.client.force_login(self.votantes[0])

        self.assertEqual(self.client.get(reverse("informes_tablero")).status_code, 403)
        self.assertEqual(self.client.get(reverse("informes_descargar")).status_code, 403)

    def test_menu_muestra_informes_solo_al_administrador(self):
        self.client.force_login(self.votantes[0])
        self.assertNotContains(self.client.get(reverse("inicio")), reverse("informes_tablero"))

        self.entrar_como_admin()
        self.assertContains(self.client.get(reverse("inicio")), reverse("informes_tablero"))


class TableroTests(BaseInformesTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_resumen_de_la_edicion_activa(self):
        respuesta = self.client.get(reverse("informes_tablero"))

        self.assertEqual(respuesta.context["edicion"], self.edicion)
        self.assertEqual(respuesta.context["resumen"]["total"], 4)
        self.assertEqual(respuesta.context["resumen"]["votantes"], 3)
        self.assertEqual(respuesta.context["total_votaciones"], 2)

    def test_agrupa_por_concurso_categoria_y_participante(self):
        respuesta = self.client.get(reverse("informes_tablero"))
        concursos = {item["concurso"].nombre: item for item in respuesta.context["concursos"]}

        self.assertEqual(concursos["Piquería"]["total"], 3)
        self.assertEqual(concursos["Piquería"]["porcentaje"], 75.0)
        self.assertEqual(concursos["Acordeón"]["total"], 1)

        votacion = concursos["Piquería"]["categorias"][0]["votaciones"][0]
        conteo = [(f["opcion"].nombre, f["votos"], f["porcentaje"]) for f in votacion["opciones"]]
        self.assertEqual(conteo, [("Opción A", 2, 66.7), ("Opción B", 1, 33.3), ("Opción C", 0, 0.0)])

    def test_marca_quien_va_ganando_y_el_ganador(self):
        respuesta = self.client.get(reverse("informes_tablero"))

        self.assertContains(respuesta, "Va ganando")  # Piquería sigue abierta.
        self.assertContains(respuesta, "Ganador")  # Acordeón ya terminó.
        self.assertContains(respuesta, "En curso · resultados parciales")

    def test_muestra_correctamente_los_cuatro_estados(self):
        ahora = timezone.now()

        programada = Votacion.objects.create(
            categoria=self.infantil,
            titulo="Votación programada",
            fecha_inicio=ahora + timedelta(days=2),
            fecha_fin=ahora + timedelta(days=4),
            abierta=True,
        )

        pendiente = Votacion.objects.create(
            categoria=self.infantil,
            titulo="Votación pendiente de cierre",
            fecha_inicio=ahora - timedelta(days=4),
            fecha_fin=ahora - timedelta(days=1),
            abierta=True,
        )

        respuesta = self.client.get(reverse("informes_tablero"))

        estados = {
            votacion["votacion"].titulo: votacion["estado"]
            for concurso in respuesta.context["concursos"]
            for categoria in concurso["categorias"]
            for votacion in categoria["votaciones"]
        }

        self.assertEqual(estados[self.votacion.titulo], "En curso")
        self.assertEqual(estados[self.votacion_acordeon.titulo], "Finalizada")
        self.assertEqual(estados[programada.titulo], "Programada")
        self.assertEqual(estados[pendiente.titulo], "Pendiente de cierre")

    def test_empate(self):
        self.votar(Usuario.objects.create_user(username="votante4", password=CLAVE), self.votacion, self.opcion_b)

        respuesta = self.client.get(reverse("informes_tablero"))

        self.assertContains(respuesta, "Empate", count=2)

    def test_filtra_por_concurso(self):
        respuesta = self.client.get(
            reverse("informes_tablero"), {"edicion": self.edicion.pk, "concurso": self.acordeon.pk}
        )

        self.assertEqual(respuesta.context["resumen"]["total"], 1)
        self.assertEqual([i["concurso"] for i in respuesta.context["concursos"]], [self.acordeon])
        self.assertNotContains(respuesta, "Piquería Infantil")

    def test_otra_edicion_no_mezcla_resultados(self):
        anterior = Edicion.objects.create(nombre="Festival 2025", anio=2025, activa=False)

        respuesta = self.client.get(reverse("informes_tablero"), {"edicion": anterior.pk})

        self.assertEqual(respuesta.context["resumen"]["total"], 0)
        self.assertContains(respuesta, "No hay votaciones registradas en esta edición.")

    def test_edicion_inexistente_responde_404(self):
        respuesta = self.client.get(reverse("informes_tablero"), {"edicion": 9999})

        self.assertEqual(respuesta.status_code, 404)


class DescargarCsvTests(BaseInformesTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_descarga_un_csv_para_excel(self):
        respuesta = self.client.get(reverse("informes_descargar"), {"edicion": self.edicion.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn('attachment; filename="informe-votaciones-2026-', respuesta["Content-Disposition"])
        self.assertTrue(respuesta.content.startswith("﻿".encode("utf-8")))

    def test_incluye_encabezado_resumen_y_detalle(self):
        filas = self.leer_csv(self.client.get(reverse("informes_descargar")))

        self.assertIn(["Generado por", "admin_informes"], filas)
        self.assertIn(["Total de votos", "4"], filas)
        self.assertIn(
            ["Piquería", "Piquería Infantil", "Votación del público infantil", "En curso", "Opción A", "2", "66,7", "Va ganando"],
            filas,
        )
        self.assertIn(
            ["Acordeón", "Acordeón Profesional", "Votación acordeón profesional", "Finalizada", "Participante 1", "1", "100,0", "Ganador"],
            filas,
        )

        inicio_detalle = filas.index(["DETALLE DE VOTOS"]) + 2
        detalle = filas[inicio_detalle:]
        self.assertEqual(len(detalle), Voto.objects.count())
        self.assertEqual(
            sorted((f[2], f[6]) for f in detalle),
            [("votante1", "Opción A"), ("votante1", "Participante 1"), ("votante2", "Opción A"), ("votante3", "Opción B")],
        )

    def test_csv_incluye_los_cuatro_estados(self):
        ahora = timezone.now()

        programada = Votacion.objects.create(
            categoria=self.infantil,
            titulo="Votación programada",
            fecha_inicio=ahora + timedelta(days=2),
            fecha_fin=ahora + timedelta(days=4),
            abierta=True,
        )
        Opcion.objects.create(
            votacion=programada,
            nombre="Participante programado",
        )

        pendiente = Votacion.objects.create(
            categoria=self.infantil,
            titulo="Votación pendiente de cierre",
            fecha_inicio=ahora - timedelta(days=4),
            fecha_fin=ahora - timedelta(days=1),
            abierta=True,
        )
        Opcion.objects.create(
            votacion=pendiente,
            nombre="Participante pendiente",
        )

        filas = self.leer_csv(
            self.client.get(reverse("informes_descargar"))
        )

        estados = {
            fila[3]
            for fila in filas
            if len(fila) == 8 and fila[0] in ("Piquería", "Acordeón")
        }

        self.assertEqual(
            estados,
            {"Programada", "En curso", "Pendiente de cierre", "Finalizada"},
        )

    def test_respeta_el_filtro_de_concurso(self):
        respuesta = self.client.get(
            reverse("informes_descargar"), {"edicion": self.edicion.pk, "concurso": self.piqueria.pk}
        )
        filas = self.leer_csv(respuesta)

        self.assertIn("-piqueria-", respuesta["Content-Disposition"])
        self.assertIn(["Concurso", "Piquería"], filas)
        self.assertIn(["Total de votos", "3"], filas)
        self.assertFalse(any("Participante 1" in fila for fila in filas))

    def test_textos_que_parecen_formulas_se_neutralizan(self):
        tramposo = Usuario.objects.create_user(username="@SUMA", password=CLAVE)
        self.votar(tramposo, self.votacion, self.opcion_c)

        filas = self.leer_csv(self.client.get(reverse("informes_descargar")))

        usuarios = [
            fila[2]
            for fila in filas
            if len(fila) == 7 and fila[2] in ("'@SUMA", "@SUMA")
        ]

        self.assertEqual(usuarios, ["'@SUMA"])