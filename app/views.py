# rides/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend, FilterSet,NumberFilter,ChoiceFilter
import django_filters.rest_framework as filters
from rest_framework import viewsets, filters as drf_filters

from .models import (
    User, DriverProfile, PassengerProfile,
    Place, Ugur, UgurRoute, Booking,
    Review, Load, DriverNotification
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
    LoadSerializer,
    DriverNotificationSerializer,
    OldFormatImportSerializer,  # наш импортёр старых заказов
)

User = get_user_model()


# ===================================================================
# 1. ПОЛЬЗОВАТЕЛИ
# ===================================================================
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ['phone', 'first_name', 'last_name']


# ===================================================================
# 2. ГОРОДА
# ===================================================================
class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    permission_classes = [IsAuthenticatedOrReadOnly]


# ===================================================================
# 3. ПОЕЗДКИ (Ugur)
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
# 4. МАРШРУТЫ
# ===================================================================
class UgurRouteViewSet(viewsets.ModelViewSet):
    queryset = UgurRoute.objects.select_related('from_place', 'to_place', 'ugur__owner')
    serializer_class = UgurRouteSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_fields = ['from_place', 'to_place', 'departure_date']
    ordering_fields = ['departure_date', 'departure_time']
    permission_classes = [IsAuthenticatedOrReadOnly]


# ===================================================================
# 5. БРОНИРОВАНИЯ
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
# 6. ПРОФИЛИ
# ===================================================================
class DriverProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriverProfile.objects.select_related('user')
    serializer_class = DriverProfileSerializer


class PassengerProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PassengerProfile.objects.select_related('user')
    serializer_class = PassengerProfileSerializer


# ===================================================================
# 7. ОТЗЫВЫ
# ===================================================================
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('from_user', 'to_user')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


# ===================================================================
# 8. ГРУЗЫ
# ===================================================================

class LoadFilter(filters.FilterSet):
    status = ChoiceFilter(choices=Load.Status.choices)
    ugur = NumberFilter(field_name='ugur')
    route = NumberFilter(field_name='route')

    # Если хочешь фильтровать по городам — делаем через связь
    from_place = NumberFilter(field_name='ugur__routes__from_place', lookup_expr='exact')
    to_place = NumberFilter(field_name='ugur__routes__to_place', lookup_expr='exact')

    class Meta:
        model = Load
        fields = ['status', 'ugur', 'route']  # ← только настоящие поля!
        # НЕ пиши сюда from_place, to_place, is_completed — их нет в модели!

class LoadViewSet(viewsets.ModelViewSet):
    queryset = Load.objects.select_related('sender', 'ugur', 'route').all()
    serializer_class = LoadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoadFilter  # ← используем правильный фильтр
    search_fields = ['description', 'receiver_name']
    ordering_fields = ['created', 'price']


# ===================================================================
# 9. УВЕДОМЛЕНИЯ ВОДИТЕЛЯ
# ===================================================================
class DriverNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = DriverNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverNotification.objects.filter(driver=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_seen(self, request, pk=None):
        notification = self.get_object()
        notification.is_seen = True
        notification.save()
        return Response({"status": "seen"})


# ===================================================================
# 10. ИМПОРТ СТАРЫХ ЗАКАЗОВ (временно, пока фронт старый)
# ===================================================================
from rest_framework.views import APIView

class ImportOldUgurView(APIView):
    permission_classes = [IsAuthenticated]

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