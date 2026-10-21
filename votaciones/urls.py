
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import RegistroUsuarioView
from .views import (
    CategoriaViewSet,
    VotacionViewSet,
    OpcionViewSet,
    RegistrarVotoView,
)

router = DefaultRouter()
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("votaciones", VotacionViewSet, basename="votacion")
router.register("opciones", OpcionViewSet, basename="opcion")

urlpatterns = [
    path("", include(router.urls)),
    path("votos/", RegistrarVotoView.as_view(), name="registrar-voto"),
    path(
    "registro/",
    RegistroUsuarioView.as_view(),
    name="registro-usuario"
),
]
