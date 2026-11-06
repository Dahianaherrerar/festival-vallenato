"""Pruebas del nivel Concurso: Edición → Concurso → Categoría → Votación → Opción.

Ejemplo usado: Edición 2026 → Concurso «Piquería» → Categorías
«Piquería Infantil» y «Piquería Mayor» → opciones A, B y C.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion, Voto


class BaseConcursoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="votante_concurso",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2026,
            activa=True,
        )
        self.concurso = Concurso.objects.create(edicion=self.edicion, nombre="Piquería")
        self.infantil, self.votacion_infantil = self.crear_categoria("Piquería Infantil")
        self.mayor, self.votacion_mayor = self.crear_categoria("Piquería Mayor")

    def crear_categoria(self, nombre, concurso=None):
        categoria = Categoria.objects.create(
            concurso=concurso or self.concurso,
            nombre=nombre,
        )
        ahora = timezone.now()
        votacion = Votacion.objects.create(
            categoria=categoria,
            titulo=f"Votación {nombre}",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        for letra in "ABC":
            Opcion.objects.create(votacion=votacion, nombre=f"Opción {letra}")
        return categoria, votacion

    def votar(self, votacion):
        opcion = votacion.opciones.first()
        return self.client.post(
            reverse("votar", args=[votacion.pk]),
            {"opcion": opcion.pk, "confirmar": "si"},
        )

    def mensajes(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)]


class ModeloConcursoTests(BaseConcursoTests):
    def test_categoria_toma_la_edicion_de_su_concurso(self):
        self.assertEqual(self.infantil.concurso, self.concurso)
        self.assertEqual(self.infantil.edicion, self.edicion)
        self.assertEqual(
            list(self.concurso.categorias.order_by("nombre")),
            [self.infantil, self.mayor],
        )

    def test_categoria_creada_solo_con_edicion_queda_en_concurso_general(self):
        categoria = Categoria.objects.create(edicion=self.edicion, nombre="Sin concurso")

        self.assertEqual(categoria.concurso.nombre, Concurso.NOMBRE_GENERAL)
        self.assertEqual(categoria.concurso.edicion, self.edicion)

    def test_cambiar_la_edicion_del_concurso_actualiza_sus_categorias(self):
        otra_edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027)

        self.concurso.edicion = otra_edicion
        self.concurso.save()

        self.infantil.refresh_from_db()
        self.assertEqual(self.infantil.edicion, otra_edicion)

    def test_no_se_repite_el_nombre_del_concurso_en_la_misma_edicion(self):
        with self.assertRaises(IntegrityError):
            Concurso.objects.create(edicion=self.edicion, nombre="Piquería")

    def test_el_mismo_concurso_puede_existir_en_otra_edicion(self):
        otra_edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027)

        concurso = Concurso.objects.create(edicion=otra_edicion, nombre="Piquería")

        self.assertEqual(concurso.edicion, otra_edicion)


class VotoPorCategoriaDelConcursoTests(BaseConcursoTests):
    def test_puede_votar_en_dos_categorias_del_mismo_concurso(self):
        self.client.force_login(self.usuario)

        self.votar(self.votacion_infantil)
        self.votar(self.votacion_mayor)

        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)

    def test_no_puede_votar_dos_veces_en_la_misma_categoria(self):
        self.client.force_login(self.usuario)
        self.votar(self.votacion_infantil)

        respuesta = self.votar(self.votacion_infantil)

        self.assertIn(
            "Ya registraste tu voto en esta categoría para esta edición.",
            self.mensajes(respuesta),
        )
        self.assertEqual(
            Voto.objects.filter(usuario=self.usuario, categoria=self.infantil).count(),
            1,
        )


class ConcursoDesactivadoTests(BaseConcursoTests):
    def setUp(self):
        super().setUp()
        self.concurso.activo = False
        self.concurso.save()

    def test_concurso_desactivado_rechaza_el_voto(self):
        self.client.force_login(self.usuario)

        respuesta = self.votar(self.votacion_infantil)

        self.assertRedirects(respuesta, reverse("votaciones"))
        self.assertIn(
            "El concurso «Piquería» no está habilitado para votar.",
            self.mensajes(respuesta),
        )
        self.assertEqual(Voto.objects.count(), 0)

    def test_listas_ocultan_categorias_y_votaciones_del_concurso_desactivado(self):
        categorias = self.client.get(reverse("categorias"))
        votaciones = self.client.get(reverse("votaciones"))

        self.assertNotContains(categorias, "Piquería Infantil")
        self.assertNotContains(votaciones, "Votación Piquería Infantil")


class ConcursoEnPantallasTests(BaseConcursoTests):
    def test_las_listas_muestran_concurso_y_categoria(self):
        categorias = self.client.get(reverse("categorias"))
        votaciones = self.client.get(reverse("votaciones"))

        self.assertContains(categorias, "Piquería · Edición 2026")
        self.assertContains(votaciones, "Piquería · Piquería Infantil")

    def test_concursos_agrupan_sus_categorias_y_enlazan_a_sus_votaciones(self):
        respuesta = self.client.get(reverse("categorias"))

        self.assertContains(respuesta, '<i class="bi bi-trophy"></i> Piquería', html=False)
        self.assertContains(respuesta, f"?categoria={self.infantil.pk}")
        self.assertContains(respuesta, f"?categoria={self.mayor.pk}")

    def test_votaciones_filtradas_por_categoria(self):
        respuesta = self.client.get(reverse("votaciones"), {"categoria": self.infantil.pk})

        self.assertContains(respuesta, "Votación Piquería Infantil")
        self.assertNotContains(respuesta, "Votación Piquería Mayor")
        self.assertContains(respuesta, "Ver todas las votaciones")

    def test_filtro_de_categoria_invalido_muestra_todas(self):
        respuesta = self.client.get(reverse("votaciones"), {"categoria": "abc"})

        self.assertContains(respuesta, "Votación Piquería Infantil")
        self.assertContains(respuesta, "Votación Piquería Mayor")

    def test_admin_permite_ver_y_crear_concursos(self):
        admin = get_user_model().objects.create_superuser(
            username="admin_prueba",
            password="ClaveDePrueba-2026",
        )
        self.client.force_login(admin)

        lista = self.client.get(reverse("admin:votaciones_concurso_changelist"))
        nuevo = self.client.get(reverse("admin:votaciones_concurso_add"))

        self.assertContains(lista, "Piquería")
        self.assertEqual(nuevo.status_code, 200)
