"""Pruebas de la recuperación de contraseña.

Flujo: «¿Olvidaste tu contraseña?» → correo registrado → correo con enlace
→ nueva contraseña y confirmación → contraseña cambiada.
En las pruebas Django guarda los correos en memoria (mail.outbox).
"""

import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse


class RecuperarClaveTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="votante_olvido",
            email="votante@ejemplo.com",
            password="ClaveVieja-2026",
        )

    def pedir_enlace(self, correo="votante@ejemplo.com"):
        return self.client.post(reverse("recuperar_clave"), {"email": correo})

    def enlace_del_correo(self):
        return re.search(r"http://testserver(\S+)", mail.outbox[0].body).group(1)

    def test_login_muestra_olvidaste_tu_contrasena(self):
        respuesta = self.client.get(reverse("login"))

        self.assertContains(respuesta, "¿Olvidaste tu contraseña?")
        self.assertContains(respuesta, reverse("recuperar_clave"))

    def test_pantalla_pide_el_correo_registrado(self):
        respuesta = self.client.get(reverse("recuperar_clave"))

        self.assertContains(respuesta, "Correo electrónico registrado")
        self.assertContains(respuesta, "Restablecer")

    def test_correo_registrado_recibe_el_enlace(self):
        respuesta = self.pedir_enlace()

        self.assertRedirects(respuesta, reverse("recuperar_clave_enviado"))
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ["votante@ejemplo.com"])
        self.assertIn("Restablece tu contraseña", correo.subject)
        self.assertIn("votante_olvido", correo.body)
        self.assertIn("/recuperar-clave/", correo.body)

    def test_mayusculas_en_el_correo_no_importan(self):
        self.pedir_enlace("VOTANTE@Ejemplo.com")

        self.assertEqual(len(mail.outbox), 1)

    def test_correo_no_registrado_no_envia_nada_ni_lo_revela(self):
        respuesta = self.pedir_enlace("nadie@ejemplo.com")

        # Misma respuesta que con un correo registrado: así nadie puede
        # averiguar qué correos tienen cuenta.
        self.assertRedirects(respuesta, reverse("recuperar_clave_enviado"))
        self.assertEqual(len(mail.outbox), 0)

    def test_correo_vacio_muestra_error(self):
        respuesta = self.pedir_enlace("")

        self.assertContains(respuesta, "Escribe el correo con el que te registraste.")
        self.assertEqual(len(mail.outbox), 0)

    def test_enlace_permite_cambiar_la_contrasena(self):
        self.pedir_enlace()
        enlace = self.enlace_del_correo()

        # Django redirige el enlace a una URL interna para no dejar el token
        # a la vista; se sigue esa redirección.
        formulario = self.client.get(enlace, follow=True)
        self.assertContains(formulario, "Nueva contraseña")
        self.assertContains(formulario, "Confirmar contraseña")
        self.assertContains(formulario, "Cambiar")

        respuesta = self.client.post(
            formulario.redirect_chain[-1][0],
            {"new_password1": "ClaveNueva-2026!", "new_password2": "ClaveNueva-2026!"},
        )

        self.assertRedirects(respuesta, reverse("recuperar_clave_listo"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("ClaveNueva-2026!"))
        self.assertTrue(
            self.client.login(username="votante_olvido", password="ClaveNueva-2026!")
        )

    def test_contrasenas_distintas_muestran_error(self):
        self.pedir_enlace()
        formulario = self.client.get(self.enlace_del_correo(), follow=True)

        respuesta = self.client.post(
            formulario.redirect_chain[-1][0],
            {"new_password1": "ClaveNueva-2026!", "new_password2": "OtraClave-2026!"},
        )

        self.assertContains(respuesta, "Las dos contraseñas no coinciden.")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("ClaveVieja-2026"))

    def test_enlace_usado_ya_no_sirve(self):
        self.pedir_enlace()
        enlace = self.enlace_del_correo()
        formulario = self.client.get(enlace, follow=True)
        self.client.post(
            formulario.redirect_chain[-1][0],
            {"new_password1": "ClaveNueva-2026!", "new_password2": "ClaveNueva-2026!"},
        )

        respuesta = self.client.get(enlace, follow=True)

        self.assertContains(respuesta, "El enlace no es válido")
