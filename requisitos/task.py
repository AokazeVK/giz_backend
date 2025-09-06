# apps/requisitos/tasks.py
from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Evaluacion, TipoSello
from accounts.models import User
from accounts.utils import log_user_action

@shared_task
def enviar_evaluacion_email(evaluacion_id, evaluadores_ids):
    """
    Tarea de Celery para enviar correos de notificación de evaluación.
    """
    try:
        evaluacion = Evaluacion.objects.get(id=evaluacion_id)
        evaluadores = User.objects.filter(id__in=evaluadores_ids)
        
        if not evaluadores.exists():
            log_user_action(None, f"Tarea de Celery: No hay evaluadores para notificar en la evaluación {evaluacion_id}")
            return "No hay destinatarios."

        # El contexto para la plantilla HTML
        context = {
            'evaluacion': evaluacion,
            'tiposello_nombre': evaluacion.tipoSello.nombre,
        }
        
        # Enviar un correo individual a cada evaluador
        for evaluador in evaluadores:
            personalized_context = context.copy()
            personalized_context['user_name'] = evaluador.username or evaluador.email
            
            html_content = render_to_string('emails/requisitos_notification.html', personalized_context)
            
            subject = f"Asignación de Evaluación: {evaluacion.tipoSello.nombre}"
            
            try:
                msg = EmailMessage(
                    subject,
                    html_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [evaluador.email]
                )
                msg.content_subtype = "html"  # Establece el tipo de contenido como HTML
                msg.send()
                log_user_action(None, f"Tarea de Celery: Correo enviado a {evaluador.email} para la evaluación {evaluacion_id}")
            except Exception as e:
                log_user_action(None, f"Tarea de Celery: Fallo al enviar correo a {evaluador.email}. Error: {e}")
        
        return "Notificación de evaluadores enviada exitosamente."
        
    except Evaluacion.DoesNotExist:
        log_user_action(None, f"Tarea de Celery: Evaluación con ID {evaluacion_id} no encontrada.")
        return "Evaluación no encontrada."