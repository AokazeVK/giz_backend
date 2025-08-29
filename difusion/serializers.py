from rest_framework import serializers
from .models import Ministerio, Encargado

class EncargadoSerializer(serializers.ModelSerializer):
    nombre_ministerio = serializers.CharField(source='ministerio.nombre', read_only=True)
    class Meta:
        model = Encargado
        fields = ["id", "ministerio", "nombre_ministerio", "nombre", "cargo", "correo", "telefono", "is_active"]


class MinisterioSerializer(serializers.ModelSerializer):
    encargados = EncargadoSerializer(many=True, read_only=True)

    class Meta:
        model = Ministerio
        fields = ["id", "nombre", "direccion", "is_active", "encargados"]
