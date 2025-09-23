# apps/preparacion/serializers.py
from rest_framework import serializers
from .models import (
    Empresa,
    FaseEmpresa,
    Capacitacion,
    Asesoramiento,
    SolicitudAsesoramiento,
    PublicacionEmpresaComunidad,
)


# ================
# CAPACITACION
# ================
class CapacitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capacitacion
        fields = ["id", "nombre", "descripcion", "foto", "is_active", "created_at"]


# ================
# ASESORAMIENTO
# ================
class AsesoramientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asesoramiento
        fields = ["id", "nombre", "descripcion", "foto", "is_active", "created_at"]


# ================
# FASE EMPRESA
# ================
class FaseEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseEmpresa
        fields = ["id", "fase_numero", "gestion", "is_active", "created_at"]


# ================
# EMPRESA
# ================
class EmpresaSerializer(serializers.ModelSerializer):
    capacitaciones = CapacitacionSerializer(many=True, read_only=True)
    asesoramientos = AsesoramientoSerializer(many=True, read_only=True)
    fases_empresa = FaseEmpresaSerializer(many=True, read_only=True)

    class Meta:
        model = Empresa
        fields = [
            "id",
            "nombre",
            "matricula",
            "nit",
            "tipo",
            "direccion",
            "is_active",
            "isAproved",
            "tipoSello",
            "capacitaciones",
            "asesoramientos",
            "fases_empresa",
            "created_at",
            "updated_at",
        ]


# ================
# SOLICITUD DE ASESORAMIENTO
# ================
class SolicitudAsesoramientoSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)
    asesoramiento_nombre = serializers.CharField(source="asesoramiento.nombre", read_only=True)

    class Meta:
        model = SolicitudAsesoramiento
        fields = [
            "id",
            "empresa",
            "empresa_nombre",
            "asesoramiento",
            "asesoramiento_nombre",
            "nombreAsesoramiento",
            "fechaTentativaInicial",
            "fechaTentativaFinal",
            "fechaAprobada",
            "estado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "estado"]
        
        
class PublicacionEmpresaComunidadSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = PublicacionEmpresaComunidad
        fields = [
            "id",
            "empresa",
            "empresa_nombre",
            "titulo",
            "fotourl",
            "descripcion",
            "activo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "empresa_nombre"]