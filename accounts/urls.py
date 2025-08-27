# apps/accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login_view, logout_view, refresh_token_view, profile_view, public_view,
    RoleViewSet, UserViewSet, permissions_tree, LogsView
)

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="roles")
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    # Auth
    path("login/", login_view),
    path("logout/", logout_view),
    path("refresh/", refresh_token_view),
    path("profile/", profile_view),
    path("public/", public_view),

    # Permisos
    path("permissions/tree/", permissions_tree),

    # Logs globales
    path("logs/", LogsView.as_view()),

    # CRUDs
    path("", include(router.urls)),
]
