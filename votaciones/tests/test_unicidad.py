from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Edicion, Opcion, Votacion, Voto


class UnicidadDeVotosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="usuario_unicidad",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2027,
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría de prueba",
            activa=True,
        )
        self.votacion, self.opcion = self.crear_subevento(
            self.categoria,
            "Primer subevento",
        )

    def crear_subevento(self, categoria, titulo):
        ahora = timezone.now()
        votacion = Votacion.objects.create(
            categoria=categoria,
            titulo=titulo,
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        opcion = Opcion.objects.create(
            votacion=votacion,
            nombre=f"Opción de {titulo}",
        )
        return votacion, opcion

    def registrar_voto(self, votacion, opcion):
        return Voto.objects.create(
            usuario=self.usuario,
            edicion=votacion.categoria.edicion,
            categoria=votacion.categoria,
            votacion=votacion,
            opcion=opcion,
        )

    def test_usuario_no_puede_votar_dos_veces_en_la_misma_votacion(self):
        self.registrar_voto(self.votacion, self.opcion)
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[self.votacion.pk]),
            {"opcion": self.opcion.pk},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Voto.objects.filter(
                usuario=self.usuario,
                categoria=self.categoria,
                edicion=self.edicion,
            ).count(),
            1,
        )

    def test_usuario_no_puede_votar_en_otro_subevento_de_la_misma_categoria(self):
        otro_subevento, otra_opcion = self.crear_subevento(
            self.categoria,
            "Segundo subevento",
        )
        self.registrar_voto(self.votacion, self.opcion)
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[otro_subevento.pk]),
            {"opcion": otra_opcion.pk},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Voto.objects.filter(
                usuario=self.usuario,
                categoria=self.categoria,
                edicion=self.edicion,
            ).count(),
            1,
        )

    def test_restriccion_de_base_de_datos_cubre_otro_subevento(self):
        otro_subevento, otra_opcion = self.crear_subevento(
            self.categoria,
            "Segundo subevento",
        )
        self.registrar_voto(self.votacion, self.opcion)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Voto.objects.create(
                    usuario=self.usuario,
                    edicion=self.edicion,
                    categoria=self.categoria,
                    votacion=otro_subevento,
                    opcion=otra_opcion,
                )

    def test_usuario_puede_votar_en_otra_categoria_de_la_misma_edicion(self):
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Otra categoría de prueba",
            activa=True,
        )
        otra_votacion, otra_opcion = self.crear_subevento(
            otra_categoria,
            "Votación de otra categoría",
        )
        self.registrar_voto(self.votacion, self.opcion)
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[otra_votacion.pk]),
            {"opcion": otra_opcion.pk, "confirmar": "si"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)

    def test_usuario_puede_votar_en_la_misma_categoria_en_otra_edicion(self):
        otra_edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2028,
            activa=True,
        )
        otra_categoria = Categoria.objects.create(
            edicion=otra_edicion,
            nombre=self.categoria.nombre,
            activa=True,
        )
        otra_votacion, otra_opcion = self.crear_subevento(
            otra_categoria,
            "Votación de 2028",
        )
        self.registrar_voto(self.votacion, self.opcion)
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[otra_votacion.pk]),
            {"opcion": otra_opcion.pk, "confirmar": "si"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)

    def test_categoria_requiere_edicion(self):
        categoria = Categoria(nombre="Categoría sin edición")

        with self.assertRaises(ValidationError):
            categoria.full_clean()
