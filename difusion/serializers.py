from rest_framework import serializers
from .models import Ministerio, Encargado, Convocatoria, FechaConvocatoria, ArchivoFechaConvocatoria


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
class ArchivoFechaConvocatoriaSerializer(serializers.ModelSerializer):
    url_file = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ArchivoFechaConvocatoria
        fields = ["id", "fecha_convocatoria", "nombre", "file", "url_file", "created_at"]
        read_only_fields = ["id", "url_file", "created_at"]

    def get_url_file(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        if obj.file:
            return obj.file.url
        return None


class FechaConvocatoriaSerializer(serializers.ModelSerializer):
    archivos = ArchivoFechaConvocatoriaSerializer(many=True, read_only=True)

    class Meta:
        model = FechaConvocatoria
        fields = ["id", "convocatoria", "fecha_inicio", "fecha_fin", "gestion", "is_active", "archivos", "created_at"]
        read_only_fields = ["id", "gestion", "archivos", "created_at"]

    def validate(self, data):
        # fecha_fin may be in data or missing (when partial update)
        fecha_inicio = data.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fecha_fin = data.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return data


class ConvocatoriaSerializer(serializers.ModelSerializer):
    fechas = FechaConvocatoriaSerializer(many=True, read_only=True)

    class Meta:
        model = Convocatoria
        fields = ["id", "nombre", "descripcion", "is_active", "fechas", "created_at", "updated_at"]
        read_only_fields = ["id", "fechas", "created_at", "updated_at"]


