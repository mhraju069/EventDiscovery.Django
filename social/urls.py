from django.urls import path
from .views import *
urlpatterns = [
    path('friend-request/', FriendRequestView.as_view(), name='friend-request'),
    path('friends/', FriendView.as_view(), name='friend'),
    path('group/', GroupView.as_view(), name='group'),
    path('group/member/<str:action>/', GroupMemberView.as_view(), name='group-member'),
]