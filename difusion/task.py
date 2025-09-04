from celery import shared_task
from django.conf import settings # Importar settings
from .models import FechaConvocatoria, Encargado, ArchivoFechaConvocatoria
from .serializers import ArchivoFechaConvocatoriaSerializer
from .utils import send_email_notification

@shared_task
def enviar_convocatoria_email(fecha_id):
    try:
        fecha_convocatoria = FechaConvocatoria.objects.get(id=fecha_id)
        encargados = Encargado.objects.filter(is_active=True)

        if not encargados.exists():
            return "No hay encargados para notificar."

        recipient_list = [encargado.correo for encargado in encargados]
        archivos_qs = ArchivoFechaConvocatoria.objects.filter(fecha_convocatoria=fecha_convocatoria)

        # Aquí solo debe ir el código corregido.
        base_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000/'

        archivos_data = ArchivoFechaConvocatoriaSerializer(
            archivos_qs,
            many=True,
            context={"base_url": base_url}
        ).data

        context = {
            "convocatoria": fecha_convocatoria.convocatoria,
            "fecha_convocatoria": fecha_convocatoria,
            "convocatoria_archivos": archivos_data,
            "encargado_nombre": "Estimado(a) Encargado(a)",
        }

        subject = f"Inicio Convocatoria: {fecha_convocatoria.convocatoria.nombre}"

        send_email_notification(subject, "emails/convocatoria_notification.html", context, recipient_list)
        return f"Correo enviado para convocatoria {fecha_convocatoria.convocatoria.nombre}"

    except FechaConvocatoria.DoesNotExist:
        return f"FechaConvocatoria {fecha_id} no existe."