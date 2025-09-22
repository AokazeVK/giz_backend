from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import DashboardViewSet
from .views import DepartamentoViewSet

# Creamos un router específico para la app de dashboard
router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Las URLs de la app de dashboard se crean a partir del router
urlpatterns = [
    path('', include(router.urls)),
]
