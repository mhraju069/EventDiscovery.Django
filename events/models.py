from django.db import models
from django.contrib.auth import get_user_model
from geopy.geocoders import Nominatim

User = get_user_model()

# Create your models here.

class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    time = models.DateTimeField()
    location = models.CharField(max_length=500, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    age_from = models.IntegerField(null=True, blank=True)
    age_to = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    members = models.ManyToManyField(User, related_name='events')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.latitude and self.longitude and not self.location:
            try:
                geolocator = Nominatim(user_agent="event_app")
                loc = geolocator.reverse(f"{self.latitude}, {self.longitude}")
                if loc:
                    self.location = loc.address
            except Exception as e:
                print(f"Geocoding error: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='event_images/')


class WishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wish_list')
    events = models.ManyToManyField(Event, related_name='wish_list')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email