from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, PlaceToGoViewSet, CityPassengerViewSet, CityDriverViewSet,
    UgurViewSet, UgurToViewSet, PassengerProfileViewSet, DriverProfileViewSet,
    CommentViewSet, LoadViewSet, NotificationDriverViewSet,
    FilterPassengerViewSet, FilterDriverViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'places-to-go', PlaceToGoViewSet)
router.register(r'city-passengers', CityPassengerViewSet)
router.register(r'city-drivers', CityDriverViewSet)
router.register(r'ugurs', UgurViewSet)
router.register(r'ugur-to', UgurToViewSet)
router.register(r'passenger-profiles', PassengerProfileViewSet)
router.register(r'driver-profiles', DriverProfileViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'loads', LoadViewSet)
router.register(r'notifications-drivers', NotificationDriverViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
