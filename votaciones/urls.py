
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("categorias/", views.categorias, name="categorias"),
    path("registro/", views.registro, name="registro"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="votaciones/login.html"
        ),
        name="login",
    ),
    path("logout/", views.cerrar_sesion, name="logout"),
    path("votaciones/", views.votaciones, name="votaciones"),
    path(
        "votaciones/<int:votacion_id>/votar/",
        views.votar,
        name="votar",
    ),
    path(
        "votaciones/<int:votacion_id>/resultados/",
        views.resultados,
        name="resultados",
    ),
    
    
]