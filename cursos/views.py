# apps/difusion/views.py
# (Asegúrate de importar los elementos necesarios)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Curso
from .serializers import CursoSerializer
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all().order_by("id")
    serializer_class = CursoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_cursos",
        "retrieve": "listar_cursos",
        "create": "crear_cursos",
        "update": "editar_cursos",
        "partial_update": "editar_cursos",
        "destroy": "eliminar_cursos",
        "toggle_estado": "editar_cursos",
        "aumentar_visualizaciones": "listar_cursos",
         "activos": "listar_cursos_activos",
    }

    def perform_create(self, serializer):
        curso = serializer.save()
        log_user_action(self.request.user, f"Creó curso '{curso.nombre}'", self.request)

    def perform_update(self, serializer):
        curso = serializer.save()
        log_user_action(self.request.user, f"Editó curso '{curso.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó curso '{instance.nombre}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        curso = self.get_object()
        curso.is_active = not curso.is_active
        curso.save()
        status_message = "activo" if curso.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de curso '{curso.nombre}' a '{status_message}'", request)
        return Response({"message": f"Curso {curso.nombre} ahora está {status_message}."})

    @action(detail=True, methods=["post"], url_path="aumentar-visualizaciones")
    def aumentar_visualizaciones(self, request, pk=None):
        curso = self.get_object()
        curso.visualizaciones += 1
        curso.save()
        log_user_action(request.user, f"Aumentó visualizaciones de '{curso.nombre}'", request)
        return Response({"message": "Visualizaciones aumentadas", "visualizaciones": curso.visualizaciones})
    
    @action(detail=False, methods=["get"], url_path="activos")
    def activos(self, request):
        """
        Retorna la lista de cursos que tienen is_active=True.
        """
        cursos_activos = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(cursos_activos, many=True)
        return Response(serializer.data)