from rest_framework import viewsets
from django.contrib.auth.models import User
from .models import (
    PlaceToGo, CityPassenger, CityDriver, Ugur, UgurTo,
    PassengerProfile, DriverProfile, Comment, Load,
    NotificationDriver
)
from .serializers import (
    UserSerializer, PlaceToGoSerializer, CityPassengerSerializer, CityDriverSerializer,
    UgurSerializer, UgurToSerializer, PassengerProfileSerializer, DriverProfileSerializer,
    CommentSerializer, LoadSerializer, NotificationDriverSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PlaceToGoViewSet(viewsets.ModelViewSet):
    queryset = PlaceToGo.objects.all()
    serializer_class = PlaceToGoSerializer


class CityPassengerViewSet(viewsets.ModelViewSet):
    queryset = CityPassenger.objects.all()
    serializer_class = CityPassengerSerializer


class CityDriverViewSet(viewsets.ModelViewSet):
    queryset = CityDriver.objects.all()
    serializer_class = CityDriverSerializer


class UgurViewSet(viewsets.ModelViewSet):
    queryset = Ugur.objects.all()
    serializer_class = UgurSerializer


class UgurToViewSet(viewsets.ModelViewSet):
    queryset = UgurTo.objects.all()
    serializer_class = UgurToSerializer


class PassengerProfileViewSet(viewsets.ModelViewSet):
    queryset = PassengerProfile.objects.all()
    serializer_class = PassengerProfileSerializer


class DriverProfileViewSet(viewsets.ModelViewSet):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class LoadViewSet(viewsets.ModelViewSet):
    queryset = Load.objects.all()
    serializer_class = LoadSerializer


class NotificationDriverViewSet(viewsets.ModelViewSet):
    queryset = NotificationDriver.objects.all()
    serializer_class = NotificationDriverSerializer

