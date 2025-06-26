from django.utils import timezone
from .models import Reservation

def is_station_reserved(station):
    now = timezone.now()
    return Reservation.objects.filter(
        station=station,
        is_validated=True,
        start_time__lte=now,
        end_time__gte=now
    ).exists()
