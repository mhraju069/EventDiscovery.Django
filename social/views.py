from django.shortcuts import render
from django.views import generic
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.response import Response
from .models import *
from .serializers import *


class FriendRequestView(APIView):
    def get(self, request):
        req = FriendRequest.objects.filter(user=request.user)
        if not req:
            return Response({'success': False, 'message': 'No Friend request found'}, status=404)
        serializer = FriendRequestSerializer(req, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = FriendRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user, user_id=request.query_params['user'])
            return Response({'success': True, 'message': 'Friend request sent'}, status=201)
        return Response({'success': False, 'message': 'Friend request sent failed'}, status=400)
    
    def delete(self, request):
        req = FriendRequest.objects.filter(id=request.query_params['id']).first()
        if not req:
            return Response({'success': False, 'message': 'Friend request not found'})
        req.delete()
        return Response({'success': True, 'message': 'Friend request deleted'})


class FriendView(APIView):
    def get(self, request):
        friends = Friends.objects.filter(user=request.user)
        serializer = FreiendSerializer(friends, many=True)
        return Response(serializer.data)

    def post(self, request):
        req = FriendRequest.objects.filter(id=request.query_params['id'], user=request.user).first()
        if not req:
            return Response({'success': False, 'message': 'Friend request not found'})
        if req.status == 'pending':
            req.status = 'accepted'
            req.save()
            Friends.objects.create(user=request.user, friend=req.sender)
            Friends.objects.create(user=req.sender, friend=request.user)
            return Response({'success': True, 'message': 'Friend request accepted'})
        return Response({'success': False, 'message': 'Friend request already accepted'})
        
    def delete(self, request):
        req = Friends.objects.filter(id=request.query_params['id'], user=request.user).first()
        if not req:
            return Response({'success': False, 'message': 'Friend not found'})
        req.delete()
        return Response({'success': True, 'message': 'Friend deleted'})


