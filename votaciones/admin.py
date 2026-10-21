from django.contrib import admin
from .models import Categoria, Votacion, Opcion, Voto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


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


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion")
    list_filter = ("votacion",)
    search_fields = ("nombre",)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "votacion",
        "opcion",
        "fecha_creacion",
    )
    list_filter = ("votacion",)
    readonly_fields = ("fecha_creacion",)
