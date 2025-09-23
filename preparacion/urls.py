from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, PublicacionEmpresaComunidadViewSet

router = DefaultRouter()
router.register(r"empresas", EmpresaViewSet, basename="empresa")
router.register(r"publicaciones-comunidad", PublicacionEmpresaComunidadViewSet, basename="publicacion-comunidad")

urlpatterns = router.urls
