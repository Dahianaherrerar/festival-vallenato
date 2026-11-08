from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Edicion, Opcion, Votacion, Voto


class ConsultaVotoAdminTests(TestCase):
    def setUp(self):
        usuario = get_user_model()
        self.administrador = usuario.objects.create_superuser(
            username="admin_votos",
            email="admin_votos@example.com",
            password="ClaveDePrueba-2026",
        )
        self.votante = usuario.objects.create_user(
            username="votante_admin",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(nombre="Festival de prueba", anio=2027)
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría de prueba",
        )
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votación de prueba",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
        )
        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Participante de prueba",
        )
        self.voto = Voto.objects.create(
            usuario=self.votante,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )
        self.client.force_login(self.administrador)

    def test_administrador_puede_consultar_votos_sin_agregar_editar_ni_eliminar(self):
        lista_url = reverse("admin:votaciones_voto_changelist")
        detalle_url = reverse("admin:votaciones_voto_change", args=[self.voto.pk])

        lista = self.client.get(lista_url)
        detalle = self.client.get(detalle_url)

        self.assertEqual(lista.status_code, 200)
        self.assertContains(lista, "votante_admin")
        self.assertContains(lista, "Categoría de prueba")
        self.assertContains(lista, "2027")
        self.assertNotContains(lista, "/admin/votaciones/voto/add/")
        self.assertEqual(detalle.status_code, 200)
        for campo in (
            "votante_admin",
            "Festival de prueba",
            "Categoría de prueba",
            "Votación de prueba",
            "Participante de prueba",
        ):
            self.assertContains(detalle, campo)
        self.assertNotContains(detalle, "Guardar")
        self.assertNotContains(detalle, "Eliminar")
