from django.shortcuts import render
from django.views import generic
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.response import Response
from .models import *
from .serializers import *
from core.permissions import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
User = get_user_model()


class FriendRequestView(APIView):
    def get(self, request):
        req = FriendRequest.objects.filter(receiver=request.user)
        if not req:
            return Response({'success': False, 'log': 'No Friend request found'}, status=404)
        serializer = FriendRequestSerializer(req, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        try:    
            req,_ = FriendRequest.objects.get_or_create(receiver=request.user, sender=User.objects.get(id=request.query_params.get('user')))
            if not _:
                return Response({'success': False, 'log': 'Friend request already sent'}, status=400)

            if req.status == 'accepted':
                return Response({'success': False, 'log': 'Friend request already accepted'}, status=400)

            req.status = 'pending'
            req.save()
            return Response({'success': True, 'log': 'Friend request sent'}, status=201)
        except Exception as e:
            return Response({'success': False, 'log': f'Friend request sent failed {e}'}, status=400)
    
    def delete(self, request):
        req = FriendRequest.objects.filter(id=request.query_params.get('id')).first()
        if not req:
            return Response({'success': False, 'log': 'Friend request not found'})
        req.delete()
        return Response({'success': True, 'log': 'Friend request deleted'})


class FriendView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        friends, _ = Friends.objects.get_or_create(user=request.user)
        serializer = FreiendSerializer(friends)
        return Response(serializer.data)

    def post(self, request):
        req = FriendRequest.objects.filter(id=request.query_params.get('id'), receiver=request.user).first()
        if not req:
            return Response({'success': False, 'log': 'Friend request not found'})
        if req.status == 'pending':
            req.status = 'accepted'
            req.save()
            obj,_ = Friends.objects.get_or_create(user=request.user)
            obj.friends.add(req.sender)
            obj,_ = Friends.objects.get_or_create(user=req.sender)
            obj.friends.add(request.user)
            return Response({'success': True, 'log': 'Friend request accepted'})
        return Response({'success': False, 'log': 'Friend request already accepted'})
        
    def delete(self, request):
        req = Friends.objects.filter(user=request.user).first()
        friend_id = request.query_params.get('user')
        friend = User.objects.filter(id=friend_id).first()
        if not friend:
            return Response({'success': False, 'log': 'Friend not found'})
        req.friends.remove(friend)
        return Response({'success': True, 'log': 'Friend removed'})


class GroupView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]
    
    def get(self, request):
        groups = Group.objects.filter(admin=request.user)
        serializer = GroupSerializer(groups, many=True)
        return Response({'success': True, 'log': serializer.data}, status=200)
    
    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(admin=request.user, members=[request.user])
            return Response({'success': True, 'log': serializer.data}, status=201)
        return Response({'success': False, 'log': serializer.errors }, status=400)

    def delete(self, request):
        group = Group.objects.filter(id=request.query_params.get('id')).first()
        if not group:
            return Response({'success': False, 'log': 'Group not found'})
        self.check_object_permissions(request, group)
        group.delete()
        return Response({'success': True, 'log': 'Group deleted'})

    def patch(self, request):
        group = Group.objects.filter(id=request.query_params.get('id')).first()
        if not group:
            return Response({'success': False, 'log': 'Group not found'}, status=404)
        self.check_object_permissions(request, group)
        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'log': serializer.data}, status=200)
        return Response({'success': False, 'log': serializer.errors }, status=400)


class GroupMemberView(APIView):
    permission_classes = [IsAuthenticated,IsGroupAdmin]
    
    def post(self, request, action):
        group = Group.objects.filter(id=request.query_params.get('id')).first()
        serializer = GroupSerializer(group)
        if not group:
            return Response({'success': False, 'log': 'Group not found'}, status=404)
        
        self.check_object_permissions(request, group)

        members = request.data.get('user',[])
        if action == 'add':
            group.members.add(*members)
            return Response({'success': True, 'log': serializer.data}, status=200)

        elif action == 'del':
            group.members.remove(*members)

            return Response({'success': True, 'log': serializer.data}, status=200)
        
        return Response({'success': False, 'log': 'Invalid action. Use add or del'}, status=400)

