
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegistroForm, VotoForm
from .models import Categoria, Votacion, Voto
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone



def inicio(request):
    return render(request, "votaciones/inicio.html")


def categorias(request):
    lista_categorias = Categoria.objects.filter(
        activa=True,
        edicion__activa=True,
    ).select_related("edicion")

    return render(
        request,
        "votaciones/categorias.html",
        {"categorias": lista_categorias},
    )


def votaciones(request):
    lista_votaciones = (
        Votacion.objects.filter(
            abierta=True,
            categoria__activa=True,
            categoria__edicion__activa=True,
        )
        .select_related("categoria", "categoria__edicion")
        .prefetch_related("opciones")
        .order_by("fecha_inicio")
    )

    return render(
        request,
        "votaciones/votaciones.html",
        {"votaciones": lista_votaciones},
    )


def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect("inicio")
    else:
        form = RegistroForm()

    return render(
        request,
        "votaciones/registro.html",
        {"form": form},
    )


@login_required
def cerrar_sesion(request):
    if request.method == "POST":
        logout(request)
        return redirect("inicio")

    return redirect("inicio")




MENSAJE_VOTO_DUPLICADO = (
    "Ya registraste tu voto en esta categoría para esta edición."
)


def motivo_votacion_no_habilitada(votacion, ahora=None):
    """Devuelve por qué no se puede votar, o None si la votación está habilitada.

    Se revisa en el servidor, en este orden: edición activa, categoría
    activa, votación abierta y periodo de fechas (CP-05).
    """
    ahora = ahora or timezone.now()
    categoria = votacion.categoria
    edicion = categoria.edicion

    if not edicion.activa:
        return (
            f"La edición {edicion.anio} no está activa; "
            "no se pueden registrar votos."
        )

    if not categoria.activa:
        return (
            f"La categoría «{categoria.nombre}» no está habilitada "
            "para votar."
        )

    if not votacion.abierta:
        return "Esta votación está cerrada y no admite votos."

    if not (votacion.fecha_inicio <= ahora <= votacion.fecha_fin):
        return "Esta votación no está dentro de su periodo habilitado."

    return None


@login_required
def votar(request, votacion_id):
    """Flujo del voto: seleccionar opción → confirmar → validar → guardar.

    1. GET: muestra las opciones de la votación.
    2. POST con la opción elegida: valida y muestra la pantalla de
       confirmación, sin guardar nada todavía.
    3. POST con confirmar=si: vuelve a validar todo en el servidor y
       guarda el voto dentro de una transacción.
    """
    votacion = get_object_or_404(
        Votacion.objects.select_related("categoria__edicion"),
        pk=votacion_id,
    )
    categoria = votacion.categoria
    edicion = categoria.edicion

    # CP-05: se rechaza de forma explícita, con mensaje, cualquier
    # edición, categoría o votación que no esté habilitada.
    motivo = motivo_votacion_no_habilitada(votacion)
    if motivo:
        messages.error(request, motivo)
        return redirect("votaciones")

    # Regla central: un voto por usuario, categoría y edición.
    if Voto.objects.filter(
        usuario=request.user,
        categoria=categoria,
        edicion=edicion,
    ).exists():
        messages.warning(request, MENSAJE_VOTO_DUPLICADO)
        return redirect("votaciones")

    if request.method == "POST":
        form = VotoForm(request.POST, votacion=votacion)

        if form.is_valid():
            opcion = form.cleaned_data["opcion"]

            # Paso de confirmación: la primera vez solo se muestra el
            # resumen; el voto se guarda cuando el usuario confirma.
            if request.POST.get("confirmar") != "si":
                return render(
                    request,
                    "votaciones/confirmar_voto.html",
                    {"votacion": votacion, "opcion": opcion},
                )

            try:
                with transaction.atomic():
                    Voto.objects.create(
                        usuario=request.user,
                        edicion=edicion,
                        categoria=categoria,
                        votacion=votacion,
                        opcion=opcion,
                    )
            except IntegrityError:
                # Dos solicitudes casi simultáneas: la restricción única de
                # MySQL deja pasar solo una (CP-09).
                messages.warning(request, MENSAJE_VOTO_DUPLICADO)
                return redirect("votaciones")

            messages.success(
                request,
                f"Tu voto por «{opcion.nombre}» se registró correctamente.",
            )
            return redirect("votaciones")

        # CP-06: opción inválida o de otra categoría. No se guarda nada y
        # se vuelve a mostrar el formulario con el error.
        messages.error(request, "No se registró el voto. Revisa tu selección.")
    else:
        form = VotoForm(votacion=votacion)

    return render(
        request,
        "votaciones/votar.html",
        {"votacion": votacion, "form": form},
    )


def resultados(request, votacion_id):
    votacion = get_object_or_404(
        Votacion,
        pk=votacion_id,
    )

    if timezone.now() <= votacion.fecha_fin:
        messages.info(
            request,
            "Los resultados estarán disponibles cuando termine la votación.",
        )
        return redirect("votaciones")

    opciones = (
        votacion.opciones
        .annotate(total_votos=Count("votos"))
        .order_by("-total_votos", "nombre")
    )

    return render(
        request,
        "votaciones/resultados.html",
        {
            "votacion": votacion,
            "opciones": opciones,
        },
    )
