import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatRoom, Message, Post, Comment
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
       
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type")

        if message_type == "chat_message":
            await self.handle_chat_message(text_data_json)
        elif message_type == "typing":
            await self.handle_typing(text_data_json)

    async def handle_chat_message(self, data):
        message_content = data["message"]
        user = self.scope["user"]

        # Save message to database
        message = await self.save_message(user, self.room_id, message_content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "sender": {
                        "id": user.id,
                        "username": user.username,
                        "avatar": user.avatar.url if user.avatar else None, # Aquí ya está bien
                    },
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def handle_typing(self, data):
        user = self.scope["user"]
        is_typing = data.get("is_typing", False)
        print(is_typing)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_status",
                "user": {"id": user.id, "username": user.username},
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "chat_message", "message": event["message"]})
        )

    async def typing_status(self, event):
        # Send typing status to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing_status",
                    "user": event["user"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, user, room_id, content):
        room = ChatRoom.objects.get(id=room_id)
        return Message.objects.create(room=room, sender=user, content=content)


class PostConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "posts_updates"

        # Join posts group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave posts group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def post_update(self, event):
        # Send post update to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "post_update",
                    "action": event["action"],
                    "post": event["post"],
                }
            )
        )

    async def comment_update(self, event):
        # Send comment update to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "comment_update",
                    "action": event["action"],
                    "comment": event["comment"],
                }
            )
        )

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.update_user_online_status(user, True)

            # Join al grupo general
            await self.channel_layer.group_add("online_users", self.channel_name)

            # Avisar a todos que este user se conectó
            await self.channel_layer.group_send(
                "online_users",
                {
                    "type": "user_status",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "avatar": user.avatar.url if hasattr(user, "avatar") and user.avatar else None,
                        "is_online": True,
                    },
                },
            )

        await self.accept()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.update_user_online_status(user, False)

            # Salir del grupo
            await self.channel_layer.group_discard("online_users", self.channel_name)

            # Avisar que se desconectó
            await self.channel_layer.group_send(
                "online_users",
                {
                    "type": "user_status",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "avatar": user.avatar.url if hasattr(user, "avatar") and user.avatar else None,
                        "is_online": False,
                    },
                },
            )

    async def user_status(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "user_status",
                "user": event["user"],
            })
        )

    @database_sync_to_async
    def update_user_online_status(self, user, is_online):
        user.is_online = is_online
        user.save(update_fields=["is_online"])
