
from django.contrib import admin
from .models import Edicion, Concurso, Categoria, Votacion, Opcion, Voto
from django.utils import timezone


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "activa")
    list_filter = ("activa", "anio")
    search_fields = ("nombre",)


class CategoriaInline(admin.TabularInline):
    model = Categoria
    extra = 1
    fields = ("nombre", "descripcion", "activa")


@admin.register(Concurso)
class ConcursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activo")
    list_filter = ("activo", "edicion")
    search_fields = ("nombre",)
    inlines = [CategoriaInline]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "concurso", "edicion", "activa")
    list_filter = ("activa", "edicion", "concurso")
    search_fields = ("nombre", "concurso__nombre")


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
    readonly_fields = (
        "usuario",
        "edicion",
        "categoria",
        "votacion",
        "opcion",
        "fecha_creacion",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False
