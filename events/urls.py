from django.urls import path
from .views import *
urlpatterns = [
    path('list/', EventListView.as_view(), name='event-list'),
    path('wish-list/', WishListView.as_view(), name='wish-list'),
    path('create/', EventCreateView.as_view(), name='event-create'),
    path('update/<int:pk>/', EventRetrieveUpdateDestroyAPIView.as_view(), name='event-retrieve-update-destroy'),
]