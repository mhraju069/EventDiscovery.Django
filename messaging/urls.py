from django.urls import path
from .views import *

urlpatterns = [
    path('create-group/', CreateGroupChatView.as_view(), name='create-group-chat'),
    path('room-list/<str:type>/', GetRoomListView.as_view(), name='room-list'),
    path('join-group/<str:action>/', JoinGroupChatView.as_view(), name='join-group-chat'),
    path('messages/<str:room>/', GetRoomMessagesView.as_view(), name='room-messages'),
]   