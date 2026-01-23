import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from .models import *
from .serializers import MessageSerializer
from rest_framework_simplejwt.tokens import AccessToken
User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except Exception as e:
        print(f"❌ Token Error: {e}")
        return None


class GlobalChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            token = self.scope['query_string'].decode().split('token=')[-1]
            self.user = await get_user_from_token(token)
            
            if not self.user:
                await self.close()
                return
            
            self.room_id = self.scope['url_route']['kwargs'].get('room_id')
            if self.room_id:
                self.room = await self.get_room(self.room_id)
                if not self.room:
                    await self.close()
                    return
                
                self.room_group_name = f"chat_{self.room_id}"
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            
            self.groups = [f"user_{self.user.id}"]
            await self.channel_layer.group_add(f"user_{self.user.id}", self.channel_name)

            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'Websocket Connected',
                'message': f"Successfully connected for {self.user.email}"
            }))
            print(f"✅ Websocket Connection Established for {self.user.email}")

        except Exception as e:
            print(f"❌ Connection Error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        for group_name in self.groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)

        await self.send(text_data=json.dumps({
            'type': 'Websocket Disconnected',
            'message': f"Disconnected for {self.user.email}"
        }))
        print(f"✅ Websocket Disconnected for {self.user.email}")

    async def receive(self, text_data):
        """
        Receive message from user and broadcast to room
        """
        try:
            data = json.loads(text_data)
            type = data.get('type', 'text')
            content = data.get('content', '')

            # Save message to DB
            message_obj = await self.save_message(self.room, self.user, type, content)

            # Use Serializer to get consistent data format
            message_data = await sync_to_async(lambda: MessageSerializer(message_obj).data)()
            
            # Since we don't have a 'request' in scope to get absolute URLs automatically, 
            # we manually handle the file path if it exists
            if message_data.get('file'):
                # In production, you'd use a setting for the domain
                domain = self.scope.get('headers', {}).get(b'host', b'localhost:8000').decode()
                scheme = 'https' if self.scope.get('https') else 'http'
                message_data['file'] = f"{scheme}://{domain}{message_data['file']}"

            # Send to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',  # calls chat_message()
                    'message': message_data
                }
            )
        except Exception as e:
            print(f"❌ Error in receive: {e}")

    # ---------------------------
    # Receive message from room group
    # ---------------------------
    
    async def chat_message(self, event):
        message = event.get('message')
        if not message:
            return
        
        # Safe lookup for sender ID (could be 'sender' from serializer or 'sender' from receive)
        sender_id = message.get('sender')
        
        if str(self.user.id) == str(sender_id):
            return
            
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    # ---------------------------
    # Helper functions
    # ---------------------------
    @database_sync_to_async
    def save_message(self, room, sender, message_type, content):
        return Message.objects.create(
            room=room,
            sender=sender,
            type=message_type,
            content=content
        )

    @database_sync_to_async
    def get_room(self, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id,members=self.user)
            return room
        except ChatRoom.DoesNotExist:
            return None
