# apps/difusion/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MinisterioViewSet, EncargadoViewSet, ConvocatoriaViewSet, FechaConvocatoriaViewSet, ArchivoFechaConvocatoriaViewSet

# Crea un router y registra tus ViewSets
router = DefaultRouter()
router.register(r'ministerios', MinisterioViewSet, basename='ministerios')
router.register(r'encargados', EncargadoViewSet, basename='encargados')
router.register(r'convocatorias', ConvocatoriaViewSet, basename="convocatorias")
router.register(r'fechas', FechaConvocatoriaViewSet, basename="fechas_convocatoria")
router.register(r'archivos', ArchivoFechaConvocatoriaViewSet, basename="archivos_fechas")

# Las URL generadas por el router se incluyen automáticamente
urlpatterns = [
    path('', include(router.urls)),
]
