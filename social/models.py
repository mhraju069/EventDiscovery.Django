from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL
# Create your models here.

class Friends(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    friends = models.ManyToManyField(User, related_name='friends_of')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Friend'
        verbose_name_plural = 'Friends'


class FriendRequest(models.Model):
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Friend Request'
        verbose_name_plural = 'Friend Requests'


class Group(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=[('school', 'School'), ('sports', 'Sports'), ('social', 'Social'), ('other', 'Other')], default='other')
    description = models.TextField()
    members = models.ManyToManyField(User, related_name='groups_members')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_of_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'


