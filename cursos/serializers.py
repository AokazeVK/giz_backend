# apps/difusion/serializers.py
# (Asegúrate de importar el modelo 'Curso')

from rest_framework import serializers
from .models import Curso

class CursoSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            "id",
            "nombre",
            "descripcion",
            "visualizaciones",
            "foto",
            "foto_url",
            "link_url",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "visualizaciones", "foto_url", "created_at", "updated_at", "is_active"]

    def get_foto_url(self, obj):
        request = self.context.get("request")
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None