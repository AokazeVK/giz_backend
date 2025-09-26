from rest_framework.routers import DefaultRouter
from .views import ArchivoAsesoramientoViewSet, AsesoramientoViewSet, EmpresaViewSet, EncargadoAsesoramientoViewSet, PublicacionEmpresaComunidadViewSet, SolicitudAsesoramientoViewSet

router = DefaultRouter()
router.register(r"empresas", EmpresaViewSet, basename="empresa")
router.register(r"publicaciones-comunidad", PublicacionEmpresaComunidadViewSet, basename="publicacion-comunidad")
router.register(r"solicitud-asesoramiento", SolicitudAsesoramientoViewSet, basename="solicitud-asesoramiento")
router.register(r"asesoramiento", AsesoramientoViewSet, basename="asesoramiento")
router.register(r"asesoramiento-archivos", ArchivoAsesoramientoViewSet, basename="asesoramiento-archivos")
router.register(r"asesoramiento-encargados", EncargadoAsesoramientoViewSet, basename="asesoramiento-encargados")
urlpatterns = router.urls
