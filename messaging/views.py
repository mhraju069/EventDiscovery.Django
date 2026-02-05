from .models import *
from .serializers import *
import json
from social.models import Group
from rest_framework import status
from .helper import get_chat_name
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView,RetrieveAPIView
from core.pagination import paginate_response,MyCursorPagination,CustomLimitPagination
from core.permissions import IsEventAdmin,IsGroupAdmin,IsChatMember
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Create your views here.

class CreatePrivateChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        recipient_id = self.request.query_params.get('id')
        if not recipient_id:
            return Response({"status": False, "log": "Recipient id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if str(request.user.id) == str(recipient_id):
            return Response({"status": False, "log": "You cannot chat with yourself"}, status=status.HTTP_400_BAD_REQUEST)

        recipient = User.objects.filter(id=recipient_id).first()
        if not recipient:
            return Response({"status": False, "log": "Recipient not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if a private chat already exists between these two users
        room = ChatRoom.objects.filter(type="private", members=request.user).filter(members=recipient).first()

        if not room:
            room = ChatRoom.objects.create(type="private", name=get_chat_name(request.user,recipient))
            room.members.add(request.user, recipient)
            room.save()

        return Response({"status": True, "log": ChatRoomSerializer(room, context={'request': request}).data}, status=status.HTTP_200_OK)


class DeleteChatView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        room_id = self.request.query_params.get('id')
        if not room_id:
            return Response({"status": False, "log": "Chat id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        room = ChatRoom.objects.filter(id=room_id).first()
        if not room:
            return Response({"status": False, "log": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user not in room.members.all():
            return Response({"status": False, "log": "You are not a member of this chat"}, status=status.HTTP_400_BAD_REQUEST)
        
        if room.type == "private":  
            room.delete()

        else:
            if request.user != room.admin:
                return Response({"status": False, "log": "You don't have permission to delete this chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.delete()
            
        return Response({"status": True, "log": "Chat deleted"}, status=status.HTTP_200_OK)


class SendFileMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id = request.data.get('room_id')
        content = request.data.get('content', '')
        reply_of_id = request.data.get('reply_of_id')
        files = request.FILES.getlist('files')
        
        if not room_id:
            return Response({"status": False, "log": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        room = ChatRoom.objects.filter(id=room_id, members=request.user).first()
        if not room:
            return Response({"status": False, "log": "Room not found or you are not a member"}, status=status.HTTP_404_NOT_FOUND)

        reply_of = None
        if reply_of_id:
            reply_of = Message.objects.filter(id=reply_of_id, room=room).first()

        messages_data = []
        
        def get_msg_type(f):
            name = f.name.lower()
            if name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                return "image"
            elif name.endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
                return "video"
            elif name.endswith(('.mp3', '.wav', '.aac', '.flac', '.ogg')):
                return "voice"
            return "file"

        if files:
            for i, file in enumerate(files):
                msg_type = get_msg_type(file)
                # Attach content only to the first message if multiple files
                msg_content = content if i == 0 else ""
                
                message_obj = Message.objects.create(
                    room=room,
                    sender=request.user,
                    type=msg_type,
                    content=msg_content,
                    file=file,
                    reply_of=reply_of
                )
                messages_data.append(MessageSerializer(message_obj, context={'request': request}).data)
        elif content:
            message_obj = Message.objects.create(
                room=room,
                sender=request.user,
                type="text",
                content=content,
                reply_of=reply_of
            )
            messages_data.append(MessageSerializer(message_obj, context={'request': request}).data)
        else:
             return Response({"status": False, "log": "Content or file is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Broadcast to WebSocket
        channel_layer = get_channel_layer()
        for msg_data in messages_data:
            message_json = json.dumps(msg_data, default=str)
            message_dict = json.loads(message_json)
            async_to_sync(channel_layer.group_send)(
                f"chat_{room_id}",
                {
                    'type': 'chat_message',
                    'message': message_dict,
                    'sender': request.user.id
                }
            )

        # Trigger Notifications
        from notifications.helper import send_notification
        recipients = room.members.exclude(id=request.user.id)
        notification_title = f"New message from {request.user.name or request.user.email}"
        if room.type == "group":
            notification_title = f"New message in {room.name or 'Group'}"
        elif room.type == "event":
            notification_title = f"Event update: {room.name or 'Event'}"

        # Get summary for notification
        if len(messages_data) > 1:
            notification_message = f"Sent {len(messages_data)} files"
        else:
            msg = messages_data[0]
            notification_message = msg.get('content')[:100] if msg.get('content') else f"Sent a {msg.get('type')}"

        for recipient in recipients:
            send_notification(
                user=recipient,
                title=notification_title,
                message=notification_message,
                notification_type='message'
            )

        return Response({"status": True, "log": messages_data}, status=status.HTTP_201_CREATED)


class CreateGroupChatView(APIView):
    permission_classes = [IsAuthenticated,IsGroupAdmin]

    def post(self, request):
        group_id = request.query_params.get('id')
        if not group_id:
            return Response({"status": False, "log": "Group id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        group = Group.objects.filter(id=group_id).first()

        if not group:
            return Response({"status": False, "log": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, group)

        room,_ = ChatRoom.objects.get_or_create(group=group, admin=request.user, type="group",defaults={"name": f'{group.name} Group'})
        if not _:
            return Response({"status": False, "log": "Group chat already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.add(*group.members.all())
        room.save()
        return Response({"status": True, "log": ChatRoomSerializer(room, context={'request': request}).data}, status=status.HTTP_201_CREATED)


class JoinGroupChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, action):
        group_id = request.query_params.get('id')
        if not group_id:
            return Response({"status": False, "log": "Group id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        group = Group.objects.filter(id=group_id).first()

        if not group:
            return Response({"status": False, "log": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        room= ChatRoom.objects.filter(group=group, type="group").first()

        if not room:
            return Response({"status": False, "log": "Group chat not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if action == "join":
            if request.user in room.members.all():
                return Response({"status": False, "log": "You are already in the group chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.members.add(request.user)
        elif action == "leave":
            if request.user not in room.members.all():
                return Response({"status": False, "log": "You are not in the group chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.members.remove(request.user)
        room.save()
        return Response({"status": True, "log": ChatRoomSerializer(room, context={'request': request}).data}, status=status.HTTP_201_CREATED)


class CreateEventChatView(APIView):
    permission_classes = [IsAuthenticated,IsEventAdmin]

    def post(self, request):
        event_id = request.query_params.get('id')
        if not event_id:
                return Response({"status": False, "log": "Event id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        event = Event.objects.filter(id=event_id).first()

        if not event:
            return Response({"status": False, "log": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, event)

        room,_ = ChatRoom.objects.get_or_create(event=event, admin=request.user, type="event",defaults={"name": f'{event.name} Event'})
        if not _:
            return Response({"status": False, "log": "Event chat already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.add(*event.members.all())
        room.save()
        return Response({"status": True, "log": ChatRoomSerializer(room, context={'request': request}).data}, status=status.HTTP_201_CREATED)


class GetRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        type = request.query_params.get('type', 'all')
        if type not in ["private","group","event","all"]:
            return Response({"status": False, "log": f"Invalid type {type}, possible values are private, group, event"}, status=status.HTTP_400_BAD_REQUEST)
        if type == "all":
            rooms = ChatRoom.objects.filter(members=request.user)
        else:
            rooms = ChatRoom.objects.filter(members=request.user, type=type)
            
        from django.db.models import Max
        rooms = rooms.annotate(last_message_at=Max('messages__created_at')).order_by('-last_message_at').distinct()
        
        return Response({"status": True, "log": ChatRoomSerializer(rooms, many=True, context={'request': request}).data}, status=status.HTTP_200_OK)


class GetRoomMessagesView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = MyCursorPagination
    def get_queryset(self):
        room = ChatRoom.objects.filter(id=self.kwargs['room']).first()
        if not room:
            return Response({"status": False, "log": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(self.request, room)
        messages = Message.objects.filter(room=room).order_by('-created_at')
        return messages


class GetRoomDetailsView(RetrieveAPIView):
    permission_classes = [IsAuthenticated,IsChatMember]
    serializer_class = ChatRoomDetailsSerializer
    def get_object(self):
        room = ChatRoom.objects.filter(id=self.kwargs['room']).first()
        if not room:
            return Response({"status": False, "log": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(self.request, room)
        return room