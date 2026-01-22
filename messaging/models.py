import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from social.models import Group
from events.models import Event
User = get_user_model()

# Create your models here.

class ChatRoom(models.Model):
    CONVERSATION_TYPE_CHOICES = (("private", "Private Chat"),("group", "Group Chat"),("event", "Event Chat"),)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=CONVERSATION_TYPE_CHOICES)
    name = models.CharField(max_length=255, blank=True, null=True)  
    members = models.ManyToManyField(User, related_name='conversations_members',)
    group = models.OneToOneField(Group,on_delete=models.CASCADE,null=True,blank=True,related_name="group_conversations")
    event = models.OneToOneField(Event,on_delete=models.CASCADE,null=True,blank=True,related_name="event_conversations")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="created_conversations",)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    MESSAGE_TYPE_CHOICES = (("text", "Text"),("image", "Image"),("file", "File"),("voice", "Voice"),)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom,on_delete=models.CASCADE,related_name="messages",)    
    sender = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name="sent_messages",)
    type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="text")
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

