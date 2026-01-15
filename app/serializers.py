# rides/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from typing import Optional, Dict
from .models import (
    User, DriverProfile, PassengerProfile,
    Place, Ugur, UgurRoute, Booking,
    Review, Load, DriverNotification,CurrentPlace
)

User = get_user_model()

# ========================== Köne sargytlaryň importy ==========================
from django.db import transaction
from datetime import datetime

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate


class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'phone'  # 🔑 используем phone вместо username
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(
        choices=['driver', 'passenger'],
        write_only=True
    )

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        role = attrs.get('role')

        # 🔹 ручная аутентификация
        user = authenticate(username=phone, password=password)
        if not user:
            raise serializers.ValidationError("Неверный телефон или пароль")

        # 🔹 проверка роли
        if role == 'driver' and not user.is_driver:
            raise serializers.ValidationError('Ulanyjy sürüji däl')
        if role == 'passenger' and not user.is_passenger:
            raise serializers.ValidationError('Ulanyjy ýolagçy däl')

        # 🔹 создаём JWT вручную
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # 🔹 формируем ответ
        return {
            'user': {
                'id': user.id,
                'phone': user.phone,
                'is_driver': user.is_driver,
                'is_passenger': user.is_passenger,
            },
            'role': role,
            'token': access,
            'refresh': str(refresh)
        }

class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['driver', 'passenger'])

    def validate_role(self, value):
        user = self.context['request'].user
        if (value == 'driver' and user.is_driver) or (value == 'passenger' and user.is_passenger):
            raise serializers.ValidationError("У пользователя уже такая роль")
        return value

class DriverProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ('marka', 'model', 'car_number', 'car_year', 'color')
        ref_name = 'DriverProfileUpdate'


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ('marka', 'model', 'car_number', 'car_year', 'color')
        ref_name = 'DriverProfile'

class DriverProfileRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ('marka', 'model', 'car_number', 'car_year', 'color')
        ref_name = 'DriverProfileRequest'


class RegisterSerializer(serializers.ModelSerializer):
    driver_profile = DriverProfileRequestSerializer(required=False)
    role = serializers.ChoiceField(choices=['driver', 'passenger'], write_only=True)

    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'password', 'role', 'driver_profile')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def validate_driver_profile(self, value):
        role = self.initial_data.get('role')
        if role != 'driver' and value is not None:
            raise serializers.ValidationError(
                "Driver profile bolmaly diňe role='driver' bolan ýagdaýynda."
            )
        return value

    def validate(self, attrs):
        role = attrs.get('role')
        if role == 'driver' and 'driver_profile' not in self.initial_data:
            raise serializers.ValidationError({
                'driver_profile': 'Driver profile zerur, role="driver" bolanda.'
            })
        return attrs

    def create(self, validated_data):
        driver_data = validated_data.pop('driver_profile', None)
        password = validated_data.pop('password')
        role = validated_data.pop('role')

        validated_data['is_driver'] = role == 'driver'
        validated_data['is_passenger'] = role == 'passenger'

        user = User.objects.create_user(password=password, **validated_data)

        if user.is_driver and driver_data:
            DriverProfile.objects.create(user=user, **driver_data)

        if user.is_passenger:
            PassengerProfile.objects.create(user=user)
            print('### Created passenger profile for user:', user.phone)

        return user

class RegisterResponseSerializer(serializers.ModelSerializer):
    driver_profile = serializers.DictField(required=False)
    
    class Meta:
        model = User
        fields = ['phone', 'first_name', 'last_name', 'is_driver', 'is_passenger', 'driver_profile']
        ref_name = "RegisterResponseSerializer"


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
    car_year = serializers.IntegerField()

    class Meta:
        model = DriverProfile
        fields = '__all__'

class CurrentPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentPlace
        exclude = ['user']  # user sahypasyny serializer-den aýyrýar


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
            'created_at',
        ]

class UgurRouteSerializer(serializers.ModelSerializer):
    from_place = PlaceSerializer(read_only=True)
    to_place = PlaceSerializer(read_only=True)
    # from_place_id = serializers.PrimaryKeyRelatedField(
    #     queryset=Place.objects.all(), source='from_place', write_only=True
    # )
    # to_place_id = serializers.PrimaryKeyRelatedField(
    #     queryset=Place.objects.all(), source='to_place', write_only=True
    # )
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
    # passenger_id = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.filter(is_passenger=True),
    #     source='passenger',
    #     write_only=True
    # )
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
            'created_at', 'is_active', 'is_completed',
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