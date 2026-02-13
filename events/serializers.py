from .models import Event, EventImage, WishList
from rest_framework import serializers

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'event', 'image']


class EventSerializer(serializers.ModelSerializer):
    images = EventImageSerializer(many=True, read_only=True)
    members = serializers.SerializerMethodField()
    admin = serializers.CharField(source='admin.email', read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'time', 'admin', 
            'location', 'latitude', 'longitude', 'age_from', 'age_to',
            'price', 'members', 'member_count', 'images'
        ]
        read_only_fields = ['id', 'admin', 'location']
    
    def get_members(self, obj):
        return obj.members.values('id', 'image', 'email')


class WishListSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    class Meta:
        model = WishList
        fields = ['events']