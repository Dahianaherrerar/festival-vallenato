from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion, Voto


class BaseParticipacionApiTests(TestCase):
    def setUp(self):
        usuario = get_user_model()
        self.usuario = usuario.objects.create_user(
            username="usuario_participacion",
            password="ClaveDePrueba-2026",
        )
        self.otro_usuario = usuario.objects.create_user(
            username="otro_usuario_participacion",
            password="ClaveDePrueba-2026",
        )
        self.edicion = Edicion.objects.create(
            nombre="Festival de prueba",
            anio=2027,
            activa=True,
        )
        self.concurso = Concurso.objects.create(
            edicion=self.edicion,
            nombre="Piquería",
            activo=True,
        )
        self.categoria = Categoria.objects.create(
            concurso=self.concurso,
            nombre="Piquería Infantil",
            activa=True,
        )
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria,
            titulo="Votación de prueba",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        self.opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Participante elegido",
            descripcion="Opción de prueba",
            activo=True,
        )

    def crear_voto(self, usuario, opcion=None):
        return Voto.objects.create(
            usuario=usuario,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=opcion or self.opcion,
        )


class ParticipacionTests(BaseParticipacionApiTests):
    def test_usuario_sin_sesion_es_redirigido_al_login(self):
        url = reverse("participacion")

        respuesta = self.client.get(url)

        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={url}",
            fetch_redirect_response=False,
        )

    def test_muestra_solo_los_votos_del_usuario_autenticado(self):
        self.crear_voto(self.usuario)
        otra_opcion = Opcion.objects.create(
            votacion=self.votacion,
            nombre="Opción de otro usuario",
        )
        self.crear_voto(self.otro_usuario, otra_opcion)
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("participacion"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "votaciones/participacion.html")
        self.assertContains(respuesta, "Piquería Infantil")
        self.assertContains(respuesta, "Participante elegido")
        self.assertNotContains(respuesta, "Opción de otro usuario")
        self.assertEqual(list(respuesta.context["votos"]), [Voto.objects.get(usuario=self.usuario)])

    def test_muestra_estado_vacio_si_el_usuario_no_ha_votado(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("participacion"))

        self.assertContains(respuesta, "Aún no has registrado votos.")
        self.assertContains(respuesta, reverse("votaciones"))

    def test_menu_enlaza_a_la_participacion_del_usuario(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse("inicio"))

        self.assertContains(respuesta, reverse("participacion"))


class ApiCategoriasTests(BaseParticipacionApiTests):
    def test_ruta_api_se_resuelve_en_el_modulo_api(self):
        vista = resolve(reverse("api_categorias")).func

        self.assertEqual(vista.__module__, "votaciones.api")

    def test_get_devuelve_categorias_votaciones_y_opciones_en_json(self):
        respuesta = self.client.get(reverse("api_categorias"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/json")
        datos = respuesta.json()
        self.assertEqual(len(datos["categorias"]), 1)
        categoria = datos["categorias"][0]
        self.assertEqual(categoria["nombre"], "Piquería Infantil")
        self.assertEqual(categoria["edicion"]["anio"], 2027)
        self.assertEqual(categoria["concurso"]["nombre"], "Piquería")
        self.assertEqual(categoria["votaciones"][0]["titulo"], "Votación de prueba")
        self.assertEqual(
            categoria["votaciones"][0]["opciones"],
            [
                {
                    "id": self.opcion.pk,
                    "nombre": "Participante elegido",
                    "descripcion": "Opción de prueba",
                }
            ],
        )

    def test_api_omite_categorias_y_opciones_inactivas(self):
        categoria_inactiva = Categoria.objects.create(
            concurso=self.concurso,
            nombre="Categoría inactiva",
            activa=False,
        )
        ahora = timezone.now()
        votacion_inactiva = Votacion.objects.create(
            categoria=categoria_inactiva,
            titulo="Votación de categoría inactiva",
            fecha_inicio=ahora - timedelta(days=1),
            fecha_fin=ahora + timedelta(days=1),
            abierta=True,
        )
        Opcion.objects.create(
            votacion=votacion_inactiva,
            nombre="Opción no expuesta",
        )
        self.opcion.activo = False
        self.opcion.save(update_fields=["activo"])

        datos = self.client.get(reverse("api_categorias")).json()

        self.assertEqual(len(datos["categorias"]), 1)
        self.assertEqual(datos["categorias"][0]["votaciones"][0]["opciones"], [])

    def test_endpoint_solo_acepta_get(self):
        respuesta = self.client.post(reverse("api_categorias"))

        self.assertEqual(respuesta.status_code, 405)

    def test_api_devuelve_lista_vacia_sin_categorias_habilitadas(self):
        self.categoria.activa = False
        self.categoria.save(update_fields=["activa"])

        respuesta = self.client.get(reverse("api_categorias"))

        self.assertEqual(respuesta.json(), {"categorias": []})
