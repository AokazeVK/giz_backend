# apps/preparacion/serializers.py
from rest_framework import serializers
from requisitos.models import TipoSello
from accounts.models import User
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
    # Campo para la escritura de usuarios
    usuarios = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    # Campo para mostrar los nombres de los usuarios en la respuesta
    usuarios_relacionados = serializers.StringRelatedField(many=True, read_only=True, source='usuarios')
    
    # Campo para mostrar el objeto completo del tipo de sello (solo lectura) con lazy import
    tipoSello = serializers.SerializerMethodField()
    # Campo para la escritura (escribir el ID del tipo de sello)
    tipoSello_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoSello.objects.all(),
        source='tipoSello',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # 👇 Campo para mostrar la lista de fases de la empresa (solo lectura)
    fases_empresa = FaseEmpresaSerializer(many=True, read_only=True)
    
    # Agregados los campos de capacitaciones y asesoramientos
    capacitaciones = CapacitacionSerializer(many=True, read_only=True)
    asesoramientos = AsesoramientoSerializer(many=True, read_only=True)

    class Meta:
        model = Empresa
        fields = [
            "id",
            "nombre",
            "rut",
            "tipo",
            "direccion",
            "is_active",
            "isAproved",
            "tipoSello",
            "tipoSello_id",
            "usuarios",
            "usuarios_relacionados",
            "fases_empresa",
            "capacitaciones",
            "asesoramientos",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tipoSello"]

    def get_tipoSello(self, obj):
        from requisitos.serializers import TipoSelloSerializer  # 👈 lazy import
        if obj.tipoSello:
            return TipoSelloSerializer(obj.tipoSello, context=self.context).data
        return None

    def create(self, validated_data):
        usuarios = validated_data.pop("usuarios", [])
        empresa = Empresa.objects.create(**validated_data)
        if usuarios:
            for user in usuarios:
                user.empresa = empresa
                user.save()
        return empresa

    def update(self, instance, validated_data):
        usuarios_nuevos = validated_data.pop("usuarios", None)
        
        instance = super().update(instance, validated_data)

        if usuarios_nuevos is not None:
            # Primero, desvincula a los usuarios que ya no están
            usuarios_a_remover = instance.usuarios.exclude(id__in=[u.id for u in usuarios_nuevos])
            for user in usuarios_a_remover:
                user.empresa = None
                user.save()

            # Luego, vincula a los nuevos usuarios
            for user in usuarios_nuevos:
                if user.empresa != instance:
                    user.empresa = instance
                    user.save()

        return instance

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