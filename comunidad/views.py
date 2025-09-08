from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Post, Comment, ChatRoom, Message
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.db.models import Count
from .serializers import (
    PostSerializer, CommentSerializer, ChatRoomSerializer,
    MessageSerializer, UserSerializer
)

# Get the custom user model once
User = get_user_model()

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)

        # Send real-time update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'posts_updates',
            {
                'type': 'post_update',
                'action': 'created',
                'post': PostSerializer(post).data
            }
        )

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)

        if serializer.is_valid():
            comment = serializer.save(author=request.user, post=post)

            # Send real-time update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "posts_updates",
                {
                    "type": "comment_update",
                    "action": "created",
                    "comment": {
                        "id": comment.id,
                        "content": comment.content,
                        "created_at": comment.created_at.isoformat(),
                        "post": post.id,
                        "author": {
                            "id": comment.author.id,
                            "username": comment.author.username,
                            "avatar": comment.author.avatar.url if comment.author.avatar else None,
                        },
                    },
                },
            )

            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def upload_image(self, request):
        if 'image' not in request.FILES:
            return Response({'error': 'No image provided'}, status=400)
        
        image = request.FILES['image']
        # Save image and return URL
        filename = default_storage.save(f'temp/{image.name}', ContentFile(image.read()))
        image_url = default_storage.url(filename)
        
        return Response({'image_url': image_url})


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)

    @action(detail=False, methods=['post'])
    def create_or_get_room(self, request):
        participant_id = request.data.get('participant_id')

        try:
            participant = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if a room exists with exactly these 2 participants
        room = ChatRoom.objects.filter(
            participants=request.user
        ).filter(
            participants=participant
        ).distinct().first()

        if not room:
            room = ChatRoom.objects.create()
            room.participants.add(request.user, participant)

        serializer = self.get_serializer(room)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def online_users(self, request):
        # Filtra directamente el campo is_online del modelo User
        online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)
        serializer = self.get_serializer(online_users, many=True)
        return Response(serializer.data)
    

