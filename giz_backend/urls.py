# giz_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView # <-- ¡Nuevas importaciones!


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("accounts.urls")),  # Incluye las URLs de tu app 'accounts'
    # Si tienes otra app, por ejemplo 'posts', la agregas aquí:
    # path("api/posts/", include("posts.urls")),
    
     # Endpoint para generar el esquema de la API en formato YAML/JSON
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Endpoint para la interfaz de Swagger UI (la visualización interactiva)
    path("api/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]