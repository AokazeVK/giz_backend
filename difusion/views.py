from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import Ministerio, Encargado
from .serializers import MinisterioSerializer, EncargadoSerializer
from accounts.permissions import HasPermissionMap
# Importa la función de utilidad para el registro de acciones
from accounts.utils import log_user_action


class MinisterioViewSet(viewsets.ModelViewSet):
    queryset = Ministerio.objects.all().order_by("id")
    serializer_class = MinisterioSerializer
    
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_ministerios",
        "retrieve": "listar_ministerios",
        "create": "crear_ministerios",
        "update": "editar_ministerios",
        "partial_update": "editar_ministerios",
        "toggle_estado": "editar_ministerios",
        "encargados_by_ministerio": "listar_encargados"
    }

    # Sobreescribe el método para registrar la creación
    def perform_create(self, serializer):
        ministerio = serializer.save()
        log_user_action(
            self.request.user, 
            f"Creó Ministerio '{ministerio.nombre}'", 
            self.request
        )

    # Sobreescribe el método para registrar la edición
    def perform_update(self, serializer):
        ministerio = serializer.save()
        log_user_action(
            self.request.user, 
            f"Editó Ministerio '{ministerio.nombre}'", 
            self.request
        )

    # Sobreescribe el método para registrar la eliminación
    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, 
            f"Eliminó Ministerio '{instance.nombre}'", 
            self.request
        )
        super().perform_destroy(instance) # Llama al método original para eliminar

    @action(detail=True, methods=['post'])
    def toggle_estado(self, request, pk=None):
        ministerio = self.get_object()
        ministerio.estado = not ministerio.estado
        ministerio.save()
        
        status_message = "activo" if ministerio.estado else "inactivo"
        log_user_action(
            request.user, 
            f"Cambió estado de Ministerio '{ministerio.nombre}' a '{status_message}'", 
            request
        )
        return Response(
            {'message': f'Ministerio {ministerio.nombre} ahora está {status_message}.'},
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=['get'])
    def encargados(self, request, pk=None):
        """
        Retorna la lista de encargados para un ministerio específico.
        Ruta: /api/difusion/ministerios/{pk}/encargados/
        """
        ministerio = self.get_object() # Obtiene el objeto Ministerio por su PK
        encargados = Encargado.objects.filter(ministerio=ministerio)
        
        # Opcional: registrar la acción
        log_user_action(
            request.user, 
            f"Consultó encargados de Ministerio '{ministerio.nombre}'", 
            request
        )
        
        serializer = EncargadoSerializer(encargados, many=True)
        return Response(serializer.data)


class EncargadoViewSet(viewsets.ModelViewSet):
    queryset = Encargado.objects.all().order_by("id")
    serializer_class = EncargadoSerializer
    
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_encargados",
        "retrieve": "listar_encargados",
        "create": "crear_encargados",
        "update": "editar_encargados",
        "partial_update": "editar_encargados",
        "toggle_estado": "editar_encargados",
    }
    
    # Sobreescribe el método para registrar la creación
    def perform_create(self, serializer):
        encargado = serializer.save()
        log_user_action(
            self.request.user, 
            f"Creó Encargado '{encargado.nombre}'", 
            self.request
        )
        
    # Sobreescribe el método para registrar la edición
    def perform_update(self, serializer):
        encargado = serializer.save()
        log_user_action(
            self.request.user, 
            f"Editó Encargado '{encargado.nombre}'", 
            self.request
        )

    # Sobreescribe el método para registrar la eliminación
    def perform_destroy(self, instance):
        log_user_action(
            self.request.user, 
            f"Eliminó Encargado '{instance.nombre}'", 
            self.request
        )
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def toggle_estado(self, request, pk=None):
        encargado = self.get_object()
        encargado.estado = not encargado.estado
        encargado.save()
        
        status_message = "activo" if encargado.estado else "inactivo"
        log_user_action(
            request.user, 
            f"Cambió estado de Encargado '{encargado.nombre}' a '{status_message}'", 
            request
        )
        return Response(
            {'message': f'Encargado {encargado.nombre} ahora está {status_message}.'},
            status=status.HTTP_200_OK
        )
    