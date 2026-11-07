from django.apps import AppConfig


class PanelConfig(AppConfig):
    """Panel propio para administradores: Administración, Usuarios e Informes."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "panel"
    verbose_name = "Panel de administración"
