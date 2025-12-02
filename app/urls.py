# rides/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .views import (
    UserViewSet,
    DriverProfileViewSet,
    PassengerProfileViewSet,
    PlaceViewSet,
    UgurViewSet,
    UgurRouteViewSet,
    BookingViewSet,
    ReviewViewSet,
    LoadViewSet,
    DriverNotificationViewSet,
    ImportOldUgurView,
    CurrentPlaceViewSet
)

# ===================================================================
# Router
# ===================================================================
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'driver-profiles', DriverProfileViewSet, basename='driverprofile')
router.register(r'passenger-profiles', PassengerProfileViewSet, basename='passengerprofile')
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'ugurs', UgurViewSet, basename='ugur')
router.register(r'routes', UgurRouteViewSet, basename='ugurroute')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'current', CurrentPlaceViewSet, basename='current')
router.register(r'loads', LoadViewSet, basename='load')
router.register(r'driver-notifications', DriverNotificationViewSet, basename='drivernotification')

urlpatterns = [
    # API
    path('', include(router.urls)),
    path('import-old-ugur/', ImportOldUgurView.as_view(), name='import-old-ugur'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]