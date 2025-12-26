from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from django.contrib import messages
from .utils import send_push_to_driver
from .models import (
    User, DriverProfile, PassengerProfile,
    Place, Ugur, UgurRoute,CurrentPlace,
    Booking, Review, Load, DriverNotification
)

@admin.action(description="Saýlanan ugurlary işjeň däl et")
def deactivate_routes(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.action(description="Saýlanan ýüklere 'Ýolda' status ber")
def mark_in_transit(modeladmin, request, queryset):
    queryset.update(status="in_transit")

@admin.action(description="Saýlanan bildirişleri sürüjilere push hökmünde ugrat")
def send_driver_notifications(modeladmin, request, queryset):
    sent = 0
    for item in queryset:
        if item.driver:
            send_push_to_driver(
                item.driver,
                title=f"Ugruňyz bar",
                body=item.message or f"{item.from_place} → {item.to_place}"
            )
            sent += 1

    messages.success(request, f"{sent} sürüjä push ugradyldy!")


# ===============================================================
# 1. Ulanyjy (User) Admin paneli
# ===============================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Список полей в таблице
    list_display = ("phone", "first_name", "last_name", "is_driver", "is_passenger", "is_staff")
    search_fields = ("phone", "first_name", "last_name")
    list_filter = ("is_driver", "is_passenger", "is_staff", "is_superuser")

    # Сортировка
    ordering = ("phone",)

    # Поля для просмотра/редактирования пользователя
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Roles", {"fields": ("is_driver", "is_passenger")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Поля для добавления нового пользователя через админку
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "first_name", "last_name", "password1", "password2", "is_driver", "is_passenger"),
        }),
    )


# ===============================================================
# 2. Sürüjiniň profili üçin admin
# ===============================================================
@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "car_number", "marka", "model", "rating", "is_verified", "is_active")
    search_fields = ("user__phone", "user__phone", "car_number", "marka", "model")
    list_filter = ("is_verified", "is_active", "color", "car_year")


# ===============================================================
# 3. Ýolagçy profili admin
# ===============================================================
@admin.register(PassengerProfile)
class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rating", "total_rides")
    search_fields = ("user__phone",)


# ===============================================================
# 4. Şäher / Ýer admini
# ===============================================================
@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "created")
    search_fields = ("name",)


# ===============================================================
# 5. Ugruň içinde ugur-route görkezmek üçin inline forma
# ===============================================================
class UgurRouteInline(admin.StackedInline):
    model = UgurRoute
    extra = 1


# ===============================================================
# 6. Syýahat (Ugur) üçin admin paneli
# ===============================================================
@admin.register(Ugur)
class UgurAdmin(admin.ModelAdmin):
    actions = [deactivate_routes]
    list_display = ("id", "owner", "driver", "type", "title", "is_active", "is_completed", "created_at")
    list_filter = (
        "type",
        "is_active",
        "is_completed",
        ("created_at", DateTimeRangeFilter),  # ★ DOGRY FORMAT
    )
    search_fields = ("title", "owner__phone", "driver__phone")
    inlines = [UgurRouteInline]  # Ugruň aşagynda ýagdaýy görkeziň


# ===============================================================
# 7. Ugryň (Route) admini
# ===============================================================
@admin.register(UgurRoute)
class UgurRouteAdmin(admin.ModelAdmin):
    list_display = ("ugur", "from_place", "to_place", "departure_date", "departure_time", "available_seats", "price_per_seat")
    list_filter = (
        ("departure_date", DateRangeFilter),  # ★ DOGRY FORMAT
        "from_place",
        "to_place",
    )
    search_fields = ("ugur__title",)


# ===============================================================
# 8. Bron (Booking) admini
# ===============================================================
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("route", "passenger", "status", "seats_booked", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("route__ugur__title", "passenger__phone")


# ===============================================================
# 9. Bellik / Review admini
# ===============================================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "rating", "created")
    list_filter = ("rating", "created")
    search_fields = ("from_user__phone", "to_user__phone")


# ===============================================================
# 10. Ýük / Load admini
# ===============================================================
@admin.register(Load)
class LoadAdmin(admin.ModelAdmin):
    actions = [mark_in_transit]
    list_display = ("id", "sender", "status", "from_place", "to_place", "price", "created")
    list_filter = ("status", "created")
    search_fields = ("sender__phone", "receiver_name", "receiver_phone")


# ===============================================================
# 11. Sürüjilere Bildiriş admini
# ===============================================================
@admin.register(DriverNotification)
class DriverNotificationAdmin(admin.ModelAdmin):
    list_display = ("driver", "from_place", "to_place", "price", "is_seen", "created")
    list_filter = ("is_seen", "created")
    search_fields = ("driver__phone", "message")
    actions = [send_driver_notifications]


@admin.register(CurrentPlace)
class CurrentPlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "latitude", "longitude")
    search_fields = ("title", "description",  "user__phone")
    list_filter = ("user",)  # islege görä wagt/ulanyjy boýunça filter goşup bolýar
    ordering = ("-id",)