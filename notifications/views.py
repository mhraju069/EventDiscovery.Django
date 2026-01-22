from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class NotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications[:20], many=True)
        return Response(serializer.data)

    def patch(self, request):
        id = request.query_params.get('id')
        if not id:
            return Response({'success': False, 'log': 'Notification ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        notification = Notification.objects.filter(id=id, user=request.user).first()

        if not notification:
            return Response({'success': False, 'log': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()
        return Response({'success': True, 'log': 'Notification marked as read'}, status=status.HTTP_200_OK)

    def delete(self, request):
        id = request.query_params.get('id')
        if not id:
            return Response({'success': False, 'log': 'Notification ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        notification = Notification.objects.filter(id=id, user=rsequest.user).first()

        if not notification:
            return Response({'success': False, 'log': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

        notification.delete()
        return Response({'success': True, 'log': 'Notification deleted'}, status=status.HTTP_200_OK)