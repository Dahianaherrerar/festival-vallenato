"""Pruebas de la sección Usuarios (solo para administradores)."""

import re
import smtplib
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()
CLAVE = "ClaveDePrueba-2026"


class BaseUsuariosTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin_usuarios", email="admin@ejemplo.com", password=CLAVE, is_staff=True
        )
        self.votante = Usuario.objects.create_user(
            username="ana_votante", email="ana@ejemplo.com", password=CLAVE, first_name="Ana"
        )
        self.sin_correo = Usuario.objects.create_user(username="sin_correo", password=CLAVE)

    def entrar_como_admin(self):
        self.client.force_login(self.admin)

    def mensajes(self, respuesta):
        return [str(m) for m in get_messages(respuesta.wsgi_request)]


class AccesoUsuariosTests(BaseUsuariosTests):
    def test_sin_sesion_redirige_al_login(self):
        url = reverse("usuarios_lista")

        respuesta = self.client.get(url)

        self.assertRedirects(respuesta, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

    def test_votante_recibe_acceso_denegado(self):
        self.client.force_login(self.votante)

        respuesta = self.client.get(reverse("usuarios_lista"))

        self.assertEqual(respuesta.status_code, 403)

    def test_menu_muestra_usuarios_solo_al_administrador(self):
        self.client.force_login(self.votante)
        self.assertNotContains(self.client.get(reverse("inicio")), reverse("usuarios_lista"))

        self.entrar_como_admin()
        self.assertContains(self.client.get(reverse("inicio")), reverse("usuarios_lista"))


class ListaUsuariosTests(BaseUsuariosTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_muestra_usuarios_con_su_correo(self):
        respuesta = self.client.get(reverse("usuarios_lista"))

        self.assertContains(respuesta, "ana_votante")
        self.assertContains(respuesta, "ana@ejemplo.com")
        self.assertContains(respuesta, "Sin correo")

    def test_no_muestra_contrasenas_ni_su_cifrado(self):
        respuesta = self.client.get(reverse("usuarios_lista"))

        self.assertNotContains(respuesta, CLAVE)
        self.assertNotContains(respuesta, self.votante.password)

    def test_busca_por_correo(self):
        respuesta = self.client.get(reverse("usuarios_lista"), {"q": "ana@"})

        self.assertContains(respuesta, "ana_votante")
        self.assertNotContains(respuesta, "sin_correo")

    def test_filtra_votantes_y_desactivados(self):
        self.sin_correo.is_active = False
        self.sin_correo.save()

        votantes = self.client.get(reverse("usuarios_lista"), {"tipo": "votantes"})
        inactivos = self.client.get(reverse("usuarios_lista"), {"estado": "inactivos"})

        fila = '<span class="fw-semibold">{}</span>'
        self.assertNotContains(votantes, fila.format("admin_usuarios"), html=True)
        self.assertContains(votantes, fila.format("ana_votante"), html=True)
        self.assertContains(inactivos, fila.format("sin_correo"), html=True)
        self.assertNotContains(inactivos, fila.format("ana_votante"), html=True)


class EnviarEnlaceTests(BaseUsuariosTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def enviar(self, usuario, **datos):
        return self.client.post(reverse("usuarios_enlace", args=[usuario.pk]), datos)

    def test_envia_el_enlace_al_correo_del_usuario(self):
        respuesta = self.enviar(self.votante)

        self.assertRedirects(respuesta, reverse("usuarios_lista"))
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ["ana@ejemplo.com"])
        self.assertIn("Un administrador", correo.body)
        self.assertIn("/recuperar-clave/", correo.body)
        self.assertIn("Se envió a «ana_votante» (ana@ejemplo.com)", self.mensajes(respuesta)[0])

    def test_el_usuario_crea_su_nueva_contrasena_con_el_enlace(self):
        self.enviar(self.votante)
        enlace = re.search(r"http://testserver(/recuperar-clave/\S+/)", mail.outbox[0].body).group(1)
        self.client.logout()

        formulario = self.client.get(enlace, follow=True)
        self.client.post(
            formulario.redirect_chain[-1][0],
            {"new_password1": "OtraClave-Segura-99", "new_password2": "OtraClave-Segura-99"},
        )

        self.assertTrue(self.client.login(username="ana_votante", password="OtraClave-Segura-99"))

    def test_usuario_sin_correo_no_recibe_nada(self):
        respuesta = self.enviar(self.sin_correo)

        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("no tiene un correo registrado", self.mensajes(respuesta)[0])

    def test_cuenta_desactivada_no_recibe_enlace(self):
        self.votante.is_active = False
        self.votante.save()

        respuesta = self.enviar(self.votante)

        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("está desactivada", self.mensajes(respuesta)[0])

    def test_si_falla_el_correo_avisa_al_administrador(self):
        error_gmail = smtplib.SMTPAuthenticationError(535, b"")
        with mock.patch("django.core.mail.EmailMultiAlternatives.send", side_effect=error_gmail):
            with self.assertLogs("panel.usuarios", level="ERROR"):
                respuesta = self.enviar(self.votante)

        self.assertIn("No se pudo enviar el correo", self.mensajes(respuesta)[0])

    def test_solo_por_post(self):
        respuesta = self.client.get(reverse("usuarios_enlace", args=[self.votante.pk]))

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(len(mail.outbox), 0)

    def test_votante_no_puede_enviar_enlaces(self):
        self.client.force_login(self.votante)

        respuesta = self.enviar(self.admin)

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_conserva_los_filtros_al_volver(self):
        respuesta = self.enviar(self.votante, filtros="q=ana&tipo=votantes&otro=x")

        self.assertRedirects(respuesta, f"{reverse('usuarios_lista')}?q=ana&tipo=votantes")


class EstadoUsuarioTests(BaseUsuariosTests):
    def setUp(self):
        super().setUp()
        self.entrar_como_admin()

    def test_desactivar_impide_iniciar_sesion_y_activar_lo_permite(self):
        url = reverse("usuarios_estado", args=[self.votante.pk])

        self.client.post(url)
        self.votante.refresh_from_db()
        self.assertFalse(self.votante.is_active)
        self.assertFalse(self.client.login(username="ana_votante", password=CLAVE))

        self.entrar_como_admin()
        self.client.post(url)
        self.votante.refresh_from_db()
        self.assertTrue(self.votante.is_active)
        self.assertTrue(self.client.login(username="ana_votante", password=CLAVE))

    def test_no_puede_desactivarse_a_si_mismo(self):
        respuesta = self.client.post(reverse("usuarios_estado", args=[self.admin.pk]))

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertIn("No puedes desactivar tu propia cuenta.", self.mensajes(respuesta))

    def test_administrador_no_desactiva_a_un_superusuario(self):
        jefe = Usuario.objects.create_superuser(username="jefe", email="jefe@ejemplo.com", password=CLAVE)

        self.client.post(reverse("usuarios_estado", args=[jefe.pk]))

        jefe.refresh_from_db()
        self.assertTrue(jefe.is_active)
