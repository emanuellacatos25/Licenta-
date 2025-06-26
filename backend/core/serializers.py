from rest_framework import serializers
from .models import CustomUser, ChargingStation, Reservation
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from datetime import timedelta

# ✅ Serializer utilizator
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email',
            'phone', 'first_name', 'last_name',
            'cnp', 'birth_date'
        ]

# ✅ Serializer stație cu status rezervare
class StationSerializer(serializers.ModelSerializer):
    is_reserved = serializers.SerializerMethodField()

    class Meta:
        model = ChargingStation
        fields = [
    'id', 'name', 'city', 'lat', 'lon', 'available',
    'connector_type', 'power_kw', 'price_per_kwh',
    'is_reserved'
]

    def get_is_reserved(self, station):
        now = timezone.now()
        return Reservation.objects.filter(
            station=station,
            is_validated=True,
            is_cancelled=False,
            start_time__lte=now,
            end_time__gte=now
        ).exists()

# ✅ Serializer rezervare cu timp rămas și denumire stație
class ReservationSerializer(serializers.ModelSerializer):
    time_left = serializers.SerializerMethodField()
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_city = serializers.CharField(source='station.city', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'user_id',
            'station',
            'station_name',
            'station_city',
            'start_time',
            'end_time',
            'validation_code',
            'is_validated',
            'is_cancelled',
            'time_left'
        ]
        read_only_fields = [
            'id',
            'user_id',
            'validation_code',
            'is_validated',
            'is_cancelled',
            'end_time',
        ]

    def get_time_left(self, obj):
        if obj.is_validated and obj.end_time:
            now = timezone.now()
            remaining = (obj.end_time - now).total_seconds()
            return max(int(remaining), 0)
        return None

# ✅ Serializer JWT token customizat
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff

        return token
