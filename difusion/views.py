from datetime import datetime, time
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

# Django y librerías de terceros
from django.db.models import Prefetch
from django.conf import settings
from django.core.mail import send_mail
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import json

# Módulos locales
from .models import Ministerio, Encargado, Convocatoria, FechaConvocatoria, ArchivoFechaConvocatoria
from .serializers import (
    MinisterioSerializer,
    EncargadoSerializer,
    ConvocatoriaSerializer,
    FechaConvocatoriaSerializer,
    ArchivoFechaConvocatoriaSerializer,
)
from .utils import send_email_notification
from .task import enviar_convocatoria_email  # Importación de la tarea de Celery
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action

# --- Vista para Ministerios ---
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

    def perform_create(self, serializer):
        ministerio = serializer.save()
        log_user_action(self.request.user, f"Creó Ministerio '{ministerio.nombre}'", self.request)

    def perform_update(self, serializer):
        ministerio = serializer.save()
        log_user_action(self.request.user, f"Editó Ministerio '{ministerio.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Ministerio '{instance.nombre}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=['post'])
    def toggle_estado(self, request, pk=None):
        ministerio = self.get_object()
        ministerio.is_active = not ministerio.is_active
        ministerio.save()
        status_message = "activo" if ministerio.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de Ministerio '{ministerio.nombre}' a '{status_message}'", request)
        return Response({'message': f'Ministerio {ministerio.nombre} ahora está {status_message}.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def encargados(self, request, pk=None):
        ministerio = self.get_object()
        encargados = Encargado.objects.filter(ministerio=ministerio)
        log_user_action(request.user, f"Consultó encargados de Ministerio '{ministerio.nombre}'", request)
        serializer = EncargadoSerializer(encargados, many=True)
        return Response(serializer.data)

# --- Vista para Encargados ---
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
    
    def perform_create(self, serializer):
        encargado = serializer.save()
        log_user_action(self.request.user, f"Creó Encargado '{encargado.nombre}'", self.request)
        
    def perform_update(self, serializer):
        encargado = serializer.save()
        log_user_action(self.request.user, f"Editó Encargado '{encargado.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Encargado '{instance.nombre}'", self.request)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def toggle_estado(self, request, pk=None):
        encargado = self.get_object()
        encargado.is_active = not encargado.is_active
        encargado.save()
        status_message = "activo" if encargado.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de Encargado '{encargado.nombre}' a '{status_message}'", request)
        return Response({'message': f'Encargado {encargado.nombre} ahora está {status_message}.'}, status=status.HTTP_200_OK)

# --- Vista para Convocatorias ---
class ConvocatoriaViewSet(viewsets.ModelViewSet):
    queryset = Convocatoria.objects.all().order_by("id")
    serializer_class = ConvocatoriaSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_convocatorias",
        "retrieve": "listar_convocatorias",
        "create": "crear_convocatorias",
        "update": "editar_convocatorias",
        "partial_update": "editar_convocatorias",
        "destroy": "eliminar_convocatorias",
        "toggle_estado": "editar_convocatorias",
        "con_fechas": "listar_convocatorias",
    }

    def perform_create(self, serializer):
        convocatoria = serializer.save()
        log_user_action(self.request.user, f"Creó convocatoria '{convocatoria.nombre}'", self.request)

    def perform_update(self, serializer):
        convocatoria = serializer.save()
        log_user_action(self.request.user, f"Editó convocatoria '{convocatoria.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó convocatoria '{instance.nombre}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        convocatoria = self.get_object()
        convocatoria.is_active = not convocatoria.is_active
        convocatoria.save()
        status_message = "activo" if convocatoria.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de Convocatoria '{convocatoria.nombre}' a '{status_message}'", request)
        return Response({"message": f"Convocatoria {convocatoria.nombre} ahora está {status_message}."})

    @action(detail=False, methods=["get"], url_path="con-fechas")
    def con_fechas(self, request):
        gestion = request.query_params.get("gestion") or request.COOKIES.get("gestion")
        if not gestion:
            return Response({"error": "Parámetro 'gestion' requerido (o cookie 'gestion' presente)"}, status=status.HTTP_400_BAD_REQUEST)

        fechas_qs = FechaConvocatoria.objects.filter(gestion=gestion, is_active=True)
        qs = self.get_queryset().prefetch_related(Prefetch("fechas", queryset=fechas_qs))
        serializer = self.get_serializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

# --- Vista para Fechas de Convocatoria ---
class FechaConvocatoriaViewSet(viewsets.ModelViewSet):
    queryset = FechaConvocatoria.objects.all().order_by("id")
    serializer_class = FechaConvocatoriaSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_fechas_convocatorias",
        "retrieve": "listar_fechas_convocatorias",
        "create": "crear_fechas_convocatorias",
        "update": "editar_fechas_convocatorias",
        "partial_update": "editar_fechas_convocatorias",
        "destroy": "eliminar_fechas_convocatorias",
        "toggle_estado": "editar_fechas_convocatorias",
        "enviar_notificacion": "crear_fechas_convocatorias",
    }

    def perform_create(self, serializer):
        # Obtener la gestión de la cookie
        gestion = self.request.COOKIES.get("gestion")
        if not gestion:
            raise serializers.ValidationError({"gestion": "Cookie 'gestion' requerida para crear fecha"})

        fecha = serializer.save(gestion=gestion)

        fecha_hora_completa = datetime.combine(fecha.fecha_inicio, fecha.hora_inicio)
        fecha_hora_completa = timezone.make_aware(fecha_hora_completa, timezone.get_current_timezone())

        if fecha_hora_completa > timezone.now():
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=fecha_hora_completa)
            task = PeriodicTask.objects.create(
                clocked=clocked,
                name=f"Notificación convocatoria {fecha.id}",
                task="difusion.task.enviar_convocatoria_email",
                args=json.dumps([fecha.id]),
                one_off=True
            )
            fecha.periodic_task = task
            fecha.save()

        log_user_action(self.request.user, f"Creó fecha {fecha.id} para convocatoria '{fecha.convocatoria.nombre}'", self.request)

    def perform_update(self, serializer):
        fecha = serializer.save()

        # Si tenía tarea asociada → eliminarla
        if fecha.periodic_task:
            fecha.periodic_task.delete()
            fecha.periodic_task = None

        # Reprogramar nueva si sigue activa
        if fecha.is_active:
            fecha_hora_completa = datetime.combine(fecha.fecha_inicio, fecha.hora_inicio)
            fecha_hora_completa = timezone.make_aware(fecha_hora_completa, timezone.get_current_timezone())
            if fecha_hora_completa > timezone.now():
                clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=fecha_hora_completa)
                task = PeriodicTask.objects.create(
                    clocked=clocked,
                    name=f"Notificación convocatoria {fecha.id}",
                    task="difusion.task.enviar_convocatoria_email",
                    args=json.dumps([fecha.id]),
                    one_off=True
                )
                fecha.periodic_task = task
                fecha.save()

        log_user_action(self.request.user, f"Editó fecha {fecha.id} de convocatoria '{fecha.convocatoria.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó fecha {instance.id} de convocatoria '{instance.convocatoria.nombre}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        fecha = self.get_object()
        fecha.is_active = not fecha.is_active
        fecha.save()

        if not fecha.is_active:
            # Si se desactiva → borrar la tarea
            if fecha.periodic_task:
                fecha.periodic_task.delete()
                fecha.periodic_task = None
                fecha.save()
        else:
            # Si se reactiva → volver a programar la tarea
            fecha_hora_completa = datetime.combine(fecha.fecha_inicio, fecha.hora_inicio)
            fecha_hora_completa = timezone.make_aware(fecha_hora_completa, timezone.get_current_timezone())
            if fecha_hora_completa > timezone.now():
                clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=fecha_hora_completa)
                task = PeriodicTask.objects.create(
                    clocked=clocked,
                    name=f"Notificación convocatoria {fecha.id}",
                    task="difusion.task.enviar_convocatoria_email",
                    args=json.dumps([fecha.id]),
                    one_off=True
                )
                fecha.periodic_task = task
                fecha.save()

        status_message = "activo" if fecha.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de fecha {fecha.id} a '{status_message}'", request)
        return Response({"message": f"Fecha {fecha.id} ahora está {status_message}."})

    @action(detail=True, methods=["post"], url_path="enviar-notificacion")
    def enviar_notificacion(self, request, pk=None):
        try:
            fecha_convocatoria = self.get_object()
            
            encargados = Encargado.objects.filter(is_active=True)
            if not encargados.exists():
                return Response({"message": "No hay encargados activos para notificar."}, status=status.HTTP_404_NOT_FOUND)
            
            recipient_list = [encargado.correo for encargado in encargados]
            archivos_qs = ArchivoFechaConvocatoria.objects.filter(fecha_convocatoria=fecha_convocatoria)
            archivos_data = ArchivoFechaConvocatoriaSerializer(archivos_qs, many=True, context={'request': request}).data
            
            context = {
                'convocatoria': fecha_convocatoria.convocatoria,
                'fecha_convocatoria': fecha_convocatoria,
                'convocatoria_archivos': archivos_data,
                'encargado_nombre': 'Estimado(a) Encargado(a)',
            }
            subject = f"Nueva Convocatoria: {fecha_convocatoria.convocatoria.nombre}"
            
            if send_email_notification(subject, 'emails/convocatoria_notification.html', context, recipient_list):
                log_user_action(request.user, f"Envió notificación de convocatoria '{fecha_convocatoria.convocatoria.nombre}' a encargados (fecha_id={pk})", request)
                return Response({"message": "Notificación por correo enviada exitosamente."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No se pudo enviar la notificación por correo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Ocurrió un error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# --- Vista para Archivos de Convocatoria ---
class ArchivoFechaConvocatoriaViewSet(viewsets.ModelViewSet):
    queryset = ArchivoFechaConvocatoria.objects.all().order_by("id")
    serializer_class = ArchivoFechaConvocatoriaSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_archivos_fechas_convocatorias",
        "retrieve": "listar_archivos_fechas_convocatorias",
        "create": "crear_archivos_fechas_convocatorias",
        "destroy": "eliminar_archivos_fechas_convocatorias",
    }

    def perform_create(self, serializer):
        archivo = serializer.save()
        log_user_action(self.request.user, f"Subió archivo '{archivo.nombre}' (fecha_id={archivo.fecha_convocatoria_id})", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó archivo '{instance.nombre}' (fecha_id={instance.fecha_convocatoria_id})", self.request)
        super().perform_destroy(instance)