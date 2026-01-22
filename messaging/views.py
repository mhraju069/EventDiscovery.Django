from .models import *
from .serializers import *
from social.models import Group
from rest_framework import status
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from core.pagination import CustomLimitPagination
from core.permissions import IsEventAdmin,IsGroupAdmin
from rest_framework.permissions import IsAuthenticated
# Create your views here.


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
    pagination_class = CustomLimitPagination
    def get_queryset(self):
        room = ChatRoom.objects.filter(id=self.kwargs['room']).first()
        if not room:
            return Response({"success": False, "log": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(self.request, room)
        messages = Message.objects.filter(room=room).order_by('-created_at')
        return messages