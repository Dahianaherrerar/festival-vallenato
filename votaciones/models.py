
from django.conf import settings
from django.db import models


class Edicion(models.Model):
    nombre = models.CharField(max_length=150)
    anio = models.PositiveSmallIntegerField(unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.anio})"


class Categoria(models.Model):
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.PROTECT,
        related_name="categorias",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Votacion(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="votaciones",
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    abierta = models.BooleanField(default=False)
    
    def clean(self):
        super().clean()

        if (
            self.fecha_inicio
            and self.fecha_fin
            and self.fecha_fin <= self.fecha_inicio
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError({
                "fecha_fin": (
                    "La fecha de finalización debe ser posterior "
                    "a la fecha de inicio."
                )
            })

    def __str__(self):
        return self.titulo


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name="opciones",
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Voto(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.PROTECT,
        related_name="votos",
    )
    opcion = models.ForeignKey(
        Opcion,
        on_delete=models.PROTECT,
        related_name="votos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "votacion"],
                name="un_voto_por_usuario_y_votacion",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.votacion}"
