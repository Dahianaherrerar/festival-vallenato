from django.urls import path

from . import views

urlpatterns = [
    path("administracion/", views.inicio, name="panel_inicio"),
    path("administracion/<str:clave>/", views.lista, name="panel_lista"),
    path("administracion/<str:clave>/nuevo/", views.crear, name="panel_crear"),
    path("administracion/<str:clave>/<int:pk>/editar/", views.editar, name="panel_editar"),
    path("administracion/<str:clave>/<int:pk>/estado/", views.cambiar_estado, name="panel_estado"),
    path("administracion/<str:clave>/<int:pk>/eliminar/", views.eliminar, name="panel_eliminar"),
]
