# apps/your_app/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email_notification(subject, template_name, context, recipient_list):
    """
    Función de utilidad para enviar un correo electrónico con una plantilla.
    """
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Correo enviado exitosamente a: {recipient_list}")
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False