# rides/admin.py
from django.contrib import admin
from .models import (
    PlaceToGo, CityPassenger, CityDriver, Ugur, UgurTo,
    PassengerProfile, DriverProfile, Comment, Load,
    NotificationDriver
)

admin.site.register(PlaceToGo)
admin.site.register(CityPassenger)
admin.site.register(CityDriver)
admin.site.register(Ugur)
admin.site.register(UgurTo)
admin.site.register(PassengerProfile)
admin.site.register(DriverProfile)
admin.site.register(Comment)
admin.site.register(Load)
admin.site.register(NotificationDriver)
