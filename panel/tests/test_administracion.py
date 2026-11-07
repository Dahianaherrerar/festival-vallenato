"""Pruebas de la sección Administración (panel propio, solo para administradores)."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion, Voto

Usuario = get_user_model()


class BaseAdministracionTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin_panel", password="ClaveDePrueba-2026", is_staff=True
        )
        self.votante = Usuario.objects.create_user(
            username="votante_panel", password="ClaveDePrueba-2026"
        )
        self.edicion = Edicion.objects.create(nombre="Festival 2026", anio=2026, activa=True)
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
        self.opcion = Opcion.objects.create(votacion=self.votacion, nombre="Opción A")

    def entrar_como_admin(self):
        self.client.force_login(self.admin)

    def mensajes(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)]


class AccesoTests(BaseAdministracionTests):
    def test_sin_sesion_redirige_al_login(self):
        url = reverse("panel_inicio")

        respuesta = self.client.get(url)

        self.assertRedirects(respuesta, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

    def test_usuario_normal_recibe_acceso_denegado(self):
        self.client.force_login(self.votante)

        respuesta = self.client.get(reverse("panel_lista", args=["concursos"]))

        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(respuesta, "Acceso denegado", status_code=403)

    def test_administrador_entra_y_ve_el_resumen(self):
        self.entrar_como_admin()

        respuesta = self.client.get(reverse("panel_inicio"))

        self.assertEqual(respuesta.status_code, 200)
        for titulo in ["Ediciones", "Concursos", "Categorías", "Votaciones", "Participantes"]:
            self.assertContains(respuesta, titulo)

    def test_menu_muestra_administracion_solo_al_administrador(self):
        self.client.force_login(self.votante)
        self.assertNotContains(self.client.get(reverse("inicio")), reverse("panel_inicio"))

        self.entrar_como_admin()
        self.assertContains(self.client.get(reverse("inicio")), reverse("panel_inicio"))

    def test_seccion_inexistente_responde_404(self):
        self.entrar_como_admin()

        respuesta = self.client.get(reverse("panel_lista", args=["inventada"]))

        self.assertEqual(respuesta.status_code, 404)


class CrearTests(BaseAdministracionTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_crear_edicion(self):
        respuesta = self.client.post(
            reverse("panel_crear", args=["ediciones"]),
            {"anio": 2028, "nombre": "Festival 2028", "descripcion": "", "activa": "on"},
        )

        self.assertRedirects(respuesta, reverse("panel_lista", args=["ediciones"]))
        self.assertTrue(Edicion.objects.filter(anio=2028).exists())

    def test_crear_concurso_categoria_votacion_y_participante(self):
        self.client.post(
            reverse("panel_crear", args=["concursos"]),
            {"edicion": self.edicion.pk, "nombre": "Acordeón", "activo": "on"},
        )
        concurso = Concurso.objects.get(nombre="Acordeón")

        self.client.post(
            reverse("panel_crear", args=["categorias"]),
            {"concurso": concurso.pk, "nombre": "Acordeón Juvenil", "activa": "on"},
        )
        categoria = Categoria.objects.get(nombre="Acordeón Juvenil")
        self.assertEqual(categoria.edicion, self.edicion)

        self.client.post(
            reverse("panel_crear", args=["votaciones"]),
            {
                "categoria": categoria.pk,
                "titulo": "Votación juvenil",
                "fecha_inicio": "2026-04-25T08:00",
                "fecha_fin": "2026-04-30T18:00",
                "abierta": "on",
            },
        )
        votacion = Votacion.objects.get(titulo="Votación juvenil")

        self.client.post(
            reverse("panel_crear", args=["participantes"]),
            {"votacion": votacion.pk, "nombre": "Participante 1", "activo": "on"},
        )
        self.assertTrue(Opcion.objects.filter(votacion=votacion, nombre="Participante 1").exists())

    def test_edicion_con_anio_repetido_muestra_error(self):
        respuesta = self.client.post(
            reverse("panel_crear", args=["ediciones"]),
            {"anio": 2026, "nombre": "Otra 2026"},
        )

        self.assertContains(respuesta, "Ya existe una edición con ese año.")

    def test_concurso_repetido_en_la_misma_edicion_muestra_error(self):
        respuesta = self.client.post(
            reverse("panel_crear", args=["concursos"]),
            {"edicion": self.edicion.pk, "nombre": "piquería"},
        )

        self.assertContains(respuesta, "Ya existe un concurso con ese nombre en esta edición.")
        self.assertEqual(Concurso.objects.filter(edicion=self.edicion).count(), 1)

    def test_votacion_con_cierre_antes_del_inicio_muestra_error(self):
        respuesta = self.client.post(
            reverse("panel_crear", args=["votaciones"]),
            {
                "categoria": self.categoria.pk,
                "titulo": "Fechas al revés",
                "fecha_inicio": "2026-04-30T18:00",
                "fecha_fin": "2026-04-25T08:00",
            },
        )

        self.assertContains(respuesta, "La fecha de finalización debe ser posterior")
        self.assertFalse(Votacion.objects.filter(titulo="Fechas al revés").exists())

    def test_nuevo_desde_lista_filtrada_preselecciona_el_padre(self):
        respuesta = self.client.get(
            reverse("panel_crear", args=["categorias"]), {"concurso": self.concurso.pk}
        )

        self.assertEqual(respuesta.context["form"].initial["concurso"], str(self.concurso.pk))


class ListaYEditarTests(BaseAdministracionTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_lista_filtra_por_concurso_y_busca_por_nombre(self):
        otro = Concurso.objects.create(edicion=self.edicion, nombre="Acordeón")
        Categoria.objects.create(concurso=otro, nombre="Acordeón Profesional")
        url = reverse("panel_lista", args=["categorias"])

        filtrada = self.client.get(url, {"concurso": self.concurso.pk})
        buscada = self.client.get(url, {"q": "profesional"})

        self.assertContains(filtrada, "Piquería Infantil")
        self.assertNotContains(filtrada, "Acordeón Profesional")
        self.assertContains(buscada, "Acordeón Profesional")
        self.assertNotContains(buscada, "Piquería Infantil")

    def test_editar_concurso(self):
        respuesta = self.client.post(
            reverse("panel_editar", args=["concursos", self.concurso.pk]),
            {"edicion": self.edicion.pk, "nombre": "Piquería Vallenata", "activo": "on"},
        )

        self.assertRedirects(respuesta, reverse("panel_lista", args=["concursos"]))
        self.concurso.refresh_from_db()
        self.assertEqual(self.concurso.nombre, "Piquería Vallenata")


class EstadoTests(BaseAdministracionTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_desactivar_y_activar_concurso(self):
        url = reverse("panel_estado", args=["concursos", self.concurso.pk])

        self.client.post(url)
        self.concurso.refresh_from_db()
        self.assertFalse(self.concurso.activo)

        self.client.post(url)
        self.concurso.refresh_from_db()
        self.assertTrue(self.concurso.activo)

    def test_cambiar_estado_solo_por_post(self):
        respuesta = self.client.get(reverse("panel_estado", args=["concursos", self.concurso.pk]))

        self.assertEqual(respuesta.status_code, 405)

    def test_cerrar_votacion(self):
        self.client.post(reverse("panel_estado", args=["votaciones", self.votacion.pk]))

        self.votacion.refresh_from_db()
        self.assertFalse(self.votacion.abierta)

    def test_conserva_el_filtro_al_volver(self):
        respuesta = self.client.post(
            reverse("panel_estado", args=["categorias", self.categoria.pk]),
            {"filtros": f"concurso={self.concurso.pk}&q=piq&otro=x"},
        )

        self.assertRedirects(
            respuesta,
            f"{reverse('panel_lista', args=['categorias'])}?concurso={self.concurso.pk}&q=piq",
        )

    def test_participante_desactivado_no_aparece_ni_se_puede_votar(self):
        self.client.post(reverse("panel_estado", args=["participantes", self.opcion.pk]))
        self.client.force_login(self.votante)
        url_votar = reverse("votar", args=[self.votacion.pk])

        formulario = self.client.get(url_votar)
        voto = self.client.post(url_votar, {"opcion": self.opcion.pk, "confirmar": "si"})

        self.assertNotContains(formulario, 'name="opcion"')
        self.assertContains(voto, "La opción seleccionada no pertenece a esta votación.")
        self.assertEqual(Voto.objects.count(), 0)


class EliminarTests(BaseAdministracionTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_pide_confirmacion_antes_de_eliminar(self):
        respuesta = self.client.get(reverse("panel_eliminar", args=["participantes", self.opcion.pk]))

        self.assertContains(respuesta, "¿Eliminar el participante «Opción A»?")
        self.assertTrue(Opcion.objects.filter(pk=self.opcion.pk).exists())

    def test_elimina_participante_sin_votos(self):
        respuesta = self.client.post(reverse("panel_eliminar", args=["participantes", self.opcion.pk]))

        self.assertRedirects(respuesta, reverse("panel_lista", args=["participantes"]))
        self.assertFalse(Opcion.objects.filter(pk=self.opcion.pk).exists())

    def test_no_elimina_participante_con_votos(self):
        Voto.objects.create(
            usuario=self.votante,
            edicion=self.edicion,
            categoria=self.categoria,
            votacion=self.votacion,
            opcion=self.opcion,
        )

        respuesta = self.client.post(reverse("panel_eliminar", args=["participantes", self.opcion.pk]))

        self.assertTrue(Opcion.objects.filter(pk=self.opcion.pk).exists())
        self.assertIn(
            "No se puede eliminar el participante «Opción A» porque tiene registros asociados "
            "(1 voto(s)). Puedes desactivarlo en su lugar.",
            self.mensajes(respuesta),
        )

    def test_no_elimina_concurso_con_categorias(self):
        respuesta = self.client.post(reverse("panel_eliminar", args=["concursos", self.concurso.pk]))

        self.assertTrue(Concurso.objects.filter(pk=self.concurso.pk).exists())
        self.assertIn("1 categoría(s)", self.mensajes(respuesta)[0])

    def test_usuario_normal_no_puede_eliminar(self):
        self.client.force_login(self.votante)

        respuesta = self.client.post(reverse("panel_eliminar", args=["participantes", self.opcion.pk]))

        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(Opcion.objects.filter(pk=self.opcion.pk).exists())
