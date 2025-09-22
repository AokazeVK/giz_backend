from rest_framework import serializers
from .models import Role, Permission, User, UserActionLog



class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo de Permisos.
    Usado para mostrar permisos de forma plana.
    """
    class Meta:
        model = Permission
        fields = ("id", "label", "code", "parent")


class PermissionTreeSerializer(serializers.ModelSerializer):
    """
    Serializador recursivo para la vista de árbol de permisos.
    Permite mostrar los permisos en una estructura jerárquica padre-hijo.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ("label", "code", "children")

    def get_children(self, obj):
        """Devuelve los hijos de un permiso para construir el árbol."""
        return PermissionTreeSerializer(obj.children.all(), many=True).data


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo de Roles.
    Permite crear y editar roles asignando permisos a través de 'permission_codes'.
    """
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Role
        fields = ("id", "name", "description", "permissions", "permission_codes", "is_active")
    def create(self, validated_data):
        """
        Crea un nuevo rol y asigna permisos desde 'permission_codes'.
        """
        codes = validated_data.pop("permission_codes", [])
        role = Role.objects.create(**validated_data)
        if codes:
            perms = Permission.objects.filter(code__in=codes)
            role.permissions.set(perms)
        return role

    def update(self, instance, validated_data):
        """
        Actualiza un rol existente y sincroniza los permisos.
        """
        codes = validated_data.pop("permission_codes", None)
        instance = super().update(instance, validated_data)
        if codes is not None:
            perms = Permission.objects.filter(code__in=codes)
            instance.permissions.set(perms)
        return instance


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    # Aquí anidamos el serializador de Empresa
    empresa = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "role_name", "is_active", "password", "confirm_password", "avatar", "empresa")


    def get_empresa(self, obj):
        from preparacion.serializers import EmpresaSerializer  # 👈 lazy import aquí
        if obj.empresa:
            return EmpresaSerializer(obj.empresa, context=self.context).data
        return None

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("confirm_password", None)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializador para cambiar la contraseña de un usuario.
    Requiere ambos campos de contraseña para validar.
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data


class UserActionLogSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo de registro de acciones del usuario.
    """
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserActionLog
        fields = ("id", "user_email", "action", "method", "path", "ip", "extra", "timestamp")
