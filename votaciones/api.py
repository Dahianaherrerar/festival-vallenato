from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Categoria, Opcion, Votacion


@require_GET
def api_categorias(request):
    """Publica categorías habilitadas y sus votaciones y opciones activas."""
    votaciones_activas = (
        Votacion.objects.order_by("fecha_inicio", "pk")
        .prefetch_related(
            Prefetch(
                "opciones",
                queryset=Opcion.objects.filter(activo=True).order_by("nombre", "pk"),
            )
        )
    )
    categorias_activas = (
        Categoria.objects.filter(
            activa=True,
            concurso__activo=True,
            edicion__activa=True,
        )
        .select_related("edicion", "concurso")
        .prefetch_related(Prefetch("votaciones", queryset=votaciones_activas))
        .order_by("edicion__anio", "concurso__nombre", "nombre", "pk")
    )

    categorias = []
    for categoria in categorias_activas:
        categorias.append(
            {
                "id": categoria.pk,
                "nombre": categoria.nombre,
                "descripcion": categoria.descripcion,
                "edicion": {
                    "id": categoria.edicion_id,
                    "nombre": categoria.edicion.nombre,
                    "anio": categoria.edicion.anio,
                },
                "concurso": {
                    "id": categoria.concurso_id,
                    "nombre": categoria.concurso.nombre,
                },
                "votaciones": [
                    {
                        "id": votacion.pk,
                        "titulo": votacion.titulo,
                        "descripcion": votacion.descripcion,
                        "fecha_inicio": votacion.fecha_inicio.isoformat(),
                        "fecha_fin": votacion.fecha_fin.isoformat(),
                        "abierta": votacion.abierta,
                        "opciones": [
                            {
                                "id": opcion.pk,
                                "nombre": opcion.nombre,
                                "descripcion": opcion.descripcion,
                            }
                            for opcion in votacion.opciones.all()
                        ],
                    }
                    for votacion in categoria.votaciones.all()
                ],
            }
        )

    return JsonResponse(
        {"categorias": categorias},
        json_dumps_params={"ensure_ascii": False},
    )
