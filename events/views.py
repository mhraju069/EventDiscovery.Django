from rest_framework import generics, status, views
from rest_framework.response import Response
from .models import Event, WishList
from core.permissions import *
from .serializers import EventSerializer, WishListSerializer
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import EventFilter

# Create your views here.

class EventListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsParent]
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['time', 'created_at']

    def get_queryset(self):
        return Event.objects.filter(members=self.request.user).prefetch_related('images', 'members')


class EventCreateView(generics.CreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsParent]

    def perform_create(self, serializer):
        serializer.save(members=[self.request.user], admin=self.request.user)


class EventRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all().prefetch_related('images', 'members')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsEventAdmin]

    def get_queryset(self):
        return super().get_queryset().filter(admin=self.request.user)


class WishListView(views.APIView):
    
    def get(self, request):
        wish_list, created = WishList.objects.prefetch_related('events').get_or_create(user=self.request.user)
        serializer = WishListSerializer(wish_list)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        event = Event.objects.filter(id=request.query_params.get('event')).first()
        action = request.query_params.get('action')

        if not event:
            return Response({'status': False, 'log': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if action not in ['add', 'remove']:
            return Response({'status': False, 'log': 'Invalid action add or remove'}, status=status.HTTP_400_BAD_REQUEST)

        wish_list, created = WishList.objects.get_or_create(user=self.request.user)

        if action == 'add':
            wish_list.events.add(event)
            return Response({'status': True, 'log': 'Event added to wish list'}, status=status.HTTP_200_OK)

        elif action == 'remove':
            wish_list.events.remove(event)
            return Response({'status': True, 'log': 'Event removed from wish list'}, status=status.HTTP_200_OK) 