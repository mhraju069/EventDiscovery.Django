from .models import *
from rest_framework import serializers

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['id', 'user', 'sender', 'status', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class FreiendSerializer(serializers.ModelSerializer):
    friends = serializers.SerializerMethodField()
    class Meta:
        model = Friends
        fields = ['id', 'user', 'friends', 'created_at']
        read_only_fields = ['id', 'user', 'friends', 'created_at']
    
    def get_friends(self, obj):
        return obj.friends.values('id', 'name', 'image')