from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventoViewSet

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='eventos')

urlpatterns = [
    # Las URLs generadas por el router, como /api/reconocimiento/
    path('', include(router.urls)),
]
