from __future__ import annotations
from django.db import models
from django.core.validators import MinValueValidator
import hashlib
import secrets
from datetime import timedelta
from django.forms import ValidationError
from django.utils import timezone
from django.db.models import Sum

class TimeSlotModel(models.Model):
    """
    Configurable slots (admin-editable).
    Example:
      - Lunch 12:00–16:00
      - Dinner 16:00–22:00
    """
    slug = models.SlugField(unique=True)  # "lunch", "dinner"
    label = models.CharField(max_length=80)  # "Lunch", "Dinner"
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "start_time"]

    def __str__(self):
        return f"{self.label} ({self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')})"

    def clean(self):
        super().clean()

        # Only validate when editing existing slot
        if not self.pk:
            return

        # New capacity the admin is trying to set
        new_capacity = self.capacity or 0

        # total booked per date for this slot (today and future)
        today = timezone.localdate()

        qs = (self.reservations
              .filter(date__gte=today)
              .values("date")
              .annotate(total=Sum("party_size"))
              .order_by())

        # Find the maximum booked on any single date
        max_booked = 0
        worst_date = None
        for row in qs:
            if (row["total"] or 0) > max_booked:
                max_booked = row["total"] or 0
                worst_date = row["date"]

        if new_capacity < max_booked:
            raise ValidationError({
                "capacity": (
                    f"Kapazität kann nicht auf {new_capacity} gesetzt werden. "
                    f"Am {worst_date} sind bereits {max_booked} Personen gebucht."
                )
            })

def default_time():
    return timezone.localtime(timezone.now()).time()
  
class ReservationModel(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40)

    date = models.DateField()
    slot = models.ForeignKey(TimeSlotModel, on_delete=models.PROTECT, related_name="reservations")
    time = models.TimeField(default=default_time)
    party_size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["date", "slot"]),
            models.Index(fields=["email", "phone"]),
            models.Index(fields=["date", "time"]),
        ]


class BlockedDayModel(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200, blank=True)
    is_closed = models.BooleanField(default=False)  # full day closed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} ({'closed' if self.is_closed else 'open'})"

class DaySlotBlockModel(models.Model):
    blocked_day = models.ForeignKey(
        BlockedDayModel,
        on_delete=models.CASCADE,
        related_name="slot_blocks",
        null=True,   # TEMP
        blank=True,  # TEMP
    )

    slot = models.ForeignKey(TimeSlotModel, on_delete=models.CASCADE)

    blocked_seats = models.PositiveIntegerField(default=0)
    is_closed = models.BooleanField(default=False)
    reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocked_day", "slot")

    def clean(self):
        super().clean()

        if not self.slot_id or self.blocked_seats is None:
            return

        # 1) basic check
        if self.blocked_seats > self.slot.capacity:
            raise ValidationError({
                "blocked_seats": (
                    f"Blockierte Plätze ({self.blocked_seats}) dürfen nicht größer sein "
                    f"als die Slot-Kapazität ({self.slot.capacity})."
                )
            })

        # If we don't have a day yet (still TEMP nullable), skip booked check
        if not self.blocked_day_id:
            return

        # 2) booked seats already in that date+slot
        booked = (
            ReservationModel.objects
            .filter(date=self.blocked_day.date, slot=self.slot)
            .aggregate(total=Sum("party_size"))["total"] or 0
        )

        # Allowed capacity after blocking
        allowed = self.slot.capacity - self.blocked_seats

        if booked > allowed:
            max_blockable = max(self.slot.capacity - booked, 0)
            raise ValidationError({
                "blocked_seats": (
                    f"Für {self.blocked_day.date} sind bereits {booked} Personen gebucht. "
                    f"Sie können maximal {max_blockable} Plätze blockieren (Kapazität {self.slot.capacity})."
                )
            })
        
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class EmailSessionModel(models.Model):
    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64, unique=True)  # sha256 hex

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    user_agent = models.CharField(max_length=300, blank=True)
    ip_prefix = models.CharField(max_length=64, blank=True)

    is_revoked = models.BooleanField(default=False)

    @staticmethod
    def hash_token(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def create_for_email(cls, email: str, *, days_valid: int = 30, request=None):
        raw = secrets.token_urlsafe(32)
        now = timezone.now()
        obj = cls(
            email=email.strip().lower(),
            token_hash=cls.hash_token(raw),
            expires_at=now + timedelta(days=days_valid),
        )
        if request is not None:
            ua = request.META.get("HTTP_USER_AGENT", "")
            obj.user_agent = ua[:300]
            ip = request.META.get("REMOTE_ADDR", "") or ""
            obj.ip_prefix = ip[:64]
        obj.save()
        return obj, raw

    def is_valid(self) -> bool:
        return (not self.is_revoked) and (self.expires_at > timezone.now())