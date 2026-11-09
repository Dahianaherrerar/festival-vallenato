
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegistroForm, VotoForm
from .models import Categoria, Opcion, Votacion, Voto
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.utils import timezone



def inicio(request):
    return render(request, "votaciones/inicio.html")


def categorias(request):
    lista_categorias = (
        Categoria.objects.filter(
            activa=True,
            concurso__activo=True,
            edicion__activa=True,
        )
        .select_related("concurso", "edicion")
        .order_by("concurso__nombre", "concurso_id", "nombre")
    )

    return render(
        request,
        "votaciones/categorias.html",
        {"categorias": lista_categorias},
    )


@login_required
def participacion(request):
    votos = (
        Voto.objects.filter(usuario=request.user)
        .select_related(
            "edicion",
            "categoria__concurso",
            "votacion",
            "opcion",
        )
        .order_by("-fecha_creacion")
    )
    return render(request, "votaciones/participacion.html", {"votos": votos})


def votaciones(request):
    # Solo se listan las votaciones en las que hoy se puede votar:
    # abiertas, de concurso, categoría y edición activos, y dentro de sus fechas.
    ahora = timezone.now()
    lista_votaciones = (
        Votacion.objects.filter(
            abierta=True,
            categoria__activa=True,
            categoria__concurso__activo=True,
            categoria__edicion__activa=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
        )
        .select_related("categoria__concurso", "categoria__edicion")
        .prefetch_related(
            Prefetch("opciones", queryset=Opcion.objects.filter(activo=True))
        )
        .order_by("fecha_inicio")
    )

    if request.user.is_authenticated:
        lista_votaciones = lista_votaciones.annotate(
            ya_voto=Exists(
                Voto.objects.filter(
                    usuario=request.user,
                    categoria_id=OuterRef("categoria_id"),
                    edicion_id=OuterRef("categoria__edicion_id"),
                )
            )
        )

    # Flujo Concurso → Categoría: desde «Concursos» se llega con
    # ?categoria=<id> y solo se muestran las votaciones de esa categoría.
    categoria = None
    categoria_id = request.GET.get("categoria", "")
    if categoria_id.isdigit():
        categoria = (
            Categoria.objects.select_related("concurso")
            .filter(pk=categoria_id)
            .first()
        )
        lista_votaciones = lista_votaciones.filter(categoria_id=categoria_id)

    return render(
        request,
        "votaciones/votaciones.html",
        {"votaciones": lista_votaciones, "categoria": categoria},
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

    Se revisa en el servidor, en este orden: edición activa, concurso
    activo, categoría activa, votación abierta y periodo de fechas (CP-05).
    """
    ahora = ahora or timezone.now()
    categoria = votacion.categoria
    concurso = categoria.concurso
    edicion = categoria.edicion

    if not edicion.activa:
        return (
            f"La edición {edicion.anio} no está activa; "
            "no se pueden registrar votos."
        )

    if not concurso.activo:
        return (
            f"El concurso «{concurso.nombre}» no está habilitado "
            "para votar."
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
        Votacion.objects.select_related("categoria__concurso", "categoria__edicion"),
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

    if timezone.now() <= votacion.fecha_fin or votacion.abierta:
        messages.info(
            request,
            "Los resultados estarán disponibles cuando termine el periodo y la administración cierre la votación.",
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