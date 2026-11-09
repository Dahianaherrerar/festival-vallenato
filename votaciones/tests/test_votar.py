"""Pruebas del flujo de votación en el servidor (Persona 2).

Casos de la guía de la Entrega 3:
- CP-01: usuario autenticado selecciona una opción válida → se registra un voto.
- CP-04: usuario no autenticado intenta votar → se exige autenticación.
- CP-05: intenta votar en una categoría no habilitada → se rechaza.
- CP-06: envía una opción de otra categoría → se rechaza.
- CSRF: un POST sin token responde 403.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Edicion, Opcion, Votacion, Voto


class BaseVotarTests(TestCase):
    """Datos comunes: una edición activa, una categoría y una votación abierta."""

    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="votante_cp",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2027,
            activa=True,
        )
        self.categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Canción inédita de prueba",
            activa=True,
        )
        self.votacion, self.opcion = self.crear_votacion(
            self.categoria, "Votación principal"
        )
        self.url_votar = reverse("votar", args=[self.votacion.pk])

    def crear_votacion(self, categoria, titulo, **campos):
        ahora = timezone.now()
        datos = {
            "categoria": categoria,
            "titulo": titulo,
            "fecha_inicio": ahora - timedelta(days=1),
            "fecha_fin": ahora + timedelta(days=1),
            "abierta": True,
        }
        datos.update(campos)
        votacion = Votacion.objects.create(**datos)
        opcion = Opcion.objects.create(votacion=votacion, nombre=f"Opción de {titulo}")
        return votacion, opcion

    def mensajes(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)]

    def total_votos(self):
        return Voto.objects.filter(usuario=self.usuario).count()


class CP01VotoValidoTests(BaseVotarTests):
    """CP-01: selección → confirmación → registro en MySQL."""

    def test_seleccionar_opcion_muestra_confirmacion_sin_guardar(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(self.url_votar, {"opcion": self.opcion.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "votaciones/confirmar_voto.html")
        self.assertContains(respuesta, self.opcion.nombre)
        self.assertEqual(self.total_votos(), 0)

    def test_confirmar_registra_un_voto_con_categoria_y_edicion(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            self.url_votar,
            {"opcion": self.opcion.pk, "confirmar": "si"},
        )

        self.assertRedirects(respuesta, reverse("votaciones"))
        voto = Voto.objects.get(usuario=self.usuario)
        self.assertEqual(voto.opcion, self.opcion)
        self.assertEqual(voto.votacion, self.votacion)
        self.assertEqual(voto.categoria, self.categoria)
        self.assertEqual(voto.edicion, self.edicion)
        self.assertIn(
            f"Tu voto por «{self.opcion.nombre}» se registró correctamente.",
            self.mensajes(respuesta),
        )


class CP04AutenticacionTests(BaseVotarTests):
    """CP-04: sin sesión no se puede votar, ni por GET ni por POST."""

    def url_login(self):
        return f"{reverse('login')}?next={self.url_votar}"

    def test_get_sin_sesion_redirige_al_login(self):
        respuesta = self.client.get(self.url_votar)

        self.assertRedirects(respuesta, self.url_login(), fetch_redirect_response=False)

    def test_post_sin_sesion_redirige_al_login_y_no_guarda(self):
        respuesta = self.client.post(
            self.url_votar,
            {"opcion": self.opcion.pk, "confirmar": "si"},
        )

        self.assertRedirects(respuesta, self.url_login(), fetch_redirect_response=False)
        self.assertEqual(Voto.objects.count(), 0)


class CP05CategoriaNoHabilitadaTests(BaseVotarTests):
    """CP-05: se rechaza con mensaje si la categoría, la edición o la votación no están habilitadas."""

    def intentar_votar(self):
        self.client.force_login(self.usuario)
        return self.client.post(
            self.url_votar,
            {"opcion": self.opcion.pk, "confirmar": "si"},
        )

    def assertRechazado(self, respuesta, mensaje):
        self.assertRedirects(respuesta, reverse("votaciones"))
        self.assertIn(mensaje, self.mensajes(respuesta))
        self.assertEqual(self.total_votos(), 0)

    def test_categoria_inactiva_se_rechaza(self):
        self.categoria.activa = False
        self.categoria.save(update_fields=["activa"])

        respuesta = self.intentar_votar()

        self.assertRechazado(
            respuesta,
            f"La categoría «{self.categoria.nombre}» no está habilitada para votar.",
        )

    def test_edicion_inactiva_se_rechaza(self):
        self.edicion.activa = False
        self.edicion.save(update_fields=["activa"])

        respuesta = self.intentar_votar()

        self.assertRechazado(
            respuesta,
            "La edición 2027 no está activa; no se pueden registrar votos.",
        )

    def test_votacion_cerrada_se_rechaza(self):
        self.votacion.abierta = False
        self.votacion.save(update_fields=["abierta"])

        respuesta = self.intentar_votar()

        self.assertRechazado(respuesta, "Esta votación está cerrada y no admite votos.")

    def test_votacion_fuera_de_periodo_se_rechaza(self):
        self.votacion.fecha_fin = timezone.now() - timedelta(minutes=1)
        self.votacion.save(update_fields=["fecha_fin"])

        respuesta = self.intentar_votar()

        self.assertRechazado(
            respuesta,
            "Esta votación no está dentro de su periodo habilitado.",
        )


class ListaVotacionesHabilitadasTests(BaseVotarTests):
    """La lista pública solo muestra votaciones en las que hoy se puede votar."""

    def test_lista_oculta_votaciones_no_habilitadas(self):
        ahora = timezone.now()
        self.crear_votacion(
            self.categoria,
            "Votación vencida",
            fecha_inicio=ahora - timedelta(days=5),
            fecha_fin=ahora - timedelta(days=1),
        )
        self.crear_votacion(
            self.categoria,
            "Votación futura",
            fecha_inicio=ahora + timedelta(days=1),
            fecha_fin=ahora + timedelta(days=5),
        )
        self.crear_votacion(self.categoria, "Votación cerrada", abierta=False)
        categoria_inactiva = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Categoría inactiva",
            activa=False,
        )
        self.crear_votacion(categoria_inactiva, "Votación de categoría inactiva")

        respuesta = self.client.get(reverse("votaciones"))

        self.assertContains(respuesta, "Votación principal")
        self.assertNotContains(respuesta, "Votación vencida")
        self.assertNotContains(respuesta, "Votación futura")
        self.assertNotContains(respuesta, "Votación cerrada")
        self.assertNotContains(respuesta, "Votación de categoría inactiva")

    def test_marca_las_votaciones_de_una_categoria_ya_votada(self):
        otra_votacion, _ = self.crear_votacion(self.categoria, "Segundo subevento")
        self.client.force_login(self.usuario)
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        respuesta = self.client.get(reverse("votaciones"))

        self.assertContains(respuesta, "Ya votaste en esta categoría", count=2)
        self.assertContains(respuesta, "Ver mi participación", count=2)
        self.assertNotContains(
            respuesta,
            reverse("votar", args=[self.votacion.pk]),
        )
        self.assertNotContains(
            respuesta,
            reverse("votar", args=[otra_votacion.pk]),
        )

    def test_categoria_distinta_sigue_mostrando_la_opcion_de_votar(self):
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Otra categoría de prueba",
            activa=True,
        )
        otra_votacion, _ = self.crear_votacion(
            otra_categoria,
            "Votación de otra categoría",
        )
        self.client.force_login(self.usuario)
        Voto.objects.create(
            usuario=self.usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        respuesta = self.client.get(reverse("votaciones"))

        self.assertContains(respuesta, reverse("votar", args=[otra_votacion.pk]))
        self.assertContains(respuesta, "Ya votaste en esta categoría")


class CP06OpcionDeOtraCategoriaTests(BaseVotarTests):
    """CP-06: una opción que pertenece a otra categoría se rechaza."""

    def test_opcion_de_otra_categoria_se_rechaza(self):
        otra_categoria = Categoria.objects.create(
            edicion=self.edicion,
            nombre="Piquería de prueba",
            activa=True,
        )
        _, opcion_ajena = self.crear_votacion(otra_categoria, "Votación de piquería")
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            self.url_votar,
            {"opcion": opcion_ajena.pk, "confirmar": "si"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "votaciones/votar.html")
        self.assertContains(respuesta, "La opción seleccionada no pertenece a esta votación.")
        self.assertIn("No se registró el voto. Revisa tu selección.", self.mensajes(respuesta))
        self.assertEqual(self.total_votos(), 0)

    def test_sin_seleccionar_opcion_se_rechaza(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(self.url_votar, {"confirmar": "si"})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debes seleccionar una opción para votar.")
        self.assertEqual(self.total_votos(), 0)


class CSRFTests(BaseVotarTests):
    """Un POST sin token CSRF responde 403 y no guarda nada."""

    def test_post_sin_token_csrf_responde_403(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)

        respuesta = cliente.post(
            self.url_votar,
            {"opcion": self.opcion.pk, "confirmar": "si"},
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.total_votos(), 0)

    def test_formulario_incluye_token_csrf(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(self.url_votar)

        self.assertContains(respuesta, "csrfmiddlewaretoken")
