# rides/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Passenger(models.Model):
    """Отдельная модель пассажира"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    rating = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Driver(models.Model):
    """Отдельная модель водителя"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    marka = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    car_number = models.CharField(max_length=50, blank=True)
    car_year = models.PositiveIntegerField(
        null=True, blank=True, 
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    reyting = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )

    def __str__(self):
        return f"{self.name} — {self.marka} {self.model} ({self.car_number})"


class PlaceToGo(models.Model):
    """Place_to_go в вашей схеме"""
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(Passenger, null=True, blank=True, on_delete=models.SET_NULL, related_name='places_created')

    def __str__(self):
        return self.name


class CityPassenger(models.Model):
    """Город/маршрут для пассажира"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='city_passengers')
    now_location = models.CharField(max_length=255)  # текущее местоположение
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    place_to_go = models.ForeignKey(PlaceToGo, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.now_location} → {self.place_to_go or '—'}"


class CityDriver(models.Model):
    """Город/маршрут для водителя (city_driver)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='city_drivers')
    driver_name = models.CharField(max_length=200, blank=True)  # опционально
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    from_place = models.CharField(max_length=255)
    to_place = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.from_place} → {self.to_place}"


class Ugur(models.Model):
    """Ugur (по макету) — основной заказ/поездка"""
    title = models.CharField(max_length=200, blank=True)  # 'ugur' в вашей схеме
    created = models.DateTimeField(auto_now_add=True)
    date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='ugurs')

    def __str__(self):
        return f"{self.title or 'Ugur'} ({self.id})"


class UgurTo(models.Model):
    """Доп. параметры маршрута (ugur_to)"""
    ugur = models.ForeignKey(Ugur, related_name='targets', on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    from_place = models.CharField(max_length=255)
    to_place = models.CharField(max_length=255)
    trip_type = models.CharField(max_length=50, blank=True)  # type
    place_count = models.PositiveIntegerField(default=1)  # place_count
    name = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.from_place} → {self.to_place} ({self.ugur_id})"


class PassengerProfile(models.Model):
    """Профиль пассажира"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    name = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    ugur = models.ForeignKey(Ugur, null=True, blank=True, on_delete=models.SET_NULL, related_name='passenger_profiles')

    def __str__(self):
        return self.name or self.user.username


class DriverProfile(models.Model):
    """Профиль водителя (suruji)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    marka = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    car_number = models.CharField(max_length=50, blank=True)
    car_year = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    created = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=300, blank=True)  # my_address (profile)
    # поле для отображения в профиле
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.marka} {self.model}"


class Comment(models.Model):
    """Comment: -user, -user_sender, -created, -description"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_received')
    user_sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_sent')
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __str__(self):
        return f"Comment from {self.user_sender.username} to {self.user.username} at {self.created}"


class Load(models.Model):
    """Load: груз/заказ"""
    sender = models.CharField(max_length=200)
    sender_phone = models.CharField(max_length=30, blank=True)
    receiver = models.CharField(max_length=200, blank=True)
    receiver_phone = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    mail_id = models.CharField(max_length=200, blank=True)  # mail_id

    def __str__(self):
        return f"Load {self.id} from {self.sender}"


class NotificationDriver(models.Model):
    """Уведомление для водителя"""
    driver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='driver_notifications')
    from_place = models.CharField(max_length=255, blank=True)
    to_place = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        return f"Notif to {self.driver.username if self.driver else '—'}: {self.from_place}→{self.to_place}"

