from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Edicion, Opcion, Votacion, Voto


class ConcurrenciaDeVotosTests(TransactionTestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="usuario_concurrente",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2027,
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría de concurrencia",
            activa=True,
        )
        ahora = timezone.now()
        self.subeventos = []

        for numero in (1, 2):
            votacion = Votacion.objects.create(
                categoria=self.categoria,
                titulo=f"Subevento {numero}",
                fecha_inicio=ahora - timedelta(days=1),
                fecha_fin=ahora + timedelta(days=1),
                abierta=True,
            )
            opcion = Opcion.objects.create(
                votacion=votacion,
                nombre=f"Opción {numero}",
            )
            self.subeventos.append((votacion.pk, opcion.pk))

    def test_solicitudes_simultaneas_guardan_un_solo_voto(self):
        if connection.vendor != "mysql":
            self.skipTest("La prueba de concurrencia requiere MySQL.")

        barrera = Barrier(2)

        def enviar_voto(subevento):
            close_old_connections()
            try:
                cliente = Client()
                cliente.force_login(self.usuario)
                votacion_id, opcion_id = subevento
                barrera.wait(timeout=10)
                respuesta = cliente.post(
                    reverse("votar", args=[votacion_id]),
                    {"opcion": opcion_id, "confirmar": "si"},
                )
                return respuesta.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            estados = list(executor.map(enviar_voto, self.subeventos))

        self.assertEqual(estados, [302, 302])
        self.assertEqual(
            Voto.objects.filter(
                usuario=self.usuario,
                edicion=self.edicion,
                categoria=self.categoria,
            ).count(),
            1,
        )
