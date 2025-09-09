# giz_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView # <-- ¡Nuevas importaciones!
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("accounts.urls")),  # Incluye las URLs de tu app 'accounts'
    path("api/difusion/", include("difusion.urls")),
    path("api/cursos/", include("cursos.urls")),
    path("api/preparacion/", include("preparacion.urls")),
    path("api/requisitos/", include("requisitos.urls")),
    path('', include('comunidad.urls')),
    path("api/reconocimiento/", include("reconocimiento.urls")),
    
    
     # Endpoint para generar el esquema de la API en formato YAML/JSON
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Endpoint para la interfaz de Swagger UI (la visualización interactiva)
    path("api/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)