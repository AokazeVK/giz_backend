from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

# Importa el modelo y serializador del mismo módulo
from .models import Departamento
from .serializers import DepartamentoSerializer

# Importa el permiso personalizado desde tu app accounts
from accounts.permissions import HasPermissionMap

class DepartamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet para listar todos los departamentos.
    Ahora protegida con el permiso personalizado HasPermissionMap.
    """
    queryset = Departamento.objects.all().order_by("id")
    serializer_class = DepartamentoSerializer
    
    # Aquí aplicamos tu clase de permiso
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    # Y aquí definimos el mapa de permisos
    permission_code_map = {
        "list": "listar_departamentos",
        "retrieve": "listar_departamentos",
    }
