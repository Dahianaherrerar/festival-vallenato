from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .admin import CategoriaInline, OpcionInline
from .models import Categoria, Edicion, Opcion, Votacion, Voto


User = get_user_model()


class AdministracionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.administrador = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="Clave-segura-para-pruebas-2026",
        )
        cls.edicion = Edicion.objects.create(
            anio=2029,
            nombre="Festival 2029",
            activa=True,
        )
        cls.categoria = Categoria.objects.create(
            edicion=cls.edicion,
            nombre="Música",
        )
        ahora = timezone.now()
        cls.votacion = Votacion.objects.create(
            categoria=cls.categoria,
            titulo="Canción favorita",
            fecha_inicio=ahora - timedelta(hours=1),
            fecha_fin=ahora + timedelta(hours=1),
        )
        Opcion.objects.create(votacion=cls.votacion, nombre="Canción A")

    def test_los_cinco_modelos_estan_registrados_en_el_admin(self):
        for modelo in (Edicion, Categoria, Votacion, Opcion, Voto):
            with self.subTest(modelo=modelo.__name__):
                self.assertIn(modelo, admin.site._registry)

    def test_edicion_y_votacion_tienen_sus_inlines(self):
        self.assertEqual(admin.site._registry[Edicion].inlines, (CategoriaInline,))
        self.assertEqual(admin.site._registry[Votacion].inlines, (OpcionInline,))

    def test_pantallas_de_edicion_y_votacion_muestran_sus_inlines(self):
        self.client.force_login(self.administrador)

        respuesta_edicion = self.client.get(
            reverse("admin:votaciones_edicion_change", args=[self.edicion.pk])
        )
        self.assertEqual(respuesta_edicion.status_code, 200)
        self.assertContains(respuesta_edicion, "Música")

        respuesta_votacion = self.client.get(
            reverse("admin:votaciones_votacion_change", args=[self.votacion.pk])
        )
        self.assertEqual(respuesta_votacion.status_code, 200)
        self.assertContains(respuesta_votacion, "Canción A")

    def test_acciones_de_votacion_abren_y_cierran_seleccion(self):
        self.client.force_login(self.administrador)
        url = reverse("admin:votaciones_votacion_changelist")
        datos = {
            "action": "abrir_votaciones",
            "_selected_action": [str(self.votacion.pk)],
            "index": "0",
        }

        self.client.post(url, datos)
        self.votacion.refresh_from_db()
        self.assertTrue(self.votacion.abierta)

        datos["action"] = "cerrar_votaciones"
        self.client.post(url, datos)
        self.votacion.refresh_from_db()
        self.assertFalse(self.votacion.abierta)


class ApiCompatibilidadTests(TestCase):
    def test_api_de_categorias_sigue_disponible(self):
        edicion = Edicion.objects.create(anio=2028, nombre="Festival 2028")
        Categoria.objects.create(edicion=edicion, nombre="Acordeón")

        respuesta = self.client.get(reverse("categoria-list"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()[0]["nombre"], "Acordeón")
