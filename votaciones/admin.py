from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion, Voto


class CategoriaInline(admin.TabularInline):
    model = Categoria
    extra = 1
    fields = ("nombre", "descripcion", "activa")


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1
    fields = ("nombre", "descripcion")


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "fecha_inicio", "fecha_fin", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "=anio")
    inlines = (CategoriaInline,)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activa")
    list_filter = ("edicion", "activa")
    search_fields = ("nombre", "edicion__nombre", "edicion__anio")
    list_select_related = ("edicion",)


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "fecha_inicio", "fecha_fin", "abierta")
    list_filter = ("abierta", "categoria__edicion", "categoria")
    search_fields = ("titulo", "categoria__nombre")
    list_select_related = ("categoria", "categoria__edicion")
    inlines = (OpcionInline,)
    actions = ("abrir_votaciones", "cerrar_votaciones")

    @admin.action(description="Abrir las votaciones seleccionadas")
    def abrir_votaciones(self, request, queryset):
        actualizadas = queryset.update(abierta=True)
        self.message_user(request, f"{actualizadas} votación(es) abierta(s).")

    @admin.action(description="Cerrar las votaciones seleccionadas")
    def cerrar_votaciones(self, request, queryset):
        actualizadas = queryset.update(abierta=False)
        self.message_user(request, f"{actualizadas} votación(es) cerrada(s).")


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion")
    list_filter = ("votacion",)
    search_fields = ("nombre",)
    list_select_related = ("votacion",)


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "votacion", "opcion", "fecha_creacion")
    list_filter = ("votacion",)
    list_select_related = ("usuario", "votacion", "opcion")
    readonly_fields = ("fecha_creacion",)
