from rest_framework import serializers
from .models import *

class ChatInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInfo
        fields = ["active","last_active"]


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()
    chat_info = serializers.SerializerMethodField()

    def get_unread_messages(self, obj):
        request = self.context.get('request')
        if obj.type == "private" and request:
            user = obj.members.filter(id=request.user.id).first()
            chat_info = user.chat_info.filter(user=request.user).first()

            msg_count = Message.objects.filter(room=obj, read_by=user).count()

            return msg_count
        return None

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

    class Meta:
        model = ChatRoom
        fields = ["id","name","image","chat_info"]


class MessageSerializer(serializers.ModelSerializer):
    reply_of = serializers.SerializerMethodField()
    seen_by = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = '__all__'

    def get_reply_of(self, obj):
        if obj.reply_of:
            return {
                "id" : obj.reply_of.id,
                "content" : obj.reply_of.content,
                "type" : obj.reply_of.type,
                "sender" : obj.reply_of.sender.name or obj.reply_of.sender.email,
                "file" : obj.reply_of.file.url if obj.reply_of.file else None,
            }
        return None

    def get_seen_by(self, obj):
        request = self.context.get('request')
        qs = obj.seen_by.all()
        if request and request.user:
            qs = qs.exclude(id=request.user.id)

        if obj.room.type == "private":
            if qs.count() > 0:
                return True
            return False

        return [
            {
                "name": user.name or user.email,
                "image": user.image.url if user.image else None
            }
            for user in qs
        ]

    def get_sender(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return {
                "name": request.user.name or request.user.email,
                "image": request.user.image.url if request.user.image else None
            }