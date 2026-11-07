"""Sección Usuarios: ver quién se registró y ayudarle a recuperar el acceso.

Nadie, ni siquiera un administrador, puede ver las contraseñas: Django solo
guarda una versión cifrada. Por eso, en vez de mostrarlas o cambiarlas a mano,
se le envía al usuario el mismo enlace de «¿Olvidaste tu contraseña?».
"""

import logging
import smtplib
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count, Q
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from .permisos import solo_administradores

Usuario = get_user_model()
registro = logging.getLogger(__name__)

FILTROS_TIPO = {
    "administradores": Q(is_staff=True),
    "votantes": Q(is_staff=False),
}
FILTROS_ESTADO = {
    "activos": Q(is_active=True),
    "inactivos": Q(is_active=False),
}
PARAMETROS_LISTA = {"q", "tipo", "estado"}


class EnlaceParaUsuario(PasswordResetForm):
    """Envía el enlace de recuperación a un usuario elegido por el administrador.

    A diferencia del formulario público, no busca por correo: usa el usuario
    de la fila donde se hizo clic. Además, si el correo falla, avisa con un
    error en lugar de ignorarlo, para que el administrador lo sepa.
    """

    def __init__(self, usuario):
        super().__init__({"email": usuario.email})
        self.usuario = usuario

    def get_users(self, email):
        return [self.usuario]

    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        asunto = "".join(render_to_string(subject_template_name, context).splitlines())
        cuerpo = render_to_string(email_template_name, context)
        EmailMultiAlternatives(asunto, cuerpo, from_email, [to_email]).send()


def correo_por_terminal():
    return settings.EMAIL_BACKEND.endswith("console.EmailBackend")


@solo_administradores
def lista(request):
    usuarios = Usuario.objects.annotate(total_votos=Count("voto")).order_by("-date_joined")

    texto = request.GET.get("q", "").strip()
    if texto:
        usuarios = usuarios.filter(
            Q(username__icontains=texto)
            | Q(email__icontains=texto)
            | Q(first_name__icontains=texto)
            | Q(last_name__icontains=texto)
        )

    tipo = request.GET.get("tipo", "")
    if tipo in FILTROS_TIPO:
        usuarios = usuarios.filter(FILTROS_TIPO[tipo])

    estado = request.GET.get("estado", "")
    if estado in FILTROS_ESTADO:
        usuarios = usuarios.filter(FILTROS_ESTADO[estado])

    resumen = {
        "total": Usuario.objects.count(),
        "administradores": Usuario.objects.filter(is_staff=True).count(),
        "votantes": Usuario.objects.filter(is_staff=False).count(),
        "inactivos": Usuario.objects.filter(is_active=False).count(),
    }

    return render(
        request,
        "panel/usuarios.html",
        {
            "usuarios": usuarios,
            "resumen": resumen,
            "texto": texto,
            "tipo": tipo,
            "estado": estado,
            "correo_por_terminal": correo_por_terminal(),
        },
    )


def volver_a_usuarios(request):
    """Regresa a la lista conservando la búsqueda y los filtros que tenía."""
    url = reverse("usuarios_lista")
    filtros = QueryDict(request.POST.get("filtros", ""))
    conservar = {k: v for k, v in filtros.items() if k in PARAMETROS_LISTA}
    return redirect(f"{url}?{urlencode(conservar)}" if conservar else url)


@require_POST
@solo_administradores
def enviar_enlace(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    nombre = usuario.get_username()

    if not usuario.email:
        messages.error(request, f"«{nombre}» no tiene un correo registrado; no se le puede enviar el enlace.")
        return volver_a_usuarios(request)
    if not usuario.is_active:
        messages.error(request, f"La cuenta de «{nombre}» está desactivada. Actívala antes de enviar el enlace.")
        return volver_a_usuarios(request)

    formulario = EnlaceParaUsuario(usuario)
    if not formulario.is_valid():
        messages.error(request, f"El correo de «{nombre}» ({usuario.email}) no es válido.")
        return volver_a_usuarios(request)

    try:
        formulario.save(
            request=request,
            use_https=request.is_secure(),
            subject_template_name="votaciones/correos/recuperar_clave_asunto.txt",
            email_template_name="votaciones/correos/recuperar_clave.txt",
            extra_email_context={"desde_administracion": True},
        )
    except (smtplib.SMTPException, OSError):
        registro.exception("No se pudo enviar el enlace de recuperación al usuario %s", usuario.pk)
        messages.error(
            request,
            "No se pudo enviar el correo. Revisa EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en el archivo .env "
            "y la conexión a internet.",
        )
    else:
        donde = " (aparece en la terminal donde corre el servidor)" if correo_por_terminal() else ""
        messages.success(
            request,
            f"Se envió a «{nombre}» ({usuario.email}) un enlace para crear una nueva contraseña{donde}. "
            "El enlace vence en 1 hora.",
        )
    return volver_a_usuarios(request)


@require_POST
@solo_administradores
def cambiar_estado(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    nombre = usuario.get_username()

    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
        return volver_a_usuarios(request)
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, f"Solo un superusuario puede cambiar el estado de «{nombre}».")
        return volver_a_usuarios(request)

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=["is_active"])

    if usuario.is_active:
        messages.success(request, f"La cuenta de «{nombre}» quedó activa: ya puede iniciar sesión.")
    else:
        messages.success(
            request,
            f"La cuenta de «{nombre}» quedó desactivada: no podrá iniciar sesión. Sus votos se conservan.",
        )
    return volver_a_usuarios(request)
