from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Edicion, Opcion, Votacion, Voto


class VistasVotacionesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="usuario_prueba",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de la Leyenda Vallenata",
            anio=2027,
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Rey Vallenato",
            activa=True,
        )
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Elección del Rey Vallenato 2027",
            descripcion="Votación de prueba",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Candidato de prueba",
        )

    def test_usuario_no_autenticado_no_puede_votar(self):
        respuesta = self.client.get(
            reverse("votar", args=[self.votacion.pk])
        )

        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={reverse('votar', args=[self.votacion.pk])}",
            fetch_redirect_response=False,
        )

    def test_usuario_autenticado_puede_votar(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[self.votacion.pk]),
            {"opcion": self.opcion.pk},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Voto.objects.filter(
                usuario=self.usuario,
                votacion=self.votacion,
            ).count(),
            1,
        )

    def test_resultados_no_disponibles_antes_del_cierre(self):
        respuesta = self.client.get(
            reverse("resultados", args=[self.votacion.pk])
        )

        self.assertRedirects(respuesta, reverse("votaciones"))

    def test_resultados_disponibles_despues_del_cierre(self):
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )
        self.votacion.fecha_fin = timezone.now() - timedelta(minutes=1)
        self.votacion.save(update_fields=["fecha_fin"])

        respuesta = self.client.get(
            reverse("resultados", args=[self.votacion.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Candidato de prueba")
        self.assertContains(respuesta, "1")

    def test_usuario_no_puede_votar_con_opcion_de_otra_votacion(self):
        ahora = timezone.now()
        otra_votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Otra votación de prueba",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        opcion_ajena = Opcion.objects.create(
            votacion=otra_votacion,
            nombre="Opción de otra votación",
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse("votar", args=[self.votacion.pk]),
            {"opcion": opcion_ajena.pk},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            Voto.objects.filter(
                usuario=self.usuario,
                votacion=self.votacion,
            ).exists()
        )

    def test_votacion_no_permite_fecha_final_anterior_al_inicio(self):
        votacion_invalida = Votacion(
            categoria=self.categoria,
            titulo="Votación con fechas inválidas",
            fecha_inicio=timezone.now() + timedelta(days=2),
            fecha_fin=timezone.now() + timedelta(days=1),
            abierta=True,
        )

        with self.assertRaises(ValidationError):
            votacion_invalida.full_clean()

    def test_admin_puede_abrir_votacion_dentro_del_periodo(self):
        administrador = get_user_model().objects.create_superuser(
            username="admin_prueba",
            email="admin@example.com",
            password="ClaveDePrueba-2026",
        )
        self.client.force_login(administrador)
        self.votacion.abierta = False
        self.votacion.save(update_fields=["abierta"])

        respuesta = self.client.post(
            reverse("admin:votaciones_votacion_changelist"),
            {
                "action": "abrir_votaciones",
                "_selected_action": [str(self.votacion.pk)],
                "index": "0",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.votacion.refresh_from_db()
        self.assertTrue(self.votacion.abierta)

    def test_admin_no_puede_abrir_votacion_fuera_del_periodo(self):
        administrador = get_user_model().objects.create_superuser(
            username="admin_prueba2",
            email="admin2@example.com",
            password="ClaveDePrueba-2026",
        )
        self.client.force_login(administrador)
        self.votacion.fecha_fin = timezone.now() - timedelta(days=1)
        self.votacion.abierta = False
        self.votacion.save(update_fields=["fecha_fin", "abierta"])

        respuesta = self.client.post(
            reverse("admin:votaciones_votacion_changelist"),
            {
                "action": "abrir_votaciones",
                "_selected_action": [str(self.votacion.pk)],
                "index": "0",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.votacion.refresh_from_db()
        self.assertFalse(self.votacion.abierta)

    def test_admin_puede_cerrar_votacion_abierta(self):
        administrador = get_user_model().objects.create_superuser(
            username="admin_prueba3",
            email="admin3@example.com",
            password="ClaveDePrueba-2026",
        )
        self.client.force_login(administrador)
        self.votacion.abierta = True
        self.votacion.save(update_fields=["abierta"])

        respuesta = self.client.post(
            reverse("admin:votaciones_votacion_changelist"),
            {
                "action": "cerrar_votaciones",
                "_selected_action": [str(self.votacion.pk)],
                "index": "0",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.votacion.refresh_from_db()
        self.assertFalse(self.votacion.abierta)
