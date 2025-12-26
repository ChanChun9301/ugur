from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils import timezone



# ===================================================================
# 1. Ulanyjy (Bir akkaund — hem Sürüji, hem Ýolagçy)
# ===================================================================
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The Phone must be set")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = None

    phone = models.CharField(
        _("Телефон"),
        max_length=17,
        unique=True,
        validators=[RegexValidator(regex=r'^\+993\d{8}$')],
        help_text=_("Необходим для входа и уведомлений")
    )
    is_driver = models.BooleanField(default=False)
    is_passenger = models.BooleanField(default=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()


# ===================================================================
# 2. Sürüjiniň profili (Eger diňe is_driver = True bolsa döredilýär)
# ===================================================================
class DriverProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='driver_profile'
    )
    marka = models.CharField(_("Ulagyň markasy"), max_length=100)
    model = models.CharField(_("Ulagyň modeli"), max_length=100)
    color = models.CharField(_("Ulagyň reňki"), max_length=50, blank=True)
    car_number = models.CharField(
        _("Гос. номер"), max_length=10, unique=True,
        validators=[RegexValidator(r'^[A-Z]{2}\d{4}[A-Z]{2}$', message=_("Mysal ucin: AG123BH"))]
    )
    car_year = models.PositiveSmallIntegerField(
        _("Год выпуска"), validators=[MinValueValidator(1995), MaxValueValidator(2026)]
    )
    rating = models.DecimalField(_("Рейтинг водителя"), default=5.00, max_digits=3, decimal_places=2)
    total_trips = models.PositiveIntegerField(_("Ýerine ýetiren syýahatlary"), default=0)
    is_verified = models.BooleanField(_("Admin tarapyndan barlanan"), default=False)
    is_active = models.BooleanField(_("Ulgamda"), default=True)

    class Meta:
        verbose_name = _("Sürüji")
        verbose_name_plural = _("Водители")

    def __str__(self):
        return f"{self.user} — {self.marka} {self.model} ({self.car_number})"

class CurrentPlace(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    title = models.CharField(_("Ýeriň ady"), max_length=500)
    description = models.TextField(_("Maglumat"), max_length=500)
    latitude = models.CharField(_("Latitude"), max_length=500)
    longitude = models.CharField(_("Longitude"), max_length=500)

    class Meta:
        verbose_name = _("Häzirki ýeri")
        verbose_name_plural = _("Bolan ýerleri")

    def __str__(self):
        return f"{self.user} — {self.title}: {self.latitude} ({self.longitude})"

# ===================================================================
# 3. Ýolagçynyň profili (islege bagly, ilkinji syýahat wagtynda döredildi)
# ===================================================================
class PassengerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='passenger_profile'
    )
    rating = models.DecimalField(_("Ýolagçynyň reýtingi"), default=5.00, max_digits=3, decimal_places=2)
    total_rides = models.PositiveIntegerField(_("Syýahat tamamlandy"), default=0)

    class Meta:
        verbose_name = _("Ýolagçy")
        verbose_name_plural = _("Ýolagçylar")


# ===================================================================
# 4. Şäher / Ýer (Hemmelere el ýeterli)
# ===================================================================
class Place(models.Model):
    name = models.CharField(_("Ýeriň ady"), max_length=200, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Şäher / Ýer")
        verbose_name_plural = _("Şäherler / Ýerler")
        ordering = ['name']

    def __str__(self):
        return self.name


# ===================================================================
# 5. Syýahat (Ugur) — Bildiriş üçin esasy
# ===================================================================
class Ugur(models.Model):
    class Type(models.TextChoices):
        DRIVER = 'driver', _("Sürüji orun hödürleýär")
        PASSENGER = 'passenger', _("Ýolagçy orun gözleýär")

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ugurs')
    driver = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='driven_ugurs',
        limit_choices_to={'is_driver': True},
        verbose_name=_("Sürüji")
    )
    type = models.CharField(_("Görnüşi"), max_length=20, choices=Type.choices, default=Type.DRIVER, db_index=True)
    title = models.CharField(_("Maglumat"), max_length=200, blank=True)

    created_at = models.DateTimeField(_("Döredildi"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Täzelendi"), auto_now=True)
    is_active = models.BooleanField(_("Işjeň"), default=True, db_index=True)
    is_completed = models.BooleanField(_("Tamamlandy"), default=False)
    views = models.PositiveIntegerField(_("Görülen"), default=0)

    class Meta:
        verbose_name = _("Syýahat (Ugur)")
        verbose_name_plural = _("Syýahatlar (Ugur)")
        ordering = ['-created_at']

    def __str__(self):
        if self.title:
            return self.title
        route = self.routes.first()
        if route:
            return f"{route.from_place} → {route.to_place} | {route.get_date_display()}"
        return f"Ugur #{self.id}"

    def get_absolute_url(self):
        return reverse('ugur_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.title and self.routes.exists():
            route = self.routes.first()
            self.title = f"{route.from_place} → {route.to_place}"
        super().save(*args, **kwargs)


# ===================================================================
# 6. Syaýahtyň ugry
# ===================================================================
class UgurRoute(models.Model):
    ugur = models.ForeignKey(Ugur, on_delete=models.CASCADE, related_name='routes')
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='departures')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='arrivals')

    departure_date = models.DateField(_("Ugraýan sene"))
    departure_time = models.TimeField(_("Ugraýan wagty"), null=True, blank=True)

    available_seats = models.PositiveSmallIntegerField(_("Boş orun"), default=4)
    price_per_seat = models.DecimalField(
        _("Ýer üçin baha (TMT)"), max_digits=8, decimal_places=2, null=True, blank=True
    )
    comment = models.TextField(_("Teswirler"), blank=True)
    stops = models.JSONField(_("Aralyk duralgalar"), blank=True, default=list)

    class Meta:
        verbose_name = _("Ugur")
        verbose_name_plural = _("Ugurlar")
        ordering = ['departure_date', 'departure_time']

    def __str__(self):
        time = self.departure_time.strftime("%H:%M") if self.departure_time else "?"
        return f"{self.from_place} → {self.to_place} | {self.departure_date} {time}"

    def get_date_display(self):
        return self.departure_date.strftime("%d.%m.%Y")


# ===================================================================
# 7. Bronlamak
# ===================================================================
class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _("Garaşylýar")
        CONFIRMED = 'confirmed', _("Tassyklanan")
        CANCELLED = 'cancelled', _("Inkär edilen")
        COMPLETED = 'completed', _("Tamamlandy")

    route = models.ForeignKey(UgurRoute, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    seats_booked = models.PositiveSmallIntegerField(_("Orun"), default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(_("Teswir"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['route', 'passenger']
        verbose_name = _("Bron")
        verbose_name_plural = _("Bronlar")

    def __str__(self):
        return f"{self.passenger} → {self.route} ({self.seats_booked} Orun)"


# ===================================================================
# 8. Bellikler
# ===================================================================
class Review(models.Model):
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.PositiveSmallIntegerField(_("Baha"), validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(_("Bellik"), blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Bellik")
        verbose_name_plural = _("Bellikler")
        unique_together = ['to_user', 'from_user', 'created']  # один отзыв за поездку

    def __str__(self):
        return f"{self.from_user} → {self.to_user}: {self.rating}★"


# ===================================================================
# 9. Kargolar
# ===================================================================
class Load(models.Model):
    class Status(models.TextChoices):
        SEARCHING = 'searching', _("Sürüji gözlenýär")
        ASSIGNED = 'assigned', _("Sürüji tapylgy") 
        IN_TRANSIT = 'in_transit', _("Ýolda")
        DELIVERED = 'delivered', _("Gowşuryldy")
        CANCELLED = 'cancelled', _("Ýatyryldy")

    # Ýük üçin sargydy kim döretdi
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sent_loads',
        verbose_name=_("Ugradýan")
    )

    # Haýsy esasy ugra berkidilen
    ugur = models.ForeignKey(
        Ugur, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='loads',
        verbose_name=_("Baglanan ýol")
    )

    # Anyk urgy
    route = models.ForeignKey(
        UgurRoute, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='loads',
        verbose_name=_("Baglanan ugur")
    )

    # Näme alyp barýas
    description = models.TextField(_("Näme alyp gitmeli"))
    weight_kg = models.PositiveSmallIntegerField(_("Agyrlygy (kg)"), null=True, blank=True)
    size = models.CharField(_("Ölçegi"), max_length=100, blank=True, help_text="Mysal: 50x40x30 sm")

    receiver_name = models.CharField(_("Kabul edýäniň ady"), max_length=200)
    receiver_phone = models.CharField(_("Kabul edýäniň telefon belgisi"), max_length=17)

    # Nyrhy
    price = models.DecimalField(_("Baha (TMT)"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_negotiable = models.BooleanField(_("Baha gepleşiler"), default=True)

    # Statusy we wagty
    status = models.CharField(_("Ýagdaýy"), max_length=20, choices=Status.choices, default=Status.SEARCHING)
    created = models.DateTimeField(_("Döredildi"), auto_now_add=True)
    updated = models.DateTimeField(_("Täzelendi"), auto_now=True)

    class Meta:
        verbose_name = _("Ýük (posylka)")
        verbose_name_plural = _("Ýükler (posylkalar)")
        ordering = ['-created']

    def __str__(self):
        if self.ugur:
            return f"Ýük #{self.id} → {self.ugur} "
        return f"Ýük #{self.id} | {self.ugur} (sürüji gözlenýär)"

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        if self.ugur and self.status == Load.Status.SEARCHING:
            self.status = Load.Status.ASSIGNED
        super().save(*args, **kwargs)

    @property
    def from_place(self):
        if self.route:
            return self.route.from_place
        if self.ugur and self.ugur.routes.exists():
            return self.ugur.routes.first().from_place
        return None

    @property
    def to_place(self):
        if self.route:
            return self.route.to_place
        if self.ugur and self.ugur.routes.exists():
            return self.ugur.routes.first().to_place
        return None


# ===================================================================
# 10. Sürüjilere bildiriş
# ===================================================================
class DriverNotification(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='notifications_from')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='notifications_to')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    message = models.CharField(max_length=500, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Sürüjä bildiriş")
        verbose_name_plural = _("Sürüjilere bildiriş")
        ordering = ['-created']

    def __str__(self):
        return f"{self.from_place}→{self.to_place} üçin {self.driver}"