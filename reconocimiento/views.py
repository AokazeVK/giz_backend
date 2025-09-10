from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasPermissionMap
from accounts.utils import log_user_action
from .models import Evento
from .serializers import EventoSerializer
from .task import enviar_evento_email, enviar_evento_actualizado_email

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

    def get_queryset(self):
        """
        Filtra los eventos por gestión usando la cookie 'gestion'.
        Solo devuelve el evento de la gestión actual (si existe).
        """
        gestion = self.request.COOKIES.get("gestion")
        return Evento.objects.filter(gestion=gestion)  # Asume que agregas campo 'gestion' al modelo

    def perform_create(self, serializer):
        gestion = self.request.COOKIES.get("gestion")
        if Evento.objects.filter(gestion=gestion).exists():
            return Response(
                {"error": "Ya existe un evento para esta gestión"},
                status=status.HTTP_400_BAD_REQUEST
            )

        evento = serializer.save(gestion=gestion)  # Guarda también la gestión
        log_user_action(self.request.user, f"Creó el evento: {evento.nombre}")
        enviar_evento_email.delay(evento.id)

    def perform_update(self, serializer):
        old_data = EventoSerializer(self.get_object()).data
        evento = serializer.save()
        log_user_action(self.request.user, f"Actualizó el evento: {evento.nombre}")
        enviar_evento_actualizado_email.delay(evento.id, old_data)

    def perform_destroy(self, instance):
        log_user_action(self.request.user, f"Eliminó el evento: {instance.nombre}")
        super().perform_destroy(instance)
