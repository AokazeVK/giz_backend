from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate

from .models import Role, User
from .serializers import RoleSerializer, UserSerializer, PasswordChangeSerializer

# ============
# LOGIN
# ============
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({"error": "Tu cuenta ha sido desactivada. Contacta al administrador."}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    response = Response({"message": "Login exitoso"})
    
    response.set_cookie(key="access_token", value=str(refresh.access_token), httponly=True, secure=False, samesite='Lax', max_age=300)
    response.set_cookie(key="refresh_token", value=str(refresh), httponly=True, secure=False, samesite='Lax', max_age=86400)
    return response

# ... el resto de tus vistas de autenticación (logout, refresh, profile, public) ...

# ============
# LOGOUT
# ============
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
        return response
    except TokenError:
        response = Response({"message": "Logout exitoso"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

# ============
# REFRESH TOKEN
# ============
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.COOKIES.get("refresh_token")

    if not refresh_token:
        return Response({"error": "No hay refresh token"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh = RefreshToken(refresh_token)
        response = Response({"message": "Token renovado"})
        response.set_cookie(key="access_token", value=str(refresh.access_token), httponly=True, secure=False, samesite='Lax', max_age=300)
        return response
    except TokenError:
        return Response({"error": "Refresh token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED)

# ============
# ENDPOINT PROTEGIDO
# ============
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    return Response({
        "username": request.user.username,
        "email": request.user.email
    })


# ============
# ENDPOINT PÚBLICO
# ============
@api_view(['GET'])
@permission_classes([AllowAny])
def public_view(request):
    return Response({"message": "Este endpoint es público"})

# ViewSet para el CRUD de Roles
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

# ViewSet para el CRUD de Usuarios
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    # Esta acción personalizada activa/desactiva al usuario
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_active_status(self, request, pk=None):
        instance = self.get_object()
        
        instance.is_active = not instance.is_active
        instance.save()

        status_message = "activo" if instance.is_active else "inactivo"
        return Response({'message': f'Usuario ahora está {status_message}.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cambiar-contrasena')
    def cambiar_contrasena(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({'message': 'Contraseña cambiada exitosamente'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)