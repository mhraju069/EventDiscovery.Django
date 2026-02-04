from rest_framework import serializers
from .models import *

class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    def get_image(self, obj):
        if obj.type == "private":
            return obj.members.exclude(id=self.context['request'].user.id).first().image.url if obj.members.exclude(id=self.context['request'].user.id).first().image else None
        return obj.image.url if obj.image else None

    def get_name(self, obj):
        if obj.type == "private":
            return obj.members.exclude(id=self.context['request'].user.id).first().name or obj.members.exclude(id=self.context['request'].user.id).first().email
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
