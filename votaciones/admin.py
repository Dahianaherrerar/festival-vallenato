
from django.contrib import admin
from .models import Edicion, Categoria, Votacion, Opcion, Voto
from django.utils import timezone


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "activa")
    list_filter = ("activa", "anio")
    search_fields = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activa")
    list_filter = ("activa", "edicion")
    search_fields = ("nombre",)


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1



@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "categoria",
        "fecha_inicio",
        "fecha_fin",
        "abierta",
    )
    list_filter = ("abierta", "categoria")
    search_fields = ("titulo",)
    inlines = [OpcionInline]

    actions = ["abrir_votaciones", "cerrar_votaciones"]

    @admin.action(description="Abrir votaciones dentro del periodo válido")
    def abrir_votaciones(self, request, queryset):
        ahora = timezone.now()

        actualizadas = queryset.filter(
            fecha_inicio__lte=ahora,
            fecha_fin__gt=ahora,
        ).update(abierta=True)

        self.message_user(
            request,
            f"{actualizadas} votación(es) abierta(s). "
            "Solo se abrieron las que están dentro de su periodo válido.",
        )

    @admin.action(description="Cerrar votaciones seleccionadas")
    def cerrar_votaciones(self, request, queryset):
        actualizadas = queryset.filter(abierta=True).update(abierta=False)

        self.message_user(
            request,
            f"{actualizadas} votación(es) cerrada(s).",
        )



@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion")
    list_filter = ("votacion",)
    search_fields = ("nombre",)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "edicion",
        "categoria",
        "votacion",
        "opcion",
        "fecha_creacion",
    )
    list_filter = ("edicion", "categoria", "votacion", "fecha_creacion")
    search_fields = (
        "usuario__username",
        "categoria__nombre",
        "votacion__titulo",
    )
