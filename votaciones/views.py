
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
        activa=True
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




@login_required
def votar(request, votacion_id):
    votacion = get_object_or_404(
        Votacion,
        pk=votacion_id,
        categoria__activa=True,
        abierta=True,
    )

    ahora = timezone.now()

    if not (votacion.fecha_inicio <= ahora <= votacion.fecha_fin):
        messages.error(
            request,
            "Esta votación no está dentro de su periodo habilitado.",
        )
        return redirect("votaciones")

    if not votacion.categoria.edicion_id:
        messages.error(
            request,
            "La categoría no tiene una edición asignada y no admite votos.",
        )
        return redirect("votaciones")

    if Voto.objects.filter(
        usuario=request.user,
        categoria=votacion.categoria,
        edicion_id=votacion.categoria.edicion_id,
    ).exists():
        messages.warning(
            request,
            "Ya registraste tu voto en esta categoría para esta edición.",
        )
        return redirect("votaciones")

    if request.method == "POST":
        form = VotoForm(request.POST, votacion=votacion)

        if form.is_valid():
            opcion = form.cleaned_data["opcion"]

            try:
                with transaction.atomic():
                    Voto.objects.create(
                        usuario=request.user,
                        edicion=votacion.categoria.edicion,
                        categoria=votacion.categoria,
                        votacion=votacion,
                        opcion=opcion,
                    )

                messages.success(
                    request,
                    "Tu voto se registró correctamente.",
                )
                return redirect("votaciones")

            except IntegrityError:
                messages.warning(
                    request,
                    "Ya registraste tu voto en esta categoría para esta edición.",
                )
                return redirect("votaciones")
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
