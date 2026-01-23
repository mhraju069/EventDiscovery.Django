from .models import *
from .serializers import *
import json
from social.models import Group
from rest_framework import status
from .helper import get_chat_name
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from core.pagination import CustomLimitPagination,MyCursorPagination
from core.permissions import IsEventAdmin,IsGroupAdmin
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Create your views here.

class CreatePrivateChatView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        recipient_id = self.request.query_params.get('id')
        if not recipient_id:
            return Response({"success": False, "log": "Recipient id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if str(request.user.id) == str(recipient_id):
            return Response({"success": False, "log": "You cannot chat with yourself"}, status=status.HTTP_400_BAD_REQUEST)

        recipient = User.objects.filter(id=recipient_id).first()
        if not recipient:
            return Response({"success": False, "log": "Recipient not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if a private chat already exists between these two users
        room = ChatRoom.objects.filter(type="private", members=request.user).filter(members=recipient).first()

        if not room:
            room = ChatRoom.objects.create(type="private", name=get_chat_name(request.user,recipient))
            room.members.add(request.user, recipient)
            room.save()

        return Response({"success": True, "log": ChatRoomSerializer(room).data}, status=status.HTTP_200_OK)


class DeleteChatView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        room_id = self.request.query_params.get('id')
        if not room_id:
            return Response({"success": False, "log": "Chat id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        room = ChatRoom.objects.filter(id=room_id).first()
        if not room:
            return Response({"success": False, "log": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user not in room.members.all():
            return Response({"success": False, "log": "You are not a member of this chat"}, status=status.HTTP_400_BAD_REQUEST)
        
        if room.type == "private":  
            room.delete()

        else:
            if request.user != room.admin:
                return Response({"success": False, "log": "You don't have permission to delete this chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.delete()
            
        return Response({"success": True, "log": "Chat deleted"}, status=status.HTTP_200_OK)


class SendFileMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id = request.data.get('room_id')
        msg_type = request.data.get('type', 'file')
        content = request.data.get('content', '')
        file = request.FILES.get('file')

        if not room_id:
            return Response({"success": False, "log": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        room = ChatRoom.objects.filter(id=room_id, members=request.user).first()
        if not room:
            return Response({"success": False, "log": "Room not found or you are not a member"}, status=status.HTTP_404_NOT_FOUND)

        # Save message to DB
        message_obj = Message.objects.create(
            room=room,
            sender=request.user,
            type=msg_type,
            content=content,
            file=file
        )

        message_data = MessageSerializer(message_obj, context={'request': request}).data
        
        # Convert message_data to a serializable format (handle UUIDs, datetime, etc.)
        message_json = json.dumps(message_data, default=str)
        message_dict = json.loads(message_json)

        # Broadcast to WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_id}",
            {
                'type': 'chat_message',
                'message': message_dict
            }
        )

        return Response({"success": True, "log": message_data}, status=status.HTTP_201_CREATED)


class CreateGroupChatView(APIView):
    permission_classes = [IsAuthenticated,IsGroupAdmin]
    def post(self, request):
        group_id = request.query_params.get('id')
        if not group_id:
            return Response({"success": False, "log": "Group id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        group = Group.objects.filter(id=group_id).first()

        if not group:
            return Response({"success": False, "log": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, group)

        room,_ = ChatRoom.objects.get_or_create(group=group, admin=request.user, type="group",defaults={"name": f'{group.name} Group'})
        if not _:
            return Response({"success": False, "log": "Group chat already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.add(*group.members.all())
        room.save()
        return Response({"success": True, "log": ChatRoomSerializer(room).data}, status=status.HTTP_201_CREATED)


class JoinGroupChatView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, action):
        group_id = request.query_params.get('id')
        if not group_id:
            return Response({"success": False, "log": "Group id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        group = Group.objects.filter(id=group_id).first()

        if not group:
            return Response({"success": False, "log": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        room= ChatRoom.objects.filter(group=group, type="group").first()

        if not room:
            return Response({"success": False, "log": "Group chat not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if action == "join":
            if request.user in room.members.all():
                return Response({"success": False, "log": "You are already in the group chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.members.add(request.user)
        elif action == "leave":
            if request.user not in room.members.all():
                return Response({"success": False, "log": "You are not in the group chat"}, status=status.HTTP_400_BAD_REQUEST)
            room.members.remove(request.user)
        room.save()
        return Response({"success": True, "log": ChatRoomSerializer(room).data}, status=status.HTTP_201_CREATED)


class CreateEventChatView(APIView):
    permission_classes = [IsAuthenticated,IsEventAdmin]
    def post(self, request):
        event_id = request.query_params.get('id')
        if not event_id:
            return Response({"success": False, "log": "Event id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        event = Event.objects.filter(id=event_id).first()

        if not event:
            return Response({"success": False, "log": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, event)

        room,_ = ChatRoom.objects.get_or_create(event=event, admin=request.user, type="event",defaults={"name": f'{event.name} Event'})
        if not _:
            return Response({"success": False, "log": "Event chat already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        room.members.add(*event.members.all())
        room.save()
        return Response({"success": True, "log": ChatRoomSerializer(room).data}, status=status.HTTP_201_CREATED)


class GetRoomListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,type=None):
        if type not in ["private","group","event"]:
            return Response({"success": False, "log": f"Invalid type {type}, possible values are private, group, event"}, status=status.HTTP_400_BAD_REQUEST)
        rooms = ChatRoom.objects.filter(members=request.user,type=type)
        return Response({"success": True,"type": type, "log": ChatRoomSerializer(rooms, many=True).data}, status=status.HTTP_200_OK)


class GetRoomMessagesView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = MyCursorPagination
    def get_queryset(self):
        room = ChatRoom.objects.filter(id=self.kwargs['room']).first()
        if not room:
            return Response({"success": False, "log": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(self.request, room)
        messages = Message.objects.filter(room=room).order_by('-created_at')
        return messages