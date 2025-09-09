from rest_framework import serializers
from .models import Empresa
from accounts.models import User
from requisitos.models import TipoSello
from requisitos.serializers import TipoSelloSerializer

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
    
    # Campo para mostrar el objeto completo del tipo de sello (solo lectura)
    tipoSello = TipoSelloSerializer(read_only=True)
    # Campo para la escritura (escribir el ID del tipo de sello)
    tipoSello_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoSello.objects.all(),
        source='tipoSello',
        write_only=True,
        required=False,
        allow_null=True
    )

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
            "isAproved", # Nuevo campo
            "tipoSello", # Campo de lectura (objeto anidado)
            "tipoSello_id", # Campo de escritura (ID)
            "usuarios",
            "usuarios_relacionados",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tipoSello"]

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
            usuarios_actuales = instance.usuarios.all()
            usuarios_a_remover = [u for u in usuarios_actuales if u not in usuarios_nuevos]
            for user in usuarios_a_remover:
                user.empresa = None
                user.save()

            for user in usuarios_nuevos:
                if user.empresa != instance:
                    user.empresa = instance
                    user.save()
        
        return instance
