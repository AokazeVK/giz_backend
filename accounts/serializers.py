from rest_framework import serializers
from .models import User, Role

# Serializer para el modelo de Rol
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

# Serializer para el modelo de Usuario
class UserSerializer(serializers.ModelSerializer):
    # Esto es para que DRF incluya el nombre del rol en el JSON
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    # Campo 'confirm_password' para la validación
    confirm_password = serializers.CharField(write_only=True, required=False)

    # Agregamos el campo is_active para que sea visible, pero no editable en la API
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        # Agregamos 'is_active' a la lista de campos
        fields = ['id', 'username', 'email', 'role', 'role_name', 'is_active', 'password', 'confirm_password']
        extra_kwargs = {
            # Hacemos que la contraseña sea opcional al actualizar con PATCH
            'password': {'write_only': True, 'required': False},
            'role': {'required': False} 
        }

    # Método para validar los datos de entrada
    def validate(self, data):
        # Valida contraseñas solo si se proporcionan en el request
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        
        return data

    # Método para crear un nuevo usuario
    def create(self, validated_data):
        validated_data.pop('confirm_password', None) # Elimina el campo de confirmación
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role')
        )
        return user

    # Método para actualizar un usuario
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        
        return super().update(instance, validated_data)
    
# Serializer para el cambio de contraseña
class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        return data