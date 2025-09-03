from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from .utils import send_email_notification  # Asegúrate de que esta importación sea correcta
from .models import Ministerio, Encargado, Convocatoria, FechaConvocatoria, ArchivoFechaConvocatoria
from .serializers import MinisterioSerializer, EncargadoSerializer,  ConvocatoriaSerializer, FechaConvocatoriaSerializer, ArchivoFechaConvocatoriaSerializer
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
        ministerio.is_active = not ministerio.is_active
        ministerio.save()
        
        status_message = "activo" if ministerio.is_active else "inactivo"
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
        encargado.is_active = not encargado.is_active
        encargado.save()
        
        status_message = "activo" if encargado.is_active else "inactivo"
        log_user_action(
            request.user, 
            f"Cambió estado de Encargado '{encargado.nombre}' a '{status_message}'", 
            request
        )
        return Response(
            {'message': f'Encargado {encargado.nombre} ahora está {status_message}.'},
            status=status.HTTP_200_OK
        )
    


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
        """
        GET /api/difusion/convocatorias/con-fechas/?gestion=2025
        Fallback: toma gestion desde cookie 'gestion' si no viene en query params.
        Devuelve convocatorias con sus fechas filtradas por la gestion dada.
        """
        gestion = request.query_params.get("gestion") or request.COOKIES.get("gestion")
        if not gestion:
            return Response({"error": "Parametro 'gestion' requerido (o cookie 'gestion' presente)"}, status=status.HTTP_400_BAD_REQUEST)

        # Prefetch fechas filtradas para evitar N+1
        fechas_qs = FechaConvocatoria.objects.filter(gestion=gestion, is_active=True)
        qs = self.get_queryset().prefetch_related(Prefetch("fechas", queryset=fechas_qs))
        serializer = self.get_serializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


# apps/your_app/views.py
from django.db.models import Prefetch
from django.conf import settings
from .utils import send_email_notification  # Asegúrate de que esta importación sea correcta
from .models import Ministerio, Encargado, Convocatoria, FechaConvocatoria, ArchivoFechaConvocatoria
from .serializers import (
    MinisterioSerializer,
    EncargadoSerializer,
    ConvocatoriaSerializer,
    FechaConvocatoriaSerializer,
    ArchivoFechaConvocatoriaSerializer,
)
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

# ... (tus otras clases de ViewSet)

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
        # Nuevo permiso para el endpoint de notificación
        "enviar_notificacion": "crear_fechas_convocatorias", 
    }

    # ... (tus métodos perform_create, perform_update, perform_destroy y toggle_estado)

    def perform_create(self, serializer):
        gestion = self.request.COOKIES.get("gestion")
        if not gestion:
            raise serializers.ValidationError({"gestion": "Cookie 'gestion' requerida para crear fecha"})
        fecha = serializer.save(gestion=gestion)
        log_user_action(self.request.user, f"Creó fecha {fecha.id} para convocatoria '{fecha.convocatoria.nombre}' (gestion={fecha.gestion})", self.request)

    def perform_update(self, serializer):
        fecha = serializer.save()
        log_user_action(self.request.user, f"Editó fecha {fecha.id} de convocatoria '{fecha.convocatoria.nombre}'", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó fecha {instance.id} de convocatoria '{instance.convocatoria.nombre}'", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=["post"], url_path="toggle-estado")
    def toggle_estado(self, request, pk=None):
        fecha = self.get_object()
        fecha.is_active = not fecha.is_active
        fecha.save()
        status_message = "activo" if fecha.is_active else "inactivo"
        log_user_action(request.user, f"Cambió estado de fecha {fecha.id} a '{status_message}'", request)
        return Response({"message": f"Fecha {fecha.id} ahora está {status_message}."})

    # El nuevo endpoint para enviar notificaciones
    @action(detail=True, methods=["post"], url_path="enviar-notificacion")
    def enviar_notificacion(self, request, pk=None):
        """
        Envía una notificación por correo a todos los encargados sobre los archivos
        de una FechaConvocatoria específica.
        URL: /api/difusion/fechas-convocatorias/{pk}/enviar-notificacion/
        """
        try:
            fecha_convocatoria = self.get_object()
            
            # Obtener todos los encargados activos a quienes notificar
            encargados = Encargado.objects.filter(is_active=True)
            if not encargados.exists():
                return Response({"message": "No hay encargados activos para notificar."}, status=status.HTTP_404_NOT_FOUND)
            
            recipient_list = [encargado.correo for encargado in encargados]
            
            # Obtener los archivos de esta fecha de convocatoria
            archivos_qs = ArchivoFechaConvocatoria.objects.filter(fecha_convocatoria=fecha_convocatoria)
            
            # Ojo: Aquí es donde necesitamos el contexto del request para las URLs de los archivos
            archivos_data = ArchivoFechaConvocatoriaSerializer(archivos_qs, many=True, context={'request': request}).data
            
            # Preparar el contexto del correo
            context = {
                'convocatoria': fecha_convocatoria.convocatoria,
                'fecha_convocatoria': fecha_convocatoria,
                'convocatoria_archivos': archivos_data,
                'encargado_nombre': 'Estimado(a) Encargado(a)',
            }
            
            subject = f"Nueva Convocatoria: {fecha_convocatoria.convocatoria.nombre}"
            
            if send_email_notification(subject, 'emails/convocatoria_notification.html', context, recipient_list):
                log_user_action(
                    request.user,
                    f"Envió notificación de convocatoria '{fecha_convocatoria.convocatoria.nombre}' a encargados (fecha_id={pk})",
                    request
                )
                return Response({"message": "Notificación por correo enviada exitosamente."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No se pudo enviar la notificación por correo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # En caso de cualquier otro error inesperado
            return Response({"error": f"Ocurrió un error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        # opcional: borrar archivo del FS si quieres
        # instance.file.delete(save=False)
        log_user_action(self.request.user, f"Eliminó archivo '{instance.nombre}' (fecha_id={instance.fecha_convocatoria_id})", self.request)
        super().perform_destroy(instance)
    