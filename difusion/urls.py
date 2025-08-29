from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MinisterioViewSet, EncargadoViewSet

router = DefaultRouter()
router.register(r'ministerios', MinisterioViewSet, basename="ministerios")
router.register(r'encargados', EncargadoViewSet, basename="encargados")

urlpatterns = [
    path("", include(router.urls)),
]
