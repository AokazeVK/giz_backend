from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Evento
from .serializers import EventoSerializer
from .task import enviar_evento_email, enviar_evento_actualizado_email
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated, HasPermissionMap]
    
    permission_code_map = {
        "list": "listar_eventos",
        "retrieve": "listar_eventos",
        "create": "crear_eventos",
        "update": "editar_eventos",
        "partial_update": "editar_eventos",
        "destroy": "eliminar_eventos",
    }
    
    def perform_create(self, serializer):
        evento = serializer.save()
        log_user_action(self.request.user, f"Creó el evento: {evento.nombre}")
        # Llama a la tarea de forma asíncrona
        enviar_evento_email.delay(evento.id) 

    def perform_update(self, serializer):
        # Captura los datos antiguos antes de la actualización para enviarlos en el email
        old_data = EventoSerializer(self.get_object()).data
        evento = serializer.save()
        log_user_action(self.request.user, f"Actualizó el evento: {evento.nombre}")
        # Llama a la tarea de forma asíncrona con los datos antiguos
        enviar_evento_actualizado_email.delay(evento.id, old_data) 

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó el evento: {instance.nombre}")
        super().perform_destroy(instance)
