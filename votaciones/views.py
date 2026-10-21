
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Categoria, Votacion, Opcion
from .serializers import RegistroUsuarioSerializer
from .serializers import (
    CategoriaSerializer,
    VotacionSerializer,
    OpcionSerializer,
    VotoSerializer,
)


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.filter(activa=True)
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]


class VotacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Votacion.objects.filter(
        categoria__activa=True
    ).select_related("categoria")
    serializer_class = VotacionSerializer
    permission_classes = [AllowAny]


class OpcionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OpcionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Opcion.objects.filter(
            votacion__categoria__activa=True
        )

        votacion_id = self.request.query_params.get("votacion")

        if votacion_id:
            queryset = queryset.filter(votacion_id=votacion_id)

        return queryset


class RegistrarVotoView(generics.CreateAPIView):
    serializer_class = VotoSerializer
    permission_classes = [IsAuthenticated]



class RegistroUsuarioView(generics.CreateAPIView):
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [AllowAny]

