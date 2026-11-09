"""Sección Informes: tablero de resultados y descarga del informe de auditoría.

El tablero agrupa los votos así: Concurso → Categoría → Votación → Participante.
El informe CSV trae el mismo resumen y, debajo, el detalle de cada voto
(fecha, usuario y participante) para poder auditar el conteo.
"""

import csv
from itertools import groupby

from django.db.models import Count, Max, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify

from votaciones.models import Concurso, Edicion, Opcion, Votacion, Voto

from .permisos import solo_administradores


def elegir_filtros(request):
    """Edición y concurso pedidos en la URL; por defecto, la edición activa."""
    ediciones = Edicion.objects.order_by("-anio")

    valor = request.GET.get("edicion", "")
    if valor.isdigit():
        edicion = get_object_or_404(Edicion, pk=valor)
    else:
        edicion = ediciones.filter(activa=True).first() or ediciones.first()

    concurso = None
    valor = request.GET.get("concurso", "")
    if edicion and valor.isdigit():
        concurso = Concurso.objects.filter(pk=valor, edicion=edicion).first()

    return ediciones, edicion, concurso


def votos_filtrados(edicion, concurso):
    votos = Voto.objects.filter(votacion__categoria__edicion=edicion)
    if concurso:
        votos = votos.filter(votacion__categoria__concurso=concurso)
    return votos


def porcentaje(parte, total):
    return round(parte * 100 / total, 1) if total else 0.0


def resultados_por_concurso(edicion, concurso=None):
    """Lista de concursos, cada uno con sus categorías, votaciones y participantes."""
    votaciones = (
        Votacion.objects.filter(categoria__edicion=edicion)
        .select_related("categoria__concurso")
        .annotate(total_votos=Count("votos"))
        .prefetch_related(
            Prefetch(
                "opciones",
                queryset=Opcion.objects.annotate(total_votos=Count("votos")).order_by("-total_votos", "nombre"),
            )
        )
        .order_by("categoria__concurso__nombre", "categoria__concurso_id", "categoria__nombre", "categoria_id", "fecha_inicio")
    )
    if concurso:
        votaciones = votaciones.filter(categoria__concurso=concurso)

    ahora = timezone.now()
    concursos = []
    for concurso_actual, del_concurso in groupby(votaciones, key=lambda v: v.categoria.concurso):
        categorias = []
        for categoria, de_la_categoria in groupby(del_concurso, key=lambda v: v.categoria):
            lista_votaciones = [armar_votacion(votacion, ahora) for votacion in de_la_categoria]
            categorias.append(
                {
                    "categoria": categoria,
                    "votaciones": lista_votaciones,
                    "total": sum(v["total"] for v in lista_votaciones),
                }
            )
        concursos.append(
            {
                "concurso": concurso_actual,
                "categorias": categorias,
                "total": sum(c["total"] for c in categorias),
            }
        )

    total_general = sum(c["total"] for c in concursos)
    for item in concursos:
        item["porcentaje"] = porcentaje(item["total"], total_general)
    return concursos


def armar_votacion(votacion, ahora):
    total = votacion.total_votos
    opciones = list(votacion.opciones.all())

    maximo = max((o.total_votos for o in opciones), default=0)
    lideres = [o for o in opciones if maximo and o.total_votos == maximo]

    if not votacion.abierta:
        estado = "Finalizada"
    elif ahora < votacion.fecha_inicio:
        estado = "Programada"
    elif ahora <= votacion.fecha_fin:
        estado = "En curso"
    else:
        estado = "Pendiente de cierre"

    return {
        "votacion": votacion,
        "total": total,
        "estado": estado,
        "en_curso": estado == "En curso",
        "empate": len(lideres) > 1,
        "opciones": [
            {
                "opcion": opcion,
                "votos": opcion.total_votos,
                "porcentaje": porcentaje(opcion.total_votos, total),
                "lider": opcion in lideres,
            }
            for opcion in opciones
        ],
    }


def resultado_texto(votacion, fila):
    if not fila["lider"]:
        return ""
    if votacion["empate"]:
        return "Empate"
    return "Va ganando" if votacion["en_curso"] else "Ganador"


@solo_administradores
def tablero(request):
    ediciones, edicion, concurso = elegir_filtros(request)
    contexto = {"ediciones": ediciones, "edicion": edicion, "concurso_elegido": concurso}

    if edicion:
        votos = votos_filtrados(edicion, concurso)
        resumen = votos.aggregate(total=Count("id"), votantes=Count("usuario", distinct=True), ultimo=Max("fecha_creacion"))
        concursos = resultados_por_concurso(edicion, concurso)
        for item in concursos:
            for categoria in item["categorias"]:
                for votacion in categoria["votaciones"]:
                    for fila in votacion["opciones"]:
                        fila["resultado"] = resultado_texto(votacion, fila)
        contexto.update(
            {
                "concursos_edicion": edicion.concursos.order_by("nombre"),
                "resumen": resumen,
                "concursos": concursos,
                "total_votaciones": sum(len(c["votaciones"]) for item in concursos for c in item["categorias"]),
            }
        )

    return render(request, "panel/informes.html", contexto)


def celda(valor):
    """Evita que Excel interprete como fórmula un texto que empieza con = + - @."""
    texto = str(valor)
    if texto[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + texto
    return texto


def numero(valor):
    """Porcentaje con coma decimal, como lo espera Excel en español."""
    return f"{valor:.1f}".replace(".", ",")


@solo_administradores
def descargar(request):
    _, edicion, concurso = elegir_filtros(request)
    if not edicion:
        return HttpResponse("No hay ediciones registradas.", status=404, content_type="text/plain; charset=utf-8")

    ahora = timezone.localtime()
    nombre = f"informe-votaciones-{edicion.anio}"
    if concurso:
        nombre += f"-{slugify(concurso.nombre)}"
    nombre += f"-{ahora:%Y%m%d-%H%M}.csv"

    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    respuesta.write("﻿")  # Marca para que Excel lea bien las tildes y la ñ.
    escritor = csv.writer(respuesta, delimiter=";")

    votos = votos_filtrados(edicion, concurso)
    resumen = votos.aggregate(total=Count("id"), votantes=Count("usuario", distinct=True))

    escritor.writerow(["Informe de auditoría de votaciones · Festival de la Leyenda Vallenata"])
    escritor.writerow(["Edición", celda(f"{edicion.nombre} ({edicion.anio})")])
    escritor.writerow(["Concurso", celda(concurso.nombre) if concurso else "Todos"])
    escritor.writerow(["Generado el", f"{ahora:%d/%m/%Y %H:%M}"])
    escritor.writerow(["Generado por", celda(request.user.get_username())])
    escritor.writerow(["Total de votos", resumen["total"]])
    escritor.writerow(["Votantes distintos", resumen["votantes"]])
    escritor.writerow([])

    escritor.writerow(["RESUMEN POR PARTICIPANTE"])
    escritor.writerow(["Concurso", "Categoría", "Votación", "Estado", "Participante", "Votos", "Porcentaje (%)", "Resultado"])
    for item in resultados_por_concurso(edicion, concurso):
        for categoria in item["categorias"]:
            for votacion in categoria["votaciones"]:
                estado = votacion["estado"]
                for fila in votacion["opciones"]:
                    escritor.writerow(
                        [
                            celda(item["concurso"].nombre),
                            celda(categoria["categoria"].nombre),
                            celda(votacion["votacion"].titulo),
                            estado,
                            celda(fila["opcion"].nombre),
                            fila["votos"],
                            numero(fila["porcentaje"]),
                            resultado_texto(votacion, fila),
                        ]
                    )
    escritor.writerow([])

    escritor.writerow(["DETALLE DE VOTOS"])
    escritor.writerow(["N.º de voto", "Fecha y hora", "Usuario", "Concurso", "Categoría", "Votación", "Participante"])
    detalle = votos.select_related("usuario", "votacion__categoria__concurso", "opcion").order_by("fecha_creacion", "pk")
    for voto in detalle:
        escritor.writerow(
            [
                voto.pk,
                f"{timezone.localtime(voto.fecha_creacion):%d/%m/%Y %H:%M:%S}",
                celda(voto.usuario.get_username()),
                celda(voto.votacion.categoria.concurso.nombre),
                celda(voto.votacion.categoria.nombre),
                celda(voto.votacion.titulo),
                celda(voto.opcion.nombre),
            ]
        )

    return respuesta
