from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Count

# Importa los modelos necesarios
from accounts.permissions import HasPermissionMap
from preparacion.models import Empresa, TipoSello
from .models import Departamento

# --- NUEVA IMPORTACIÓN ---

from cursos.models import Curso
from cursos.serializers import CursoSerializer



class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para acciones de dashboard que requieren agregaciones.
    No se mapea a un modelo específico.
    """
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    # Define el mapa de permisos para las acciones personalizadas.
    # El nombre de la acción debe coincidir con el del método.
    permission_code_map = {
        "get_conteo_empresas_por_tipoSello": "listar_dashboard_analisis",
        "get_conteo_empresas_por_departamento": "listar_dashboard_analisis",
        # --- NUEVO PERMISO ---
        "get_cursos_con_visualizaciones": "listar_dashboard_analisis",
    }
    
    @action(detail=False, methods=['get'])
    def get_conteo_empresas_por_tipoSello(self, request):
        """
        Retorna el conteo de empresas agrupadas por su tipo de sello.
        """
        data = Empresa.objects.values('tipoSello__nombre').annotate(
            conteo=Count('id')
        ).order_by('tipoSello__nombre')
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def get_conteo_empresas_por_departamento(self, request):
        """
        Retorna el conteo de empresas agrupadas por su departamento.
        """
        # La relación 'departamentos' viene del related_name en el modelo Empresa
        data = Empresa.objects.values('departamentos__nombre').annotate(
            conteo=Count('id')
        ).order_by('departamentos__nombre')
        
        return Response(data)
    
    # --- NUEVA ACCIÓN ---
    @action(detail=False, methods=['get'])
    def get_cursos_con_visualizaciones(self, request):
        """
        Retorna todos los cursos con su conteo de visualizaciones.
        """
        cursos = Curso.objects.all().order_by("id")
        serializer = CursoSerializer(cursos, many=True)
        return Response(serializer.data)
