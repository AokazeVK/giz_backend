from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch

# Importa los nuevos modelos y serializadores
from .models import TipoSello, Requisito, RequisitoInput, ChecklistEvaluacion, Evaluacion, EvaluacionFases
from .serializers import (
    TipoSelloSerializer, 
    RequisitoSerializer, 
    RequisitoInputSerializer,
    ChecklistEvaluacionSerializer, 
    EvaluacionSerializer,
    EvaluacionFasesSerializer
)
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action

# Importación de la tarea de Celery
from .task import enviar_evaluacion_email

class TipoSelloViewSet(viewsets.ModelViewSet):
    queryset = TipoSello.objects.all()
    serializer_class = TipoSelloSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_tipos_sello",
        "retrieve": "listar_tipos_sello",
        "create": "crear_tipos_sello",
        "update": "editar_tipos_sello",
        "partial_update": "editar_tipos_sello",
        "destroy": "eliminar_tipos_sello",
    }
    
    def get_queryset(self):
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            evaluaciones_qs = Evaluacion.objects.filter(gestion=gestion).prefetch_related("evaluadores")
            return TipoSello.objects.all().prefetch_related(
                "requisitos__inputs",
                Prefetch("evaluaciones", queryset=evaluaciones_qs)
            )
        return TipoSello.objects.all().prefetch_related("requisitos__inputs", "evaluaciones__evaluadores")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["gestion"] = self.request.COOKIES.get("gestion")
        return context
    
    def perform_create(self, serializer):
        tiposello = serializer.save()
        log_user_action(self.request.user, f"Creó Tipo de Sello: {tiposello.nombre}", self.request)

    def perform_update(self, serializer):
        tiposello = serializer.save()
        log_user_action(self.request.user, f"Actualizó Tipo de Sello: {tiposello.nombre}", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Tipo de Sello: {instance.nombre}", self.request)
        super().perform_destroy(instance)


class RequisitoViewSet(viewsets.ModelViewSet):
    queryset = Requisito.objects.all().prefetch_related("inputs")
    serializer_class = RequisitoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_requisitos",
        "retrieve": "listar_requisitos",
        "create": "crear_requisitos",
        "update": "editar_requisitos",
        "partial_update": "editar_requisitos",
        "destroy": "eliminar_requisitos",
    }
    
    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            qs = qs.filter(gestion=gestion)
        return qs

    def perform_create(self, serializer):
        gestion = self.request.COOKIES.get("gestion")
        if not gestion:
            return Response({"error": "La cookie 'gestion' es requerida para crear un requisito."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        requisito = serializer.save(gestion=gestion)
        log_user_action(self.request.user, f"Creó un Requisito con ID: {requisito.id}", self.request)
        
    def perform_update(self, serializer):
        requisito = serializer.save()
        log_user_action(self.request.user, f"Actualizó un Requisito con ID: {requisito.id}", self.request)
        
    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Requisito con ID: {instance.id}", self.request)
        super().perform_destroy(instance)


class RequisitoInputViewSet(viewsets.ModelViewSet):
    queryset = RequisitoInput.objects.all()
    serializer_class = RequisitoInputSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_requisitos_input",
        "retrieve": "listar_requisitos_input",
        "create": "crear_requisitos_input",
        "update": "editar_requisitos_input",
        "partial_update": "editar_requisitos_input",
        "destroy": "eliminar_requisitos_input",
        "toggle_status": "editar_requisitos_input",
    }
    
    def perform_create(self, serializer):
        input_instance = serializer.save()
        log_user_action(self.request.user, f"Creó RequisitoInput: {input_instance.label}", self.request)

    def perform_update(self, serializer):
        input_instance = serializer.save()
        log_user_action(self.request.user, f"Actualizó RequisitoInput: {input_instance.label}", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó RequisitoInput: {instance.label}", self.request)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de un RequisitoInput.
        """
        requisito_input = self.get_object()
        requisito_input.isActive = not requisito_input.isActive
        requisito_input.save()
        log_user_action(self.request.user, f"Se alternó el estado de RequisitoInput con ID: {requisito_input.id} a {requisito_input.isActive}", self.request)
        return Response({"message": f"El estado del RequisitoInput ha sido cambiado a {requisito_input.isActive}."}, status=status.HTTP_200_OK)
    
        
class ChecklistEvaluacionViewSet(viewsets.ModelViewSet):
    # El serializador ya maneja la relación
    queryset = ChecklistEvaluacion.objects.all()
    serializer_class = ChecklistEvaluacionSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_checklist_evaluacion",
        "retrieve": "listar_checklist_evaluacion",
        "create": "crear_checklist_evaluacion",
        "update": "editar_checklist_evaluacion",
        "partial_update": "editar_checklist_evaluacion",
        "destroy": "eliminar_checklist_evaluacion",
        "toggle_status": "editar_checklist_evaluacion",
    }

    def perform_create(self, serializer):
        checklist = serializer.save()
        log_user_action(self.request.user, f"Creó Checklist de Evaluación: {checklist.nombre}", self.request)
    
    def perform_update(self, serializer):
        checklist = serializer.save()
        log_user_action(self.request.user, f"Actualizó Checklist de Evaluación: {checklist.nombre}", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Checklist de Evaluación: {instance.nombre}", self.request)
        super().perform_destroy(instance)
        
    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de un Checklist de Evaluación.
        """
        checklist = self.get_object()
        checklist.isActive = not checklist.isActive
        checklist.save()
        log_user_action(self.request.user, f"Se alternó el estado de Checklist con ID: {checklist.id} a {checklist.isActive}", self.request)
        return Response({"message": f"El estado del Checklist ha sido cambiado a {checklist.isActive}."}, status=status.HTTP_200_OK)


# Nuevo ViewSet para las fases de evaluación
class EvaluacionFasesViewSet(viewsets.ModelViewSet):
    queryset = EvaluacionFases.objects.all().prefetch_related("checklists")
    serializer_class = EvaluacionFasesSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]

    permission_code_map = {
        "list": "listar_fases_evaluacion",
        "retrieve": "listar_fases_evaluacion",
        "create": "crear_fases_evaluacion",
        "update": "editar_fases_evaluacion",
        "partial_update": "editar_fases_evaluacion",
        "destroy": "eliminar_fases_evaluacion",
        "toggle_status": "editar_fases_evaluacion",
    }
    
    def perform_create(self, serializer):
        # Obtiene el ID de la evaluación del validated_data
        evaluacion_id = serializer.validated_data.get('evaluacion').id
        
        # Filtra la evaluación para obtener el campo 'gestion'
        try:
            evaluacion = Evaluacion.objects.get(id=evaluacion_id)
            gestion = evaluacion.gestion
        except Evaluacion.DoesNotExist:
            return Response({"error": "La evaluación proporcionada no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Asigna la gestión a la instancia de la fase antes de guardar
        fase = serializer.save(gestion=gestion)
        log_user_action(self.request.user, f"Creó una fase: {fase.nombre}", self.request)
    
    def perform_update(self, serializer):
        fase = serializer.save()
        log_user_action(self.request.user, f"Actualizó la fase: {fase.nombre}", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó la fase: {instance.nombre}", self.request)
        super().perform_destroy(instance)

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Alterna el estado (activo/inactivo) de una fase de evaluación.
        """
        fase = self.get_object()
        fase.isActive = not fase.isActive
        fase.save()
        log_user_action(self.request.user, f"Se alternó el estado de la fase con ID: {fase.id} a {fase.isActive}", self.request)
        return Response({"message": f"El estado de la fase ha sido cambiado a {fase.isActive}."}, status=status.HTTP_200_OK)

class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all().prefetch_related("evaluadores", "fases__checklists")
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_evaluaciones",
        "retrieve": "listar_evaluaciones",
        "create": "crear_evaluaciones",
        "update": "editar_evaluaciones",
        "partial_update": "editar_evaluaciones",
        "destroy": "eliminar_evaluaciones",
        "cambiar_estado": "editar_evaluaciones",
    }
    
    def get_queryset(self):
        qs = super().get_queryset()
        gestion = self.request.COOKIES.get("gestion")
        if gestion:
            # Aquí se filtra por la gestión de la evaluación, no de las fases
            qs = qs.filter(gestion=gestion)
        return qs
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["gestion"] = self.request.COOKIES.get("gestion")
        return context

    def perform_create(self, serializer):
        evaluacion = serializer.save()
        log_user_action(self.request.user, f"Creó Evaluación para: {evaluacion.tipoSello.nombre} en gestión {evaluacion.gestion}", self.request)
        
        # Llama a la tarea de Celery de forma asíncrona
        evaluadores_ids = list(evaluacion.evaluadores.values_list('id', flat=True))
        if evaluadores_ids:
            enviar_evaluacion_email.delay(evaluacion.id, evaluadores_ids)

    def perform_update(self, serializer):
        old_evaluadores = set(self.get_object().evaluadores.all())
        evaluacion = serializer.save()
        new_evaluadores = set(evaluacion.evaluadores.all())
        added_evaluadores = new_evaluadores - old_evaluadores
        
        log_user_action(self.request.user, f"Actualizó Evaluación para: {evaluacion.tipoSello.nombre} en gestión {evaluacion.gestion}", self.request)
        
        if added_evaluadores:
            added_evaluadores_ids = list(user.id for user in added_evaluadores)
            enviar_evaluacion_email.delay(evaluacion.id, added_evaluadores_ids)
            log_user_action(self.request.user, f"Se programó el envío de correo a {len(added_evaluadores)} nuevos evaluadores.", self.request)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó Evaluación para: {instance.tipoSello.nombre} en gestión {instance.gestion}", self.request)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        evaluacion = self.get_object()
        new_status = request.data.get("estado")
        
        if new_status and new_status in dict(Evaluacion.ESTADO_CHOICES):
            evaluacion.estado = new_status
            evaluacion.save()
            log_user_action(self.request.user, f"Cambió el estado de la evaluación {evaluacion.id} a '{new_status}'", self.request)
            return Response({"message": f"Estado de la evaluación cambiado a '{new_status}'."}, 
                            status=status.HTTP_200_OK)
        
        return Response({"error": "Estado inválido proporcionado."}, status=status.HTTP_400_BAD_REQUEST)
