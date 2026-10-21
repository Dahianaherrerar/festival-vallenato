
from django.utils import timezone
from rest_framework import serializers
from .models import Categoria, Votacion, Opcion, Voto


from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion", "activa"]


class VotacionSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True
    )

    class Meta:
        model = Votacion
        fields = [
            "id",
            "categoria",
            "categoria_nombre",
            "titulo",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "abierta",
        ]


class OpcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opcion
        fields = ["id", "votacion", "nombre", "descripcion"]


class VotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voto
        fields = ["id", "votacion", "opcion", "fecha_creacion"]
        read_only_fields = ["id", "fecha_creacion"]

    def validate(self, attrs):
        usuario = self.context["request"].user
        votacion = attrs["votacion"]
        opcion = attrs["opcion"]
        ahora = timezone.now()

        if not votacion.categoria.activa:
            raise serializers.ValidationError(
                "La categoría no está activa."
            )

        if not votacion.abierta:
            raise serializers.ValidationError(
                "La votación no está abierta."
            )

        if not (votacion.fecha_inicio <= ahora <= votacion.fecha_fin):
            raise serializers.ValidationError(
                "La votación está fuera de su periodo permitido."
            )

        if opcion.votacion_id != votacion.id:
            raise serializers.ValidationError(
                "La opción no pertenece a esta votación."
            )

        if Voto.objects.filter(
            usuario=usuario,
            votacion=votacion
        ).exists():
            raise serializers.ValidationError(
                "Ya has votado en esta votación."
            )

        return attrs

    def create(self, validated_data):
        return Voto.objects.create(
            usuario=self.context["request"].user,
            **validated_data
        )



