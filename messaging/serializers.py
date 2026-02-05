from rest_framework import serializers
from .models import *

class ChatInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInfo
        fields = ["active","active_at"]


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


class ChatRoomDetailsSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    chat_info = serializers.SerializerMethodField()
    
    def get_chat_info(self, obj):
        request = self.context.get('request')
        if obj.type == "private" and request:
            other_user = obj.members.exclude(id=request.user.id).first()
            chat_info = other_user.chat_info.filter(user=other_user).first()
            return ChatInfoSerializer(chat_info).data
        return None
    
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
        fields = ["id","name","image","chat_info"]


class MessageSerializer(serializers.ModelSerializer):
    reply_of = serializers.SerializerMethodField()
    class Meta:
        model = Message
        fields = '__all__'

    def get_reply_of(self, obj):
        if obj.reply_of:
            return {
                "id" : obj.reply_of.id,
                "content" : obj.reply_of.content,
                "type" : obj.reply_of.type,
                }
        return None
