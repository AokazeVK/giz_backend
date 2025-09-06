from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet)
router.register(r'chat-rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]