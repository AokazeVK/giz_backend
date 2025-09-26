# apps/requisitos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EnlacesViewSet,
    EvaluacionDatoViewSet,
    RequisitoInputValorViewSet,
    TipoSelloViewSet, 
    RequisitoViewSet, 
    RequisitoInputViewSet, 
    ChecklistEvaluacionViewSet, 
    EvaluacionViewSet,
    EvaluacionFasesViewSet  # Importa la nueva vista
)

# Crea un router y registra tus ViewSets
router = DefaultRouter()
router.register(r'tipos-sello', TipoSelloViewSet, basename='tipos-sello')
router.register(r'requisitos', RequisitoViewSet, basename='requisitos')
router.register(r'requisitos-input', RequisitoInputViewSet, basename='requisitos-input')
router.register(r'checklist-evaluacion', ChecklistEvaluacionViewSet, basename='checklist-evaluacion')
router.register(r'evaluaciones', EvaluacionViewSet, basename='evaluaciones')
router.register(r'evaluacion-fases', EvaluacionFasesViewSet, basename='evaluacion-fases')  # Nueva ruta
router.register(r'requisitos-valores', RequisitoInputValorViewSet, basename='requisitos-valores')  # Nueva ruta
router.register(r'evaluacion-dato', EvaluacionDatoViewSet, basename='evaluacion-dato')  # Nueva ruta
router.register(r'enlaces', EnlacesViewSet, basename='enlaces')  # Nueva ruta

# Las URL generadas por el router se incluyen en tu URL principal
urlpatterns = [
    path('', include(router.urls)),
]