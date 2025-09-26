# apps/preparacion/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Django y librerías de terceros
from django.db.models import Prefetch

# Módulos locales
from accounts.models import User
from accounts.serializers import UserSerializer
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from dashboard.models import Departamento
from dashboard.serializers import DepartamentoSerializer
from .models import (
    Capacitacion,
    Empresa,
    FaseEmpresa,
    Asesoramiento,
    SolicitudAsesoramiento,
    PublicacionEmpresaComunidad,
    ArchivoAsesoramiento,
    EncargadoAsesoramiento
)
from .serializers import (
    CapacitacionSerializer,
    EmpresaSerializer,
    FaseEmpresaSerializer,
    AsesoramientoSerializer,
    SolicitudAsesoramientoSerializer,
    PublicacionEmpresaComunidadSerializer,
    ArchivoAsesoramientoSerializer,
    EncargadoAsesoramientoSerializer
)
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
        "create": "crear_asesoramientos",
        "update": "editar_asesoramientos",
        "partial_update": "editar_asesoramientos",
        "destroy": "eliminar_asesoramientos",
        "toggle_estado": "editar_asesoramientos",
        "list_publicos": "ver_asesoramientos_publicos",
        "list_encargados_asesoramiento": "listar_encargados_asesoramiento",
        "list_archivos_asesoramiento": "listar_archivos_asesoramiento",
    }
    
    def perform_create(self, serializer):
        asesoramiento = serializer.save()
        log_user_action(self.request.user, f"Creó el Asesoramiento '{asesoramiento.nombre}'", self.request)

    def perform_update(self, serializer):
        asesoramiento = serializer.save()
        log_user_action(self.request.user, f"Editó el Asesoramiento '{asesoramiento.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó el Asesoramiento '{instance.nombre}'", self.request)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        asesoramiento = self.get_object()
        asesoramiento.is_active = not asesoramiento.is_active
        asesoramiento.save()
        status_message = "activo" if asesoramiento.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de Asesoramiento '{asesoramiento.nombre}' a '{status_message}'", request)
        return Response({"message": f"Asesoramiento {asesoramiento.nombre} ahora está {status_message}."})

    @action(detail=False, methods=["get"], url_path="publicos")
    def list_publicos(self, request):
        qs = Asesoramiento.objects.filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get"], url_path="encargados")
    def list_encargados_asesoramiento(self, request, pk=None):
        asesoramiento = self.get_object()
        encargados = asesoramiento.encargados_asesoramiento.filter(is_active=True)
        serializer = EncargadoAsesoramientoSerializer(encargados, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="archivos")
    def list_archivos_asesoramiento(self, request, pk=None):
        asesoramiento = self.get_object()
        archivos = asesoramiento.archivos.filter(is_active=True)
        serializer = ArchivoAsesoramientoSerializer(archivos, many=True, context={'request': request})
        return Response(serializer.data)


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
        "completar": "completar_solicitudes_asesoramiento",  # Nuevo permiso
        "cancelar": "cancelar_solicitudes_asesoramiento",    # Nuevo permiso
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

    @action(detail=True, methods=["patch"])
    def completar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.estado = "COMPLETADO"
        solicitud.save()
        log_user_action(request.user, f"Marcó como completada la solicitud de asesoramiento para la empresa '{solicitud.empresa.nombre}'", self.request)
        
        # No se envía correo electrónico, solo se actualiza el estado.
        return Response(SolicitudAsesoramientoSerializer(solicitud).data)

    @action(detail=True, methods=["patch"])
    def cancelar(self, request, pk=None):
        solicitud = self.get_object()
        solicitud.estado = "CANCELADO"
        solicitud.save()
        log_user_action(request.user, f"Canceló la solicitud de asesoramiento para la empresa '{solicitud.empresa.nombre}'", self.request)

        # No se envía correo electrónico, solo se actualiza el estado.
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


# ============================
#   VISTA PARA ARCHIVOS DE ASESORAMIENTO
# ============================
class ArchivoAsesoramientoViewSet(viewsets.ModelViewSet):
    queryset = ArchivoAsesoramiento.objects.all().order_by("id")
    serializer_class = ArchivoAsesoramientoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_archivos_asesoramiento",
        "retrieve": "listar_archivos_asesoramiento",
        "create": "crear_archivos_asesoramiento",
        "destroy": "eliminar_archivos_asesoramiento",
    }

    def perform_create(self, serializer):
        archivo = serializer.save()
        log_user_action(self.request.user, f"Subió archivo '{archivo.nombre}' (asesoramiento_id={archivo.asesoramiento_id})", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó archivo '{instance.nombre}' (asesoramiento_id={instance.asesoramiento_id})", self.request)
        super().perform_destroy(instance)


# ============================
#   VISTA PARA ENCARGADOS DE ASESORAMIENTO
# ============================
class EncargadoAsesoramientoViewSet(viewsets.ModelViewSet):
    queryset = EncargadoAsesoramiento.objects.all().order_by("id")
    serializer_class = EncargadoAsesoramientoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_encargados_asesoramiento",
        "retrieve": "listar_encargados_asesoramiento",
        "create": "crear_encargados_asesoramiento",
        "update": "editar_encargados_asesoramiento",
        "partial_update": "editar_encargados_asesoramiento",
        "destroy": "eliminar_encargados_asesoramiento",
        "toggle_estado": "editar_encargados_asesoramiento"
    }

    def perform_create(self, serializer):
        encargado_as = serializer.save()
        log_user_action(self.request.user, f"Creó Encargado de Asesoramiento '{encargado_as.nombre}' para '{encargado_as.asesoramiento.nombre}'", self.request)

    def perform_update(self, serializer):
        encargado_as = serializer.save()
        log_user_action(self.request.user, f"Editó Encargado de Asesoramiento '{encargado_as.nombre}' para '{encargado_as.asesoramiento.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Encargado de Asesoramiento '{instance.nombre}' para '{instance.asesoramiento.nombre}'", self.request)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def toggle_estado(self, request, pk=None):
        encargado_as = self.get_object()
        encargado_as.is_active = not encargado_as.is_active
        encargado_as.save()
        status_message = "activo" if encargado_as.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de Encargado de Asesoramiento '{encargado_as.nombre}' a '{status_message}'", request)
        return Response({'message': f'Encargado de Asesoramiento ahora está {status_message}.'}, status=status.HTTP_200_OK)

class CapacitacionViewSet(viewsets.ModelViewSet):
    queryset = Capacitacion.objects.all().order_by("-created_at")
    serializer_class = CapacitacionSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "ver_capacitaciones",
        "retrieve": "ver_capacitaciones",
        "create": "crear_capacitaciones",
        "update": "editar_capacitaciones",
        "partial_update": "editar_capacitaciones",
        "destroy": "eliminar_capacitaciones",
        "toggle_estado": "editar_capacitaciones",
    }

    def perform_create(self, serializer):
        capacitacion = serializer.save()
        log_user_action(
            self.request.user,
            f"Creó la capacitación '{capacitacion.nombre}'",
            self.request
        )

    def perform_update(self, serializer):
        capacitacion = serializer.save()
        log_user_action(
            self.request.user,
            f"Editó la capacitación '{capacitacion.nombre}'",
            self.request
        )

    def perform_destroy(self, instance):
        log_user_action(
            self.request.user,
            f"Eliminó la capacitación '{instance.nombre}'",
            self.request
        )
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        capacitacion = self.get_object()
        capacitacion.is_active = not capacitacion.is_active
        capacitacion.save()
        estado = "activa" if capacitacion.is_active else "inactiva"
        log_user_action(
            request.user,
            f"Cambió estado de la capacitación '{capacitacion.nombre}' a {estado}",
            request
        )
        return Response(
            {"message": f"La capacitación '{capacitacion.nombre}' ahora está {estado}."},
            status=status.HTTP_200_OK
        )