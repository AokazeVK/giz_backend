# apps/accounts/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate

from .models import Role, User, Permission, RolePermission, UserActionLog
from .serializers import (
    RoleSerializer, UserSerializer, PasswordChangeSerializer,
    UserActionLogSerializer, PermissionTreeSerializer, PermissionSerializer
)
from .permissions import HasPermissionMap
from .utils import log_user_action


# =========================
# AUTH
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email", "").lower().strip()
    password = request.data.get("password")
    user = authenticate(request, username=email, password=password)

    if user is None:
        log_user_action(None, f"Login fallido ({email})", request)
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        log_user_action(user, "Intento de login con usuario inactivo", request)
        return Response({"error": "Tu cuenta ha sido desactivada. Contacta al administrador."}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    response = Response({"message": "Login exitoso"})
    response.set_cookie(key="access_token", value=str(refresh.access_token),
                        httponly=True, secure=False, samesite='Lax', max_age=300)
    response.set_cookie(key="refresh_token", value=str(refresh),
                        httponly=True, secure=False, samesite='Lax', max_age=86400)

    log_user_action(user, "Login exitoso", request)
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        response = Response({"message": "Logout exitoso"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
    except TokenError:
        response = Response({"message": "Logout exitoso"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

    log_user_action(request.user, "Logout exitoso", request)
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"error": "No hay refresh token"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        response = Response({"message": "Token renovado"})
        response.set_cookie(key="access_token", value=str(refresh.access_token),
                            httponly=True, secure=False, samesite='Lax', max_age=300)
        log_user_action(None, "Refresh token (nuevo access)", request)
        return response
    except TokenError:
        return Response({"error": "Refresh token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED)


# =========================
# PROFILE
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user

    role_data = None
    if user.role:
        permissions = RolePermission.objects.filter(role=user.role).select_related("permission")
        perms_list = [{"label": rp.permission.label, "code": rp.permission.code} for rp in permissions]
        role_data = {"name": user.role.name, "permissions": perms_list}


    avatar_url = user.avatar.url if user.avatar else None

    return Response({
        "username": user.username,
        "email": user.email,
        "avatar": avatar_url,  #
        "role": role_data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_view(request):
    return Response({"message": "Este endpoint es público"})


# =========================
# PERMISSIONS TREE
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permissions_tree(request):
    def build_tree(parent=None):
        nodes = []
        perms = Permission.objects.filter(parent=parent)
        for perm in perms:
            nodes.append({
                "label": perm.label,
                "key": perm.code,
                "children": build_tree(parent=perm)
            })
        return nodes

    return Response(build_tree())


# =========================
# VIEWSETS: Roles & Users
# =========================
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related("permissions").order_by("id")
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    # Map de permisos por acción del ViewSet
    permission_code_map = {
        "list": "listar_roles",
        "retrieve": "listar_roles",
        "create": "crear_roles",
        "update": "editar_roles",
        "partial_update": "editar_roles",
        "destroy": "eliminar_roles",
        "set_permissions": "editar_permisos_roles",
        "get_permissions_list": "listar_roles",
    }

    def perform_create(self, serializer):
        role = serializer.save()
        log_user_action(self.request.user, f"Creó rol '{role.name}'", self.request)

    def perform_update(self, serializer):
        role = serializer.save()
        log_user_action(self.request.user, f"Editó rol '{role.name}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó rol '{instance.name}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=["get"], url_path="permissions")
    def get_permissions_list(self, request, pk=None):
        role = self.get_object()
        codes = list(role.permissions.values_list("code", flat=True))
        return Response({"permissions": codes})

    @action(detail=True, methods=["post"], url_path="permissions")
    def set_permissions(self, request, pk=None):
        role = self.get_object()
        codes = request.data.get("permissions", [])
        perms = Permission.objects.filter(code__in=codes)
        role.permissions.set(perms)
        log_user_action(request.user, f"Actualizó permisos de rol '{role.name}'", request, extra={"codes": codes})
        return Response({"message": "Permisos actualizados", "count": perms.count()})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related("role").order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_usuarios",
        "retrieve": "listar_usuarios",
        "create": "crear_usuarios",
        "update": "editar_usuarios",
        "partial_update": "editar_usuarios",
        "destroy": "eliminar_usuarios",
        "toggle_active_status": "editar_usuarios",
        "cambiar_contrasena": "cambiar_contrasena_usuarios",
    }

    def perform_create(self, serializer):
        user = serializer.save()
        log_user_action(self.request.user, f"Creó usuario {user.email}", self.request)

    def perform_update(self, serializer):
        user = serializer.save()
        log_user_action(self.request.user, f"Editó usuario {user.email}", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó usuario {instance.email}", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_active_status(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = not instance.is_active
        instance.save()
        status_message = "activo" if instance.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de {instance.email} a {status_message}", request)
        return Response({'message': f'Usuario ahora está {status_message}.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cambiar-contrasena')
    def cambiar_contrasena(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            log_user_action(request.user, f"Cambió contraseña de {user.email}", request)
            return Response({'message': 'Contraseña cambiada exitosamente'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# LOGS (GLOBAL) – sólo para superadmin o permiso dedicado
# =========================
class LogsView(APIView):
    permission_classes = [IsAuthenticated, HasPermissionMap]
    required_permission = "ver_historial_global"

    def get(self, request):
        logs = UserActionLog.objects.select_related("user").all()[:1000]  # limita si quieres
        return Response(UserActionLogSerializer(logs, many=True).data)
