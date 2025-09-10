from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from accounts.models import User
from .models import Evento
from django.contrib.sites.models import Site # 👈 Importación necesaria

@shared_task
def enviar_evento_email(evento_id):
    """
    Envía un correo de invitación a un evento a todos los usuarios
    que pertenecen a una empresa aprobada, usando un template HTML.
    """
    try:
        evento = Evento.objects.get(id=evento_id)
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        # 👈 Obtener la URL absoluta de la imagen para el correo
        imagen_url = None
        if evento.imagen:
            current_site = Site.objects.get_current()
            imagen_url = f"{base_url}{evento.imagen.url}"

        usuarios = User.objects.filter(
            empresa__isnull=False,
            empresa__isAproved=True
        ).select_related('empresa__tipoSello')
        
        for usuario in usuarios:
            empresa = usuario.empresa
            
            subject = f"Invitación al evento de reconocimiento: {evento.nombre}"
            
            # Crea el contexto para el template HTML
            context = {
                'subject': subject,
                'evento': evento,
                'empresa': empresa,
                'intro_message': "Nos complace invitarlo(a) a nuestro evento especial.",
                'year': timezone.now().year,
                'is_update': False, # Indica que no es un correo de actualización
                'imagen_url': imagen_url, # 👈 Agregamos la URL de la imagen al contexto
            }

            html_message = render_to_string('emails/invitacion_evento.html', context)
            plain_message = (
                f"Estimado(a) representante de la empresa {empresa.nombre},\n\n"
                f"Nos complace invitarlo(a) a nuestro evento especial.\n\n"
                f"Detalles del Evento:\n"
                f"Nombre del Evento: {evento.nombre}\n"
                f"Descripción: {evento.descripcion}\n"
                f"Lugar: {evento.lugar}\n"
                f"Fecha y Hora: {evento.fecha}\n\n"
            )
            
            if usuario.email:
                destinatarios = [usuario.email]
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    html_message=html_message,
                    fail_silently=False,
                )
    except Evento.DoesNotExist:
        print(f"Evento con ID {evento_id} no encontrado.")


@shared_task
def enviar_evento_actualizado_email(evento_id, datos_antiguos):
    """
    Envía un correo de actualización a los usuarios de empresas aprobadas,
    usando un template HTML.
    """
    try:
        evento = Evento.objects.get(id=evento_id)
        
        # 👈 Obtener la URL absoluta de la imagen para el correo de actualización
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        # 👈 Obtener la URL absoluta de la imagen para el correo
        imagen_url = None
        if evento.imagen:
            current_site = Site.objects.get_current()
            imagen_url = f"{base_url}{evento.imagen.url}"
        
        usuarios = User.objects.filter(
            empresa__isnull=False,
            empresa__isAproved=True
        ).select_related('empresa__tipoSello')
        
        subject = f"Actualización sobre el evento: {evento.nombre}"
        
        # Crea el contexto para el template HTML de actualización
        context = {
            'subject': subject,
            'evento': evento,
            'intro_message': "El evento ha sido modificado. A continuación, los detalles actualizados:",
            'year': timezone.now().year,
            'is_update': True, # Indica que es un correo de actualización
            'datos_antiguos': datos_antiguos,
            'imagen_url': imagen_url, # 👈 Agregamos la URL de la imagen al contexto
        }

        html_message = render_to_string('emails/invitacion_evento.html', context)
        
        plain_message = (
            f"Hola,\n\n"
            f"El evento '{datos_antiguos.get('nombre', 'N/A')}' ha sido modificado.\n\n"
            f"Consulta los nuevos detalles en el correo HTML."
        )

        for usuario in usuarios:
            if usuario.email:
                destinatarios = [usuario.email]
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    destinatarios,
                    html_message=html_message,
                    fail_silently=False,
                )
    except Evento.DoesNotExist:
        print(f"Evento con ID {evento_id} no encontrado.")
