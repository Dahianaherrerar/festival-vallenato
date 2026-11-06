
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Edicion(models.Model):
    nombre = models.CharField(max_length=150)
    anio = models.PositiveSmallIntegerField(unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.anio})"


class Concurso(models.Model):
    """Concurso de una edición (ej. Piquería), que agrupa sus categorías."""

    NOMBRE_GENERAL = "Concurso general"

    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.PROTECT,
        related_name="concursos",
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "concurso"
        verbose_name_plural = "concursos"
        ordering = ["edicion", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "nombre"],
                name="concurso_unico_por_edicion",
            )
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Si el concurso cambia de edición, sus categorías cambian con él.
        self.categorias.exclude(edicion=self.edicion).update(edicion=self.edicion)

    def __str__(self):
        return f"{self.nombre} ({self.edicion.anio})"


class Categoria(models.Model):
    concurso = models.ForeignKey(
        Concurso,
        on_delete=models.PROTECT,
        related_name="categorias",
    )
    # La edición se copia del concurso; se conserva para que la regla
    # «un voto por usuario, categoría y edición» y las consultas existentes
    # sigan funcionando igual.
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.PROTECT,
        related_name="categorias",
        editable=False,
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def sincronizar_edicion(self):
        if self.concurso_id:
            self.edicion_id = self.concurso.edicion_id

    def clean_fields(self, exclude=None):
        self.sincronizar_edicion()
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        # Compatibilidad: si una categoría se crea solo con su edición (código
        # o pruebas anteriores al modelo Concurso), queda en el concurso
        # general de esa edición.
        if not self.concurso_id and self.edicion_id:
            self.concurso, _ = Concurso.objects.get_or_create(
                edicion_id=self.edicion_id,
                nombre=Concurso.NOMBRE_GENERAL,
            )
        self.sincronizar_edicion()
        super().save(*args, **kwargs)

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
    edicion = models.ForeignKey(
        Edicion,
        on_delete=models.PROTECT,
        related_name="votos",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="votos",
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

    def clean(self):
        super().clean()
        errors = {}

        if self.votacion_id and self.categoria_id:
            if self.votacion.categoria_id != self.categoria_id:
                errors["categoria"] = (
                    "La categoría debe corresponder a la votación seleccionada."
                )

        if self.opcion_id and self.votacion_id:
            if self.opcion.votacion_id != self.votacion_id:
                errors["opcion"] = (
                    "La opción debe corresponder a la votación seleccionada."
                )

        if self.categoria_id and self.edicion_id:
            if self.categoria.edicion_id != self.edicion_id:
                errors["edicion"] = (
                    "La edición debe corresponder a la categoría seleccionada."
                )

        if errors:
            raise ValidationError(errors)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "categoria", "edicion"],
                name="un_voto_por_usuario_categoria_edicion",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.votacion}"
