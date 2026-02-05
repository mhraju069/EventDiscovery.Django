from rest_framework import serializers
from .models import *

class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.type == "private" and request:
            other_user = obj.members.exclude(id=request.user.id).first()
            if other_user and other_user.image:
                return other_user.image.url
            return None
        return obj.image.url if obj.image else None

    def get_name(self, obj):
        request = self.context.get('request')
        if obj.type == "private" and request:
            other_user = obj.members.exclude(id=request.user.id).first()
            if other_user:
                return other_user.name or other_user.email
            return "Deleted User"
        return obj.name 

    def get_last_message(self, obj):
        message = obj.messages.last()
        if message:
            return {
                "sender" : message.sender.name or message.sender.email,
                "content" : message.content,
                "created_at" : message.created_at,
                }
        return None
    
    class Meta:
        model = ChatRoom
        fields = ["id","type","name","image","last_message"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
