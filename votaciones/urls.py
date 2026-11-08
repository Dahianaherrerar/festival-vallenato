
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import NuevaClaveForm, RecuperarClaveForm

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
    # Recuperación de contraseña (vistas de Django con plantillas propias):
    # pedir correo → aviso de envío → nueva contraseña → listo.
    path(
        "recuperar-clave/",
        auth_views.PasswordResetView.as_view(
            form_class=RecuperarClaveForm,
            template_name="votaciones/recuperar_clave.html",
            email_template_name="votaciones/correos/recuperar_clave.txt",
            subject_template_name="votaciones/correos/recuperar_clave_asunto.txt",
            success_url=reverse_lazy("recuperar_clave_enviado"),
        ),
        name="recuperar_clave",
    ),
    path(
        "recuperar-clave/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="votaciones/recuperar_clave_enviado.html",
        ),
        name="recuperar_clave_enviado",
    ),
    path(
        "recuperar-clave/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=NuevaClaveForm,
            template_name="votaciones/recuperar_clave_confirmar.html",
            success_url=reverse_lazy("recuperar_clave_listo"),
        ),
        name="recuperar_clave_confirmar",
    ),
    path(
        "recuperar-clave/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="votaciones/recuperar_clave_listo.html",
        ),
        name="recuperar_clave_listo",
    ),
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