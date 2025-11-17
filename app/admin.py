# rides/admin.py
from django.contrib import admin
from .models import *

admin.site.register(Place)
admin.site.register(User)
admin.site.register(Booking)
admin.site.register(Ugur)
admin.site.register(UgurRoute)
admin.site.register(PassengerProfile)
admin.site.register(DriverProfile)
admin.site.register(Review)
admin.site.register(Load)
admin.site.register(DriverNotification)
