"""Sección Administración: crear, editar, desactivar y eliminar desde la app.

Las cinco partes (ediciones, concursos, categorías, votaciones y
participantes) comparten las mismas vistas; lo que cambia de una a otra está
en el diccionario SECCIONES.
"""

from dataclasses import dataclass, field
from typing import Callable

from django.contrib import messages
from urllib.parse import urlencode

from django.db.models import ProtectedError
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from votaciones.models import Categoria, Concurso, Edicion, Opcion, Votacion, Voto

from .forms import (
    CategoriaForm,
    ConcursoForm,
    EdicionForm,
    ParticipanteForm,
    VotacionForm,
)
from .permisos import solo_administradores


def periodo(votacion):
    inicio = timezone.localtime(votacion.fecha_inicio).strftime("%d/%m/%Y %H:%M")
    fin = timezone.localtime(votacion.fecha_fin).strftime("%d/%m/%Y %H:%M")
    return f"{inicio} – {fin}"


@dataclass
class Seccion:
    modelo: type
    formulario: type
    singular: str  # «la edición»
    plural: str  # «Ediciones»
    icono: str
    campo_estado: str
    columnas: list  # [(título, función que recibe el objeto)]
    orden: list
    relacionados: list = field(default_factory=list)
    busqueda: str = "nombre"
    # Filtro por el «padre»: (parámetro GET, etiqueta, función que da las opciones)
    filtro: tuple | None = None
    textos_estado: tuple = ("Activo", "Inactivo", "Activar", "Desactivar")
    descripcion: str = ""
    nombre: Callable = str


SECCIONES = {
    "ediciones": Seccion(
        modelo=Edicion,
        formulario=EdicionForm,
        singular="la edición",
        plural="Ediciones",
        icono="calendar3",
        campo_estado="activa",
        columnas=[("Año", lambda o: o.anio), ("Nombre", lambda o: o.nombre)],
        orden=["-anio"],
        textos_estado=("Activa", "Inactiva", "Activar", "Desactivar"),
        descripcion="Cada año del Festival.",
        nombre=lambda o: f"{o.nombre} ({o.anio})",
    ),
    "concursos": Seccion(
        modelo=Concurso,
        formulario=ConcursoForm,
        singular="el concurso",
        plural="Concursos",
        icono="trophy",
        campo_estado="activo",
        columnas=[
            ("Concurso", lambda o: o.nombre),
            ("Edición", lambda o: o.edicion.anio),
        ],
        orden=["-edicion__anio", "nombre"],
        relacionados=["edicion"],
        filtro=("edicion", "Edición", lambda: Edicion.objects.order_by("-anio")),
        descripcion="Piquería, Acordeón, Canción inédita…",
        nombre=lambda o: f"{o.nombre} ({o.edicion.anio})",
    ),
    "categorias": Seccion(
        modelo=Categoria,
        formulario=CategoriaForm,
        singular="la categoría",
        plural="Categorías",
        icono="collection",
        campo_estado="activa",
        columnas=[
            ("Categoría", lambda o: o.nombre),
            ("Concurso", lambda o: o.concurso.nombre),
            ("Edición", lambda o: o.edicion.anio),
        ],
        orden=["-edicion__anio", "concurso__nombre", "nombre"],
        relacionados=["concurso", "edicion"],
        filtro=(
            "concurso",
            "Concurso",
            lambda: Concurso.objects.select_related("edicion").order_by("-edicion__anio", "nombre"),
        ),
        textos_estado=("Activa", "Inactiva", "Activar", "Desactivar"),
        descripcion="Infantil, Juvenil, Aficionado, Profesional…",
        nombre=lambda o: f"{o.concurso.nombre} · {o.nombre}",
    ),
    "votaciones": Seccion(
        modelo=Votacion,
        formulario=VotacionForm,
        singular="la votación",
        plural="Votaciones",
        icono="check2-square",
        campo_estado="abierta",
        columnas=[
            ("Votación", lambda o: o.titulo),
            ("Concurso · Categoría", lambda o: f"{o.categoria.concurso.nombre} · {o.categoria.nombre}"),
            ("Periodo", periodo),
        ],
        orden=["-fecha_inicio"],
        relacionados=["categoria__concurso", "categoria__edicion"],
        busqueda="titulo",
        filtro=(
            "categoria",
            "Categoría",
            lambda: Categoria.objects.select_related("concurso").order_by("concurso__nombre", "nombre"),
        ),
        textos_estado=("Abierta", "Cerrada", "Abrir", "Cerrar"),
        descripcion="Periodo en que se vota en una categoría.",
        nombre=lambda o: o.titulo,
    ),
    "participantes": Seccion(
        modelo=Opcion,
        formulario=ParticipanteForm,
        singular="el participante",
        plural="Participantes",
        icono="people",
        campo_estado="activo",
        columnas=[
            ("Participante", lambda o: o.nombre),
            ("Concurso · Categoría", lambda o: f"{o.votacion.categoria.concurso.nombre} · {o.votacion.categoria.nombre}"),
            ("Votación", lambda o: o.votacion.titulo),
        ],
        orden=["votacion__categoria__concurso__nombre", "votacion__categoria__nombre", "nombre"],
        relacionados=["votacion__categoria__concurso"],
        filtro=(
            "votacion",
            "Votación",
            lambda: Votacion.objects.select_related("categoria__concurso").order_by("-fecha_inicio"),
        ),
        descripcion="Las opciones por las que se vota.",
        nombre=lambda o: o.nombre,
    ),
}


def etiqueta_filtro(objeto):
    """Texto de cada opción del filtro, con su concurso para no confundirlas."""
    if isinstance(objeto, Categoria):
        return f"{objeto.concurso.nombre} · {objeto.nombre}"
    if isinstance(objeto, Votacion):
        return f"{objeto.categoria.concurso.nombre} · {objeto.categoria.nombre} · {objeto.titulo}"
    return str(objeto)


def obtener_seccion(clave):
    if clave not in SECCIONES:
        raise Http404("Sección no encontrada")
    return SECCIONES[clave]


def contexto_base(clave, seccion):
    return {"clave": clave, "seccion_panel": seccion, "secciones": SECCIONES}


@solo_administradores
def inicio(request):
    tarjetas = [
        {
            "clave": clave,
            "seccion": seccion,
            "total": seccion.modelo.objects.count(),
            "activos": seccion.modelo.objects.filter(**{seccion.campo_estado: True}).count(),
        }
        for clave, seccion in SECCIONES.items()
    ]
    return render(request, "panel/inicio.html", {"tarjetas": tarjetas, "secciones": SECCIONES})


@solo_administradores
def lista(request, clave):
    seccion = obtener_seccion(clave)
    objetos = seccion.modelo.objects.select_related(*seccion.relacionados).order_by(*seccion.orden)

    texto = request.GET.get("q", "").strip()
    if texto:
        objetos = objetos.filter(**{f"{seccion.busqueda}__icontains": texto})

    filtro_actual = ""
    opciones_filtro = []
    if seccion.filtro:
        parametro, _, opciones = seccion.filtro
        opciones_filtro = [(str(o.pk), etiqueta_filtro(o)) for o in opciones()]
        filtro_actual = request.GET.get(parametro, "")
        if filtro_actual.isdigit():
            objetos = objetos.filter(**{f"{parametro}_id": filtro_actual})

    filas = [
        {
            "objeto": objeto,
            "celdas": [(titulo, funcion(objeto)) for titulo, funcion in seccion.columnas],
            "activo": getattr(objeto, seccion.campo_estado),
        }
        for objeto in objetos
    ]

    return render(
        request,
        "panel/lista.html",
        {
            **contexto_base(clave, seccion),
            "filas": filas,
            "texto": texto,
            "opciones_filtro": opciones_filtro,
            "filtro_actual": filtro_actual,
        },
    )


@solo_administradores
def crear(request, clave):
    seccion = obtener_seccion(clave)

    if request.method == "POST":
        form = seccion.formulario(request.POST)
        if form.is_valid():
            objeto = form.save()
            messages.success(request, f"Se creó {seccion.singular} «{seccion.nombre(objeto)}».")
            return redirect("panel_lista", clave=clave)
    else:
        # Si se viene de una lista filtrada (ej. un concurso), se preselecciona.
        inicial = {}
        if seccion.filtro and request.GET.get(seccion.filtro[0], "").isdigit():
            inicial[seccion.filtro[0]] = request.GET[seccion.filtro[0]]
        form = seccion.formulario(initial=inicial)

    return render(
        request,
        "panel/formulario.html",
        {**contexto_base(clave, seccion), "form": form, "titulo": f"Nuevo registro · {seccion.plural}"},
    )


@solo_administradores
def editar(request, clave, pk):
    seccion = obtener_seccion(clave)
    objeto = get_object_or_404(seccion.modelo, pk=pk)

    if request.method == "POST":
        form = seccion.formulario(request.POST, instance=objeto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Se guardaron los cambios de {seccion.singular} «{seccion.nombre(objeto)}».")
            return redirect("panel_lista", clave=clave)
    else:
        form = seccion.formulario(instance=objeto)

    return render(
        request,
        "panel/formulario.html",
        {
            **contexto_base(clave, seccion),
            "form": form,
            "objeto": objeto,
            "titulo": f"Editar {seccion.singular} «{seccion.nombre(objeto)}»",
        },
    )


@require_POST
@solo_administradores
def cambiar_estado(request, clave, pk):
    seccion = obtener_seccion(clave)
    objeto = get_object_or_404(seccion.modelo, pk=pk)

    nuevo = not getattr(objeto, seccion.campo_estado)
    setattr(objeto, seccion.campo_estado, nuevo)
    objeto.save(update_fields=[seccion.campo_estado])

    estado = seccion.textos_estado[0 if nuevo else 1].lower()
    messages.success(request, f"{seccion.singular.capitalize()} «{seccion.nombre(objeto)}» quedó {estado}.")
    return volver_a_la_lista(request, clave)


def volver_a_la_lista(request, clave):
    """Regresa a la lista conservando la búsqueda y el filtro que tenía."""
    url = reverse("panel_lista", args=[clave])
    filtros = QueryDict(request.POST.get("filtros", ""))
    conservar = {k: v for k, v in filtros.items() if k in {"q", "edicion", "concurso", "categoria", "votacion"}}
    return redirect(f"{url}?{urlencode(conservar)}" if conservar else url)


NOMBRES_DEPENDENCIAS = {
    Concurso: "concurso(s)",
    Categoria: "categoría(s)",
    Votacion: "votación(es)",
    Opcion: "participante(s)",
    Voto: "voto(s)",
}


def describir_dependencias(error):
    """«3 voto(s) y 1 categoría(s)» a partir de un ProtectedError."""
    conteo = {}
    for objeto in error.protected_objects:
        nombre = NOMBRES_DEPENDENCIAS.get(type(objeto), "registro(s)")
        conteo[nombre] = conteo.get(nombre, 0) + 1
    return " y ".join(f"{total} {nombre}" for nombre, total in conteo.items())


@solo_administradores
def eliminar(request, clave, pk):
    seccion = obtener_seccion(clave)
    objeto = get_object_or_404(seccion.modelo, pk=pk)
    nombre = seccion.nombre(objeto)

    if request.method == "POST":
        try:
            objeto.delete()
        except ProtectedError as error:
            messages.error(
                request,
                f"No se puede eliminar {seccion.singular} «{nombre}» porque tiene registros "
                f"asociados ({describir_dependencias(error)}). Puedes desactivarlo en su lugar.",
            )
        else:
            messages.success(request, f"Se eliminó {seccion.singular} «{nombre}».")
        return volver_a_la_lista(request, clave)

    return render(
        request,
        "panel/eliminar.html",
        {**contexto_base(clave, seccion), "objeto": objeto, "nombre": nombre},
    )
