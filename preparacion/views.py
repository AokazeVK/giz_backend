from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Empresa, FaseEmpresa, Asesoramiento, SolicitudAsesoramiento, PublicacionEmpresaComunidad # 👈 Asegúrate de importar el nuevo modelo
from .serializers import EmpresaSerializer, FaseEmpresaSerializer, AsesoramientoSerializer, SolicitudAsesoramientoSerializer, PublicacionEmpresaComunidadSerializer  # 👈 Asegúrate de importar el nuevo serializer
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from rest_framework.permissions import IsAuthenticated
from dashboard.models import Departamento
from dashboard.serializers import DepartamentoSerializer
from .task import enviar_solicitud_asesoramiento_email
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

# ========================
# ASESORAMIENTO
# ========================
class AsesoramientoViewSet(viewsets.ModelViewSet):
    queryset = Asesoramiento.objects.all()
    serializer_class = AsesoramientoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "ver_asesoramientos",
        "retrieve": "ver_asesoramientos",
        "list_publicos": "ver_asesoramientos_publicos",
    }

    @action(detail=False, methods=["get"], url_path="publicos")
    def list_publicos(self, request):
        qs = Asesoramiento.objects.filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ========================
# SOLICITUD DE ASESORAMIENTO
# ========================
class SolicitudAsesoramientoViewSet(viewsets.ModelViewSet):
    queryset = SolicitudAsesoramiento.objects.all()
    serializer_class = SolicitudAsesoramientoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "ver_solicitudes_asesoramiento",
        "create": "crear_solicitudes_asesoramiento",
        "aprobar": "aprobar_solicitudes_asesoramiento",
        "rechazar": "rechazar_solicitudes_asesoramiento",
    }

    @action(detail=True, methods=["patch"])
    def aprobar(self, request, pk=None):
        solicitud = self.get_object()
        fecha = request.data.get("fechaAprobada")

        if not fecha:
            return Response(
                {"error": "Debe proporcionar una fechaAprobada"},
                status=status.HTTP_400_BAD_REQUEST
            )

        solicitud.estado = "APROBADO"
        solicitud.fechaAprobada = fecha
        solicitud.save()

        # Llamada al task para enviar el correo
        enviar_solicitud_asesoramiento_email.delay(solicitud.id)

        return Response(SolicitudAsesoramientoSerializer(solicitud).data)

    @action(detail=True, methods=["patch"])
    def rechazar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.estado = "RECHAZADO"
        solicitud.save()

        enviar_solicitud_asesoramiento_email.delay(solicitud.id)

        return Response(SolicitudAsesoramientoSerializer(solicitud).data)
    
class PublicacionEmpresaComunidadViewSet(viewsets.ModelViewSet):
    queryset = PublicacionEmpresaComunidad.objects.all().order_by('-created_at')
    serializer_class = PublicacionEmpresaComunidadSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "ver_publicaciones_comunidad",
        "retrieve": "ver_publicaciones_comunidad",
        "create": "crear_publicaciones_comunidad",
        "update": "editar_publicaciones_comunidad",
        "partial_update": "editar_publicaciones_comunidad",
        "destroy": "eliminar_publicaciones_comunidad",
        "toggle": "editar_publicaciones_comunidad",
        "por_empresa": "ver_publicaciones_comunidad",
    }

    def get_queryset(self):
        """
        Por defecto devuelve todas las publicaciones (con orden reciente).
        Si pasás ?activo=true devuelve solo las activas.
        """
        qs = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            if activo.lower() in ("1", "true", "yes"):
                qs = qs.filter(activo=True)
            elif activo.lower() in ("0", "false", "no"):
                qs = qs.filter(activo=False)
        return qs

    @action(detail=True, methods=["post"], url_path="toggle")
    def toggle(self, request, pk=None):
        """
        Alterna el campo 'activo' de la publicación.
        """
        publicacion = self.get_object()
        publicacion.activo = not publicacion.activo
        publicacion.save()
        return Response(
            PublicacionEmpresaComunidadSerializer(publicacion, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], url_path=r"empresa/(?P<empresa_id>[^/.]+)")
    def por_empresa(self, request, empresa_id=None):
        """
        Trae las publicaciones correspondientes a la empresa que lo publicó.
        Por defecto trae solo las activas; para incluir inactivas pasar ?include_inactive=1
        URL: /api/publicaciones-comunidad/empresa/12/
        """
        include_inactive = request.query_params.get("include_inactive")
        qs = PublicacionEmpresaComunidad.objects.filter(empresa_id=empresa_id)
        if include_inactive not in ("1", "true", "yes"):
            qs = qs.filter(activo=True)
        qs = qs.order_by("-created_at")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)