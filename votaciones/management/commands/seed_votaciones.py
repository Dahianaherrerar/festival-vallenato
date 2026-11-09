from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion


class Command(BaseCommand):
    help = (
        "Crea datos ficticios de demostración sin borrar ni modificar "
        "registros existentes."
    )

    def handle(self, *args, **options):
        edicion, _ = Edicion.objects.get_or_create(
            anio=2027,
            defaults={
                "nombre": "Festival de prueba",
                "descripcion": "Edición ficticia para demostraciones.",
                "activa": True,
            },
        )
        concurso, _ = Concurso.objects.get_or_create(
            edicion=edicion,
            nombre="Concurso de demostración",
            defaults={
                "descripcion": "Concurso ficticio para demostraciones.",
                "activo": True,
            },
        )

        piqueria = self.obtener_categoria(
            concurso,
            "Demo - Piquería Infantil",
            activa=True,
        )
        cancion = self.obtener_categoria(
            concurso,
            "Demo - Canción inédita",
            activa=True,
        )
        inactiva = self.obtener_categoria(
            concurso,
            "Demo - Categoría inactiva",
            activa=False,
        )

        self.obtener_votacion(
            piqueria,
            "Primera ronda de prueba",
            ("Participante A", "Participante B"),
        )
        self.obtener_votacion(
            piqueria,
            "Final de prueba",
            ("Finalista A", "Finalista B"),
        )
        self.obtener_votacion(
            cancion,
            "Votación de canción inédita",
            ("Canción A", "Canción B"),
        )
        self.obtener_votacion(
            inactiva,
            "Votación de categoría inactiva",
            ("Opción no disponible",),
        )

        usuarios = get_user_model().objects
        for username, email, nombre in (
            ("votante_demo", "votante_demo@example.com", "Votante"),
            ("votante_demo_dos", "votante_demo_dos@example.com", "Segundo votante"),
        ):
            usuario, creado = usuarios.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": nombre,
                    "is_staff": False,
                    "is_active": True,
                },
            )
            if creado:
                usuario.set_unusable_password()
                usuario.save(update_fields=["password"])

        self.stdout.write(
            self.style.SUCCESS(
                "Datos de demostración listos: edición 2027, dos categorías activas "
                "(una con dos subeventos), una categoría inactiva y dos usuarios ficticios."
            )
        )
        self.stdout.write(
            "Las cuentas votante_demo y votante_demo_dos no tienen contraseña "
            "inicial; asígnales una con «python manage.py changepassword votante_demo» "
            "y repite para votante_demo_dos."
        )

    def obtener_categoria(self, concurso, nombre, *, activa):
        categoria, _ = Categoria.objects.get_or_create(
            concurso=concurso,
            nombre=nombre,
            defaults={
                "descripcion": "Categoría ficticia para pruebas.",
                "activa": activa,
            },
        )
        return categoria

    def obtener_votacion(self, categoria, titulo, opciones):
        ahora = timezone.now()
        votacion, _ = Votacion.objects.get_or_create(
            categoria=categoria,
            titulo=titulo,
            defaults={
                "descripcion": "Votación ficticia para demostraciones.",
                "fecha_inicio": ahora - timedelta(days=1),
                "fecha_fin": ahora + timedelta(days=365),
                "abierta": True,
            },
        )
        for nombre in opciones:
            Opcion.objects.get_or_create(
                votacion=votacion,
                nombre=nombre,
                defaults={"descripcion": "Participante ficticio."},
            )
        return votacion
