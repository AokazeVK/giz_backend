from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login_view,
    logout_view,
    refresh_token_view,
    profile_view,
    public_view,
    RoleViewSet,
    UserViewSet
)

# Crea un router para los ViewSets
router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    # Endpoints existentes
    path("login/", login_view),
    path("logout/", logout_view),
    path("refresh/", refresh_token_view),
    path("profile/", profile_view),
    path("public/", public_view),

    # Endpoints CRUD
    path("", include(router.urls)),
]
