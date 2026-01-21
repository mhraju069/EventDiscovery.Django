from .models import *
from rest_framework import serializers

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.email')
    receiver = serializers.CharField(source='receiver.email')
    class Meta:
        model = FriendRequest
        fields = ['id', 'receiver', 'sender', 'status', 'created_at']
        read_only_fields = ['id', 'receiver', 'created_at']


class FreiendSerializer(serializers.ModelSerializer):
    friends = serializers.SerializerMethodField()
    class Meta:
        model = Friends
        fields = ['id', 'user', 'friends', 'created_at']
        read_only_fields = ['id', 'user', 'friends', 'created_at']
    
    def get_friends(self, obj):
        return obj.friends.values('id', 'name', 'image','email')


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField()
    class Meta:
        model = Group
        fields = ['id', 'name', 'type', 'description', 'members', 'admin', 'created_at']
        read_only_fields = ['id', 'admin', 'created_at']

    def get_members(self, obj):
        return obj.members.values('id', 'name', 'image')

    def get_admin(self, obj):
        return obj.admin.email
