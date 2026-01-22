from django.urls import path
from .views import *

urlpatterns = [
    path('', GetChatRoomsView.as_view(), name='chat-rooms'),
    path('create-group/', CreateGroupChatView.as_view(), name='create-group-chat'),
    path('join-group/<str:action>/', JoinGroupChatView.as_view(), name='join-group-chat'),
]   