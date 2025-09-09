from rest_framework import serializers
from .models import Evento

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        # Se actualiza la lista de campos para incluir 'fecha' y 'hora'
        fields = ["id", "nombre", "descripcion", "lugar", "fecha", "hora", "is_active", "imagen", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
