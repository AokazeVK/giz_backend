from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Empresa
from .serializers import EmpresaSerializer
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from rest_framework.permissions import IsAuthenticated

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "ver_empresas",
        "retrieve": "ver_empresas",
        "create": "crear_empresas",
        "update": "editar_empresas",
        "partial_update": "editar_empresas",
        "destroy": "eliminar_empresas",
        "toggle_status": "editar_empresas",
        "listar_usuarios": "ver_empresas",
    }

    def perform_create(self, serializer):
        empresa = serializer.save()
        log_user_action(self.request.user, f"Creó la empresa {empresa.nombre}")

    def perform_update(self, serializer):
        empresa = serializer.save()
        log_user_action(self.request.user, f"Editó la empresa {empresa.nombre}")

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó la empresa {instance.nombre}")
        instance.delete()

    @action(detail=False, methods=['get'], url_path='usuarios') #  Ajustado a detail=False
    def listar_usuarios(self, request): #  Se eliminó pk=None
        """
        Listar todos los usuarios del sistema.
        """
        # Cambiamos la consulta para obtener todos los usuarios, no solo los de una empresa
        usuarios = User.objects.all()
        serializer = UserSerializer(usuarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"])
    def toggle_status(self, request, pk=None):
        empresa = self.get_object()
        empresa.is_active = not empresa.is_active
        empresa.save()
        status_text = "activada" if empresa.is_active else "desactivada"
        log_user_action(request.user, f"{status_text.capitalize()} la empresa {empresa.nombre}")
        return Response(
            {"status": f"Empresa {status_text} correctamente"},
            status=status.HTTP_200_OK
        )
