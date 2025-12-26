# rides/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend, NumberFilter,ChoiceFilter
import django_filters.rest_framework as filters
from rest_framework import viewsets, filters as drf_filters
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import PhoneTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from rest_framework import generics, permissions

from .models import (
    User, DriverProfile, PassengerProfile,
    Place, Ugur, UgurRoute, Booking,
    Review, Load, DriverNotification,CurrentPlace
)
from .serializers import (
    UserSerializer,
    DriverProfileSerializer,
    PassengerProfileSerializer,
    PlaceSerializer,
    UgurListSerializer,
    UgurDetailSerializer,
    UgurCreateSerializer,
    UgurRouteSerializer,
    BookingSerializer,
    ReviewSerializer,
    CurrentPlaceSerializer,
    LoadSerializer,
    DriverNotificationSerializer,
    OldFormatImportSerializer,
    DriverProfileUpdateSerializer
    )

User = get_user_model()



# ===================================================================
# 0. Auth
# ===================================================================
class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = {
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_driver': user.is_driver,
                'is_passenger': user.is_passenger,
            }
            if user.is_driver:
                driver = user.driver_profile
                data['driver_profile'] = {
                    'marka': driver.marka,
                    'model': driver.model,
                    'car_number': driver.car_number,
                    'car_year': driver.car_year,
                    'color': driver.color,
                }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateRolesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        is_driver = request.data.get('is_driver', user.is_driver)
        is_passenger = request.data.get('is_passenger', user.is_passenger)
        driver_profile_data = request.data.get('driver_profile')

        user.is_driver = is_driver
        user.is_passenger = is_passenger
        user.save()

        if is_driver:
            profile, created = DriverProfile.objects.get_or_create(user=user)
            if driver_profile_data:
                serializer = DriverProfileSerializer(profile, data=driver_profile_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Если пользователь больше не водитель, можно удалить профиль водителя или деактивировать
            DriverProfile.objects.filter(user=user).delete()

        return Response({'detail': 'Роли обновлены'}, status=status.HTTP_200_OK)
        
# ===================================================================
# 1. Ulanyjylar
# ===================================================================
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['phone', 'first_name', 'last_name']


# ===================================================================
# 2. Şäherler
# ===================================================================
class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    permission_classes = [IsAuthenticatedOrReadOnly]


# ===================================================================
# 3. Syýahat (Ugur)
# ===================================================================
class UgurViewSet(viewsets.ModelViewSet):
    queryset = Ugur.objects.filter(is_active=True).select_related('owner', 'driver').prefetch_related('routes')
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['type', 'driver', 'owner']
    search_fields = ['title', 'routes__from_place__name', 'routes__to_place__name']
    ordering_fields = ['created_at', 'routes__departure_date']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return UgurListSerializer
        if self.action == 'create':
            return UgurCreateSerializer
        return UgurDetailSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# ===================================================================
# 4. Ugurlar
# ===================================================================
class UgurRouteViewSet(viewsets.ModelViewSet):
    queryset = UgurRoute.objects.select_related('from_place', 'to_place', 'ugur__owner')
    serializer_class = UgurRouteSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_fields = ['from_place', 'to_place', 'departure_date']
    ordering_fields = ['departure_date', 'departure_time']
    permission_classes = [IsAuthenticatedOrReadOnly]


# ===================================================================
# 5. Bronlamak
# ===================================================================
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('passenger', 'route__from_place', 'route__to_place')
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(passenger=user) | self.queryset.filter(route__ugur__driver=user)

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)


# ===================================================================
# 6. Profiller
# ===================================================================
class DriverProfileUpdateView(generics.UpdateAPIView, generics.CreateAPIView):
    serializer_class = DriverProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Получаем или создаём профиль водителя для текущего пользователя
        profile, created = DriverProfile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class DriverProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriverProfile.objects.select_related('user')
    serializer_class = DriverProfileSerializer

class CurrentPlaceViewSet(viewsets.ModelViewSet):
    queryset = CurrentPlace.objects.select_related('user')
    serializer_class = CurrentPlaceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Create wagty user-i request.user bilen baglaýar
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # User diňe öz ýerlerini görýär
        return self.queryset.filter(user=self.request.user)


class PassengerProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PassengerProfile.objects.select_related('user')
    serializer_class = PassengerProfileSerializer


# ===================================================================
# 7. Bellikler
# ===================================================================
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('from_user', 'to_user')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


# ===================================================================
# 8. Ýükler
# ===================================================================

class LoadFilter(filters.FilterSet):
    status = ChoiceFilter(choices=Load.Status.choices)
    ugur = NumberFilter(field_name='ugur')
    route = NumberFilter(field_name='route')

    from_place = NumberFilter(field_name='ugur__routes__from_place', lookup_expr='exact')
    to_place = NumberFilter(field_name='ugur__routes__to_place', lookup_expr='exact')

    class Meta:
        model = Load
        fields = ['status', 'ugur', 'route']

class LoadViewSet(viewsets.ModelViewSet):
    queryset = Load.objects.select_related('sender', 'ugur', 'route').all()
    serializer_class = LoadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoadFilter 
    search_fields = ['description', 'receiver_name']
    ordering_fields = ['created', 'price']


# ===================================================================
# 9. Sürüjiniň bildirişi
# ===================================================================
class DriverNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = DriverNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverNotification.objects.filter(driver=self.request.user)


    @extend_schema(
        parameters=[
            OpenApiParameter("pk", int, OpenApiParameter.PATH),
        ]
    )
    @action(detail=True, methods=['post'])
    def mark_as_seen(self, request, pk:int=None):
        notification = self.get_object()
        notification.is_seen = True
        notification.save()
        return Response({"status": "seen"})


# ===================================================================
# 10. Köne sargytlary import etmek
# ===================================================================


class ImportOldUgurView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OldFormatImportSerializer

    def post(self, request):
        data = request.data[0] if isinstance(request.data, list) else request.data
        serializer = OldFormatImportSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "success": True,
                "ugur_id": result["ugur"].id,
                "route_id": result["route"].id,
                "bookings": result["bookings_created"]
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

