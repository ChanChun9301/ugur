# rides/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .views import (
    # Новые ViewSet’ы
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

    # Специально для импорта старых заказов (который мы делали раньше)
    ImportOldUgurView,
)

# ===================================================================
# Роутер
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
router.register(r'loads', LoadViewSet, basename='load')
router.register(r'driver-notifications', DriverNotificationViewSet, basename='drivernotification')

# ===================================================================
# Основные URL’ы
# ===================================================================
urlpatterns = [
    # API
    path('', include(router.urls)),

    # Импорт старых заказов (временно, пока фронт не обновится)
    path('import-old-ugur/', ImportOldUgurView.as_view(), name='import-old-ugur'),

    # OpenAPI схема
    path('schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI (красиво и удобно для разработчиков и тестировщиков)
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Redoc (ещё красивее)
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]