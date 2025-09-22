from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Empresa, FaseEmpresa # 👈 Asegúrate de importar el nuevo modelo
from .serializers import EmpresaSerializer, FaseEmpresaSerializer # 👈 Asegúrate de importar el nuevo serializer
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from rest_framework.permissions import IsAuthenticated
from dashboard.models import Departamento
from dashboard.serializers import DepartamentoSerializer

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
        "listar_departamentos": "ver_empresas",
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

    @action(detail=False, methods=['get'], url_path='usuarios')
    def listar_usuarios(self, request):
        """
        Listar todos los usuarios del sistema.
        """
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
    
    # Nueva acción para listar las fases de una empresa
    @action(detail=True, methods=['get'], url_path='fases-evaluacion')
    def fases_evaluacion(self, request, pk=None):
        """
        Obtiene las fases de evaluación de una empresa.
        Opcionalmente, se puede filtrar por gestión.
        URL: /api/empresas/{id}/fases-evaluacion/?gestion=2024
        """
        empresa = self.get_object()
        gestion = request.COOKIES.get('gestion', None)

        if gestion:
            fases = empresa.fases_empresa.filter(gestion=gestion)
        else:
            fases = empresa.fases_empresa.all()

        serializer = FaseEmpresaSerializer(fases, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'], url_path='listar-departamentos')
    def listar_departamentos(self, request):
        """
        Obtiene la lista de todos los departamentos.
        URL: /api/v1/empresas/listar-departamentos/
        """
        departamentos = Departamento.objects.all().order_by("nombre")
        serializer = DepartamentoSerializer(departamentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
