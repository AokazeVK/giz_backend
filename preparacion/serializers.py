from rest_framework import serializers
from .models import Empresa
from accounts.models import User

class EmpresaSerializer(serializers.ModelSerializer):
    usuarios = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    # Este campo es para mostrar los usuarios, pero ahora usa el related_name
    usuarios_relacionados = serializers.StringRelatedField(many=True, read_only=True, source='usuarios')
    
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
            "usuarios", # Campo para la escritura
            "usuarios_relacionados", # Campo para la lectura
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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
        
        # Primero, actualiza los campos básicos de la empresa
        instance = super().update(instance, validated_data)

        if usuarios_nuevos is not None:
            # Desasocia a los usuarios que ya no pertenecen a la empresa
            usuarios_actuales = instance.usuarios.all()
            usuarios_a_remover = [u for u in usuarios_actuales if u not in usuarios_nuevos]
            for user in usuarios_a_remover:
                user.empresa = None
                user.save()

            # Asocia a los nuevos usuarios a la empresa
            for user in usuarios_nuevos:
                if user.empresa != instance:
                    user.empresa = instance
                    user.save()
        
        return instance