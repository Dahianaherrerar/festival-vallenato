from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion


class SeedVotacionesTests(TestCase):
    def test_crea_datos_ficticios_reutilizables_sin_duplicarlos(self):
        salida = StringIO()

        call_command("seed_votaciones", stdout=salida)

        self.assertTrue(Edicion.objects.filter(anio=2027, activa=True).exists())
        self.assertTrue(
            Categoria.objects.filter(
                nombre="Demo - Piquería Infantil",
                activa=True,
                votaciones__titulo="Primera ronda de prueba",
            ).exists()
        )
        categoria_con_subeventos = Categoria.objects.get(nombre="Demo - Piquería Infantil")
        self.assertEqual(categoria_con_subeventos.votaciones.count(), 2)
        self.assertTrue(
            Categoria.objects.filter(
                nombre="Demo - Categoría inactiva",
                activa=False,
            ).exists()
        )
        self.assertEqual(
            get_user_model().objects.filter(username__in=["votante_demo", "votante_demo_dos"]).count(),
            2,
        )
        self.assertFalse(
            get_user_model().objects.get(username="votante_demo").has_usable_password()
        )

        conteos = (
            Edicion.objects.count(),
            Concurso.objects.count(),
            Categoria.objects.count(),
            Votacion.objects.count(),
            Opcion.objects.count(),
            get_user_model().objects.count(),
        )
        call_command("seed_votaciones", stdout=StringIO())
        self.assertEqual(
            conteos,
            (
                Edicion.objects.count(),
                Concurso.objects.count(),
                Categoria.objects.count(),
                Votacion.objects.count(),
                Opcion.objects.count(),
                get_user_model().objects.count(),
            ),
        )
        self.assertIn("Datos de demostración listos", salida.getvalue())
