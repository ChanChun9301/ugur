from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    PlaceToGo, CityPassenger, CityDriver, Ugur, UgurTo,
    PassengerProfile, DriverProfile, Comment, Load,
    NotificationDriver, 
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

# -------------------------------------
# PlaceToGo
class PlaceToGoSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)

    class Meta:
        model = PlaceToGo
        fields = '__all__'

# -------------------------------------
# CityPassenger
class CityPassengerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    place_to_go = PlaceToGoSerializer(read_only=True)

    class Meta:
        model = CityPassenger
        fields = '__all__'

# -------------------------------------
# CityDriver
class CityDriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CityDriver
        fields = '__all__'

# -------------------------------------
# Ugur
class UgurSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    targets = serializers.StringRelatedField(many=True, read_only=True)  # related_name='targets'

    class Meta:
        model = Ugur
        fields = '__all__'

# -------------------------------------
# UgurTo
class UgurToSerializer(serializers.ModelSerializer):
    ugur = UgurSerializer(read_only=True)

    class Meta:
        model = UgurTo
        fields = '__all__'

# -------------------------------------
# PassengerProfile
class PassengerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    ugur = UgurSerializer(read_only=True)

    class Meta:
        model = PassengerProfile
        fields = '__all__'

# -------------------------------------
# DriverProfile
class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DriverProfile
        fields = '__all__'

# -------------------------------------
# Comment
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_sender = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

# -------------------------------------
# Load
class LoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Load
        fields = '__all__'

# -------------------------------------
# NotificationDriver
class NotificationDriverSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)

    class Meta:
        model = NotificationDriver
        fields = '__all__'
