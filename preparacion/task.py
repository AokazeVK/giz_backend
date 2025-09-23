from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from accounts.models import User
from .models import SolicitudAsesoramiento


@shared_task
def enviar_solicitud_asesoramiento_email(solicitud_id):
    """
    Envía un correo a la empresa sobre el estado de su solicitud de asesoramiento.
    """
    try:
        solicitud = SolicitudAsesoramiento.objects.select_related(
            "empresa", "asesoramiento"
        ).get(id=solicitud_id)

        empresa = solicitud.empresa
        usuarios = User.objects.filter(empresa=empresa)

        subject = f"Solicitud de Asesoramiento: {solicitud.asesoramiento.nombre}"
        context = {
            "empresa": empresa,
            "solicitud": solicitud,
            "subject": subject,
            "year": timezone.now().year,
        }

        html_message = render_to_string(
            "emails/solicitud_asesoramiento.html", context
        )

        plain_message = (
            f"Estimado(a) representante de {empresa.nombre},\n\n"
            f"Su solicitud de asesoramiento '{solicitud.asesoramiento.nombre}' "
            f"ha sido {solicitud.estado}.\n"
        )

        if solicitud.estado == "APROBADO":
            plain_message += f"Fecha aprobada: {solicitud.fechaAprobada}\n\n"
        elif solicitud.estado == "RECHAZADO":
            plain_message += "Lamentamos informarle que su solicitud fue rechazada.\n\n"

        for usuario in usuarios:
            if usuario.email:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    html_message=html_message,
                    fail_silently=False,
                )

    except SolicitudAsesoramiento.DoesNotExist:
        print(f"Solicitud {solicitud_id} no encontrada.")
