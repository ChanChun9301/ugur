# rides/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from typing import Optional, Dict
from .models import (
    User, DriverProfile, PassengerProfile,
    Place, Ugur, UgurRoute, Booking,
    Review, Load, DriverNotification
)

User = get_user_model()

# ========================== Köne sargytlaryň importy ==========================
from django.db import transaction
from datetime import datetime


class OldFormatImportSerializer(serializers.Serializer):
    ugur = serializers.DictField()
    created = serializers.CharField(max_length=8)  # "12:50"
    passengers = serializers.ListField(child=serializers.DictField())

    def validate_ugur(self, data):
        required = ['date_to_go', 'time_to_go', 'driver']
        for field in required:
            if field not in data:
                raise serializers.ValidationError(f"Hökmany setir: {field}")
        return data

    @transaction.atomic
    def create(self, validated_data):
        ugur_data = validated_data['ugur']
        passengers_data = validated_data['passengers']
        created_time_str = validated_data['created']

        # 1. Sürüji köne ID boýunça
        driver_user = User.objects.get(driver_profile__id=ugur_data['driver'])

        # 2. Ugur döredýäris
        ugur = Ugur.objects.create(
            owner=driver_user,
            driver=driver_user,
            type=Ugur.Type.DRIVER,
            title="Import edilen syýahat"
        )

        # 3. Wagty parsit edýäris
        dep_date = datetime.strptime(ugur_data['date_to_go'], "%d.%m.%y").date()
        dep_time = datetime.strptime(ugur_data['time_to_go'], "%H:%M").time()

        # 4. Şäherler
        from_place, _ = Place.objects.get_or_create(name="Aşgabat")
        to_place, _ = Place.objects.get_or_create(name="Görkezilmedik")

        # 5. Ugur
        route = UgurRoute.objects.create(
            ugur=ugur,
            from_place=from_place,
            to_place=to_place,
            departure_date=dep_date,
            departure_time=dep_time,
            available_seats=4,
            comment=f"{created_time_str}-da köne ulgamdan import"
        )

        # 6. Bronlar
        created_bookings = 0
        for p in passengers_data:
            try:
                passenger_user = User.objects.get(passenger_profile__id=p['id'])
                Booking.objects.create(
                    route=route,
                    passenger=passenger_user,
                    seats_booked=1,
                    status=Booking.Status.CONFIRMED,
                    comment="Awtoimport"
                )
                created_bookings += 1
            except User.DoesNotExist:
                continue

        return {
            "ugur": ugur,
            "route": route,
            "bookings_created": created_bookings
        }

# ===================================================================
# 1. Esasy ulanyjy
# ===================================================================
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_driver = serializers.BooleanField(read_only=True)
    is_passenger = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone', 'full_name',
                  'is_driver', 'is_passenger', 'date_joined']
        read_only_fields = ['date_joined']


# ===================================================================
# 2. Sürüjiniň profili
# ===================================================================
class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    car_display = serializers.CharField(source='__str__', read_only=True)

    class Meta:
        model = DriverProfile
        fields = '__all__'


# ===================================================================
# 3. Ýolagçynyň profili
# ===================================================================
class PassengerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PassengerProfile
        fields = '__all__'


# ===================================================================
# 4. Şäher / Ýer
# ===================================================================
class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name']


# ===================================================================
# 5. Syýahadyň ugurlary (UgurRoute)
# ===================================================================

class UgurForRouteSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Ugur
        fields = [
            'id', 'title', 'type', 'type_display',
            'owner', 'driver', 'is_active', 'is_completed',
            'created_at', 'views'
        ]

class UgurRouteSerializer(serializers.ModelSerializer):
    from_place = PlaceSerializer(read_only=True)
    to_place = PlaceSerializer(read_only=True)
    from_place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.all(), source='from_place', write_only=True
    )
    to_place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.all(), source='to_place', write_only=True
    )
    date_display = serializers.CharField(source='get_date_display', read_only=True)
    time_display = serializers.CharField(source='get_time_display', read_only=True, allow_null=True)

    ugur = UgurForRouteSerializer(read_only=True)

    class Meta:
        model = UgurRoute
        fields = '__all__'
        read_only_fields = ['ugur']


# ===================================================================
# 6. Bronlamak
# ===================================================================
class BookingSerializer(serializers.ModelSerializer):
    passenger = UserSerializer(read_only=True)
    passenger_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_passenger=True),
        source='passenger',
        write_only=True
    )
    route = UgurRouteSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['created_at', 'status']


# ===================================================================
# 7.Esasy syýahat (Ugur)
# ===================================================================
class UgurListSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    main_route = UgurRouteSerializer(source='routes.first', read_only=True)
    route_count = serializers.IntegerField(source='routes.count', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Ugur
        fields = [
            'id', 'owner', 'driver', 'type', 'type_display', 'title',
            'created_at', 'is_active', 'is_completed', 'views',
            'main_route', 'route_count'
        ]

class UgurDetailSerializer(serializers.ModelSerializer):
    """Syýahat barada doly maglumat"""
    owner = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    driver_profile = DriverProfileSerializer(source='driver.driver_profile', read_only=True)
    routes = UgurRouteSerializer(many=True, read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Ugur
        fields = '__all__'

class UgurCreateSerializer(serializers.ModelSerializer):
    """Syýahat döretmek üçin (sürüjilere)"""
    routes = UgurRouteSerializer(many=True)

    class Meta:
        model = Ugur
        fields = ['type', 'title', 'routes']

    def create(self, validated_data):
        routes_data = validated_data.pop('routes')
        ugur = Ugur.objects.create(owner=self.context['request'].user, **validated_data)
        if ugur.type == Ugur.Type.DRIVER:
            ugur.driver = self.context['request'].user
            ugur.save()

        for route_data in routes_data:
            UgurRoute.objects.create(ugur=ugur, **route_data)

        return ugur


# ===================================================================
# 8. Bellikler
# ===================================================================
class ReviewSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['from_user']

# ===================================================================
# 9. Kargolar
# ===================================================================
class LoadSerializer(serializers.ModelSerializer):
    from_place = serializers.SerializerMethodField()
    to_place = serializers.SerializerMethodField()
    sender = UserSerializer(read_only=True)
    ugur = UgurListSerializer(read_only=True)
    route = UgurRouteSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Load
        fields = '__all__'  
        read_only_fields = ['sender', 'status', 'created', 'updated']

    def get_from_place(self, obj) -> Optional[dict]:
        place = obj.from_place
        return PlaceSerializer(place).data if place else None

    def get_to_place(self, obj) -> Optional[dict]:
        place = obj.to_place
        return PlaceSerializer(place).data if place else None

# ===================================================================
# 10. Sürüji üçin bildiriş
# ===================================================================
class DriverNotificationSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    from_place = PlaceSerializer(read_only=True)
    to_place = PlaceSerializer(read_only=True)

    class Meta:
        model = DriverNotification
        fields = '__all__'
        read_only_fields = ['created', 'is_seen']