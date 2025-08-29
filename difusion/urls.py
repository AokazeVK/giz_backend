# apps/difusion/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MinisterioViewSet, EncargadoViewSet

# Crea un router y registra tus ViewSets
router = DefaultRouter()
router.register(r'ministerios', MinisterioViewSet, basename='ministerios')
router.register(r'encargados', EncargadoViewSet, basename='encargados')

# Las URL generadas por el router se incluyen automáticamente
urlpatterns = [
    path('', include(router.urls)),
]
