# apps/reconocimiento/serializers.py
from rest_framework import serializers
from .models import Evento

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = ["id", "nombre", "descripcion", "lugar", "fecha_hora", "is_active", "imagen", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]