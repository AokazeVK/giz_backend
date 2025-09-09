from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReconocimientoViewSet

router = DefaultRouter()
router.register(r'', ReconocimientoViewSet, basename='reconocimiento')

urlpatterns = [
    # Las URLs generadas por el router, como /api/reconocimiento/
    path('', include(router.urls)),
]
