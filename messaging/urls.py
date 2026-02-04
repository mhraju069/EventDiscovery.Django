from django.urls import path
from .views import *

urlpatterns = [
    path('create-private/', CreatePrivateChatView.as_view(), name='create-private-chat'),
    path('create-group/', CreateGroupChatView.as_view(), name='create-group-chat'),
    path('room-list/', GetRoomListView.as_view(), name='room-list'),
    path('join-group/<str:action>/', JoinGroupChatView.as_view(), name='join-group-chat'),
    path('messages/<str:room>/', GetRoomMessagesView.as_view(), name='room-messages'),
    path('send-file-message/', SendFileMessageView.as_view(), name='send-file-message'),
    path('delete-chat/', DeleteChatView.as_view(), name='delete-chat'),
]   