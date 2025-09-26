from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.db.models.functions import ExtractMonth

from accounts.permissions import HasPermissionMap
from cursos.models import Curso
from cursos.serializers import CursoSerializer
from preparacion.models import Empresa
from dashboard.models import Departamento
from accounts.models import UserActionLog


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para acciones de dashboard (agregaciones).
    """
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "get_conteo_empresas_por_tipoSello": "listar_dashboard_analisis",
        "get_conteo_empresas_por_departamento": "listar_dashboard_analisis",
        "usuarios_activos_por_mes": "listar_dashboard_analisis",
        "get_cursos_con_visualizaciones": "listar_dashboard_analisis",
    }

    @action(detail=False, methods=["get"], url_path="empresas-por-tipo-sello")
    def get_conteo_empresas_por_tipoSello(self, request):
        """
        Retorna el conteo de empresas agrupadas por su tipo de sello.
        """
        data = (
            Empresa.objects.values("tipoSello__nombre")
            .annotate(conteo=Count("id"))
            .order_by("tipoSello__nombre")
        )

        resultado = {d["tipoSello__nombre"]: d["conteo"] for d in data}
        return Response(resultado)

    @action(detail=False, methods=["get"], url_path="empresas-por-departamento-sello")
    def get_conteo_empresas_por_departamento(self, request):
        """
        Retorna el conteo de empresas agrupadas por departamento y tipo de sello.
        """
        data = (
            Empresa.objects.values("departamentos__nombre", "tipoSello__nombre")
            .annotate(conteo=Count("id"))
            .order_by("departamentos__nombre", "tipoSello__nombre")
        )

        resultado = {}
        for d in data:
            depto = d["departamentos__nombre"] or "SIN DEPARTAMENTO"
            sello = d["tipoSello__nombre"] or "SIN SELLO"
            if depto not in resultado:
                resultado[depto] = {}
            resultado[depto][sello] = d["conteo"]

        return Response(resultado)

    @action(detail=False, methods=["get"], url_path="usuarios-activos-por-mes")
    def usuarios_activos_por_mes(self, request):
        """
        Retorna la cantidad de logins exitosos agrupados por mes.
        """
        data = (
            UserActionLog.objects.filter(action="Login exitoso")
            .annotate(month=ExtractMonth("timestamp"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

        resultado = {meses[d["month"]]: d["total"] for d in data}
        return Response(resultado)

    
    # --- NUEVA ACCIÓN ---
    @action(detail=False, methods=['get'])
    def get_cursos_con_visualizaciones(self, request):
        """
        Retorna todos los cursos con su conteo de visualizaciones.
        """
        cursos = Curso.objects.all().order_by("id")
        serializer = CursoSerializer(cursos, many=True)
        return Response(serializer.data)
