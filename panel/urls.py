from django.urls import path

from . import informes, usuarios, views

urlpatterns = [
    path("administracion/", views.inicio, name="panel_inicio"),
    path("administracion/<str:clave>/", views.lista, name="panel_lista"),
    path("administracion/<str:clave>/nuevo/", views.crear, name="panel_crear"),
    path("administracion/<str:clave>/<int:pk>/editar/", views.editar, name="panel_editar"),
    path("administracion/<str:clave>/<int:pk>/estado/", views.cambiar_estado, name="panel_estado"),
    path("administracion/<str:clave>/<int:pk>/eliminar/", views.eliminar, name="panel_eliminar"),
    # Sección Usuarios
    path("usuarios/", usuarios.lista, name="usuarios_lista"),
    path("usuarios/<int:pk>/enlace/", usuarios.enviar_enlace, name="usuarios_enlace"),
    path("usuarios/<int:pk>/estado/", usuarios.cambiar_estado, name="usuarios_estado"),
    # Sección Informes
    path("informes/", informes.tablero, name="informes_tablero"),
    path("informes/descargar/", informes.descargar, name="informes_descargar"),
]
