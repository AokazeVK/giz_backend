# apps/requisitos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoSelloViewSet, 
    RequisitoViewSet, 
    RequisitoInputViewSet,  # Vuelve a importar la clase
    ChecklistEvaluacionViewSet, 
    EvaluacionViewSet
)

# Crea un router y registra tus ViewSets
router = DefaultRouter()
router.register(r'tipos-sello', TipoSelloViewSet, basename='tipos-sello')
router.register(r'requisitos', RequisitoViewSet, basename='requisitos')
router.register(r'requisitos-input', RequisitoInputViewSet, basename='requisitos-input') # Vuelve a registrar el ViewSet
router.register(r'checklist-evaluacion', ChecklistEvaluacionViewSet, basename='checklist-evaluacion')
router.register(r'evaluaciones', EvaluacionViewSet, basename='evaluaciones')

# Las URL generadas por el router se incluyen en tu URL principal
urlpatterns = [
    path('', include(router.urls)),
]