# giz_backend/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "giz_backend.settings")

# Primero define la aplicación HTTP para inicializar Django
django_asgi_app = get_asgi_application()

# IMPORTA EL MIDDLEWARE DESPUÉS de que Django ya está listo
from comunidad.middleware import JwtAuthMiddleware
import comunidad.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddleware(
        URLRouter(
            comunidad.routing.websocket_urlpatterns
        )
    ),
})
