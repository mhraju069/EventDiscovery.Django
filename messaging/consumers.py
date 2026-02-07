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
from django.db.models import Q
import uuid

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except Exception as e:
        print(f"❌ Token Error: {e}")
        return None


class GlobalSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = self.scope['query_string'].decode().split('token=')[-1]
        self.user = await get_user_from_token(token)
        
        if not self.user:
            await self.close()
            return

        self.room_group_name = 'global_socket'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.user_status(self.user, True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.user_status(self.user, False)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'global_message',
                'message': data['message']
            }
        )

    async def global_message(self, event):
        await self.send(text_data=json.dumps(event))
    

    
    @database_sync_to_async
    def user_status(self, user, active=False):
        try:
            obj, created = ChatInfo.objects.get_or_create(user=user)
            obj.active = active
            if not active:
                obj.last_active = timezone.now()
            else:
                obj.last_active = None
            obj.save()
            return obj
        except Exception as e:
            print(f"❌ User status update failed: {e}")
            return None


class ChatConsumer(AsyncWebsocketConsumer):


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
        
        if hasattr(self, 'groups'):
            for group_name in self.groups:
                await self.channel_layer.group_discard(group_name, self.channel_name)

        print(f"✅ Websocket Disconnected for {getattr(self.user, 'email', 'Unknown User')}")


    async def receive(self, text_data):

        try:
            print(f"📥 Received data: {text_data}")
            data = json.loads(text_data)
            
            action_type = data.get('type', 'chat_message')
            
            msg_type = data.get('message_type', 'text')
            if msg_type not in ['text', 'image', 'file', 'voice', 'video']:
                msg_type = 'text'
                
            content = data.get('content', '')

            if not self.room:
                print("❌ No room associated with this connection")
                return

            message_obj = await self.save_message(self.room, self.user, msg_type, content)
            print(f"💾 Message saved to DB: {message_obj.id}")

            message_data = await sync_to_async(lambda: MessageSerializer(message_obj).data)()
            
            message_data = json.loads(json.dumps(message_data, default=str))

            if message_data.get('file'):
                headers = dict(self.scope.get('headers', []))
                domain = headers.get(b'host', b'localhost:8000').decode()
                scheme = 'https' if self.scope.get('https') else 'http'
                message_data['file'] = f"{scheme}://{domain}{message_data['file']}"

            print(f"📡 Broadcasting to group: {self.room_group_name}")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', 
                    'message': message_data
                }
            )

        except Exception as e:
            print(f"❌ Error in receive: {e}")
            import traceback
            traceback.print_exc()


    async def chat_message(self, event):
        message = event.get('message')
        if not message:
            return
        
        sender_id = message.get('sender')
        
        if str(self.user.id) == str(sender_id):
            return
            
        print(f"📤 Sending message to user {self.user.email} in room {self.room_id}")
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }, default=str))


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
            query_filter = Q(members=self.user)
            
            room_lookup = Q()
            
            is_uuid = False
            try:
                uuid.UUID(str(room_id))
                is_uuid = True
                room_lookup |= Q(id=room_id)
            except (ValueError, TypeError):
                pass
                
            if str(room_id).isdigit():
                room_lookup |= Q(group_id=room_id) | Q(event_id=room_id)
            
            if not room_lookup:
                print(f"⚠️ Invalid room_id format: {room_id}")
                return None
                
            room = ChatRoom.objects.filter(query_filter & room_lookup).first()
            return room
        except Exception as e:
            print(f"❌ Room lookup failed for room_id: {room_id}. Error: {e}")
            return None


        try:
            obj, created = ChatInfo.objects.get_or_create(user=user)
            obj.active = active
            obj.active_at = timezone.now()
            obj.save()
            return obj
        except ChatInfo.DoesNotExist:
            return None