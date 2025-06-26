from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.contrib.auth import get_user_model
from django.conf import settings








# 👤 MODEL USER
class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20)
    cnp = models.CharField(max_length=13, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(unique=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True
    )


    def __str__(self):
        return self.username

# 🔌 MODEL STAȚIE DE ÎNCĂRCARE
class ChargingStation(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    available = models.BooleanField(default=True)
    connector_type = models.CharField(max_length=50, choices=[('Type 2', 'Type 2'), ('CCS', 'CCS'), ('CHAdeMO', 'CHAdeMO')], default='Type 2')
    power_kw = models.IntegerField(default=22)
    price_per_kwh = models.FloatField(default=1.5)

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def is_currently_reserved(self):
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now()
        return Reservation.objects.filter(
            station=self,
            is_validated=True,
            start_time__lte=now,
            end_time__gte=now
        ).exists()

    
    

# 📅 MODEL REZERVARE
class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey('ChargingStation', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    validation_code = models.UUIDField(default=uuid.uuid4, editable=False)
    is_validated = models.BooleanField(default=False)
    is_cancelled=models.BooleanField(default=False)
    is_hidden_by_user = models.BooleanField(default=False)


    def __str__(self):
        return f"Rezervare: {self.user.username} -> {self.station.name}"

