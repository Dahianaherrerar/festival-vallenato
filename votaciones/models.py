"""Modelos para ediciones, categorías, votaciones y registro de votos."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Edicion(models.Model):
    anio = models.PositiveSmallIntegerField("año", unique=True)
    nombre = models.CharField(max_length=120)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(
        default=False,
        help_text="Es la edición que se muestra en la página de inicio. Solo una puede estar activa.",
    )

    class Meta:
        verbose_name = "edición"
        verbose_name_plural = "ediciones"
        ordering = ["-anio"]

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError(
                {"fecha_fin": "La fecha de fin no puede ser anterior a la fecha de inicio."}
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.activa:
                Edicion.objects.exclude(pk=self.pk).filter(activa=True).update(activa=False)


class Categoria(models.Model):
    edicion = models.ForeignKey(
        Edicion,
        verbose_name="edición",
        on_delete=models.PROTECT,
        related_name="categorias",
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField("descripción", blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["edicion", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "nombre"],
                name="categoria_nombre_unico_por_edicion",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.edicion.anio})"


class Votacion(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="votaciones",
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField("descripción", blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    abierta = models.BooleanField(
        default=False,
        help_text="Para poder votar debe estar marcada y dentro del periodo de votación.",
    )

    class Meta:
        verbose_name = "votación"
        verbose_name_plural = "votaciones"
        ordering = ["titulo"]
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "titulo"],
                name="votacion_titulo_unico_por_categoria",
            )
        ]

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                {"fecha_fin": "La fecha de fin debe ser posterior al inicio."}
            )

    @property
    def edicion(self):
        return self.categoria.edicion

    @property
    def esta_abierta(self):
        return self.abierta and self.fecha_inicio <= timezone.now() <= self.fecha_fin

    @property
    def estado(self):
        if self.esta_abierta:
            return "abierta"
        if timezone.now() < self.fecha_inicio:
            return "proxima"
        return "cerrada"

    @property
    def estado_texto(self):
        return {
            "abierta": "Abierta",
            "proxima": "Próximamente",
            "cerrada": "Cerrada",
        }[self.estado]


class Opcion(models.Model):
    votacion = models.ForeignKey(
        Votacion,
        on_delete=models.CASCADE,
        related_name="opciones",
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField("descripción", blank=True)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["votacion", "nombre"],
                name="opcion_nombre_unico_por_votacion",
            )
        ]

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
        verbose_name = "voto"
        verbose_name_plural = "votos"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "votacion"],
                name="un_voto_por_usuario_y_votacion",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.votacion}"
