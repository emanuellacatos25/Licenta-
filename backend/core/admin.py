from django.contrib import admin
from .models import ChargingStation, Reservation, CustomUser

admin.site.register(ChargingStation)
admin.site.register(Reservation)
admin.site.register(CustomUser)
