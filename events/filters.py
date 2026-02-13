from django_filters import rest_framework as filters
from .models import Event
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import math

class EventFilter(filters.FilterSet):
    time_period = filters.CharFilter(method='filter_time_period')
    distance = filters.NumberFilter(method='filter_distance')
    user_lat = filters.NumberFilter(method='noop')
    user_long = filters.NumberFilter(method='noop')
    price_type = filters.CharFilter(method='filter_price')
    status = filters.CharFilter(method='filter_status')

    class Meta:
        model = Event
        fields = {
            'age_from': ['gte', 'lte', 'exact'],
            'age_to': ['gte', 'lte', 'exact'],
            'price': ['gte', 'lte', 'exact'],
            'admin': ['exact'],
        }

    def noop(self, queryset, name, value):
        return queryset

    def filter_time_period(self, queryset, name, value):
        now = timezone.now()
        if value == 'today':
            return queryset.filter(time__date=now.date())
        elif value == 'this_weekend':
            # Assuming weekend is Saturday and Sunday
            saturday = now + timedelta(days=(5 - now.weekday()) % 7)
            sunday = saturday + timedelta(days=1)
            return queryset.filter(time__date__range=[saturday.date(), sunday.date()])
        return queryset

    def filter_status(self, queryset, name, value):
        now = timezone.now()
        if value == 'upcoming':
            return queryset.filter(time__gt=now)
        elif value == 'past':
            return queryset.filter(time__lt=now)
        return queryset

    def filter_price(self, queryset, name, value):
        if value == 'free':
            return queryset.filter(price=0)
        elif value == 'paid':
            return queryset.filter(price__gt=0)
        return queryset

    def filter_distance(self, queryset, name, value):
        user_lat = self.data.get('user_lat')
        user_long = self.data.get('user_long')
        
        if not (user_lat and user_long and value):
            return queryset

        return self.apply_distance_filter(queryset, user_lat, user_long, value)

    def apply_distance_filter(self, queryset, lat, long, distance):
        lat = float(lat)
        long = float(long)
        distance = float(distance)

        # 1 degree of latitude is approx 69 miles
        lat_range = distance / 69.0
        # 1 degree of longitude is approx 69 * cos(lat) miles
        long_range = distance / (69.0 * math.cos(math.radians(lat)))

        return queryset.filter(
            latitude__range=(lat - lat_range, lat + lat_range),
            longitude__range=(long - long_range, long + long_range)
        )

    @property
    def qs(self):
        parent_qs = super().qs
        user_lat = self.data.get('user_lat')
        user_long = self.data.get('user_long')
        distance = self.data.get('distance')

        # If coordinates are provided but no distance is specified, default to 5 miles
        if user_lat and user_long and not distance:
            return self.apply_distance_filter(parent_qs, user_lat, user_long, 5.0)
        
        return parent_qs
