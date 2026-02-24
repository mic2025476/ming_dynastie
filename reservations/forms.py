from django import forms
from django.utils import timezone
from django.db.models import Sum

from core_settings.models import SiteSettings
from .models import DaySlotBlockModel, ReservationModel, BlockedDayModel, TimeSlotModel


class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = ReservationModel
        fields = ["name", "email", "phone", "date", "time", "party_size", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()

        d = cleaned.get("date")
        t = cleaned.get("time")
        party_size = cleaned.get("party_size") or 0

        settings = SiteSettings.objects.first()

        if not d or not t:
            return cleaned

        # Opening hours validation
        if settings and (t < settings.opening_time or t > settings.closing_time):
            self.add_error("time", "Reservierungen sind nur während der Öffnungszeiten möglich.")
            return cleaned

        # 🔥 Find matching slot
        slot = None
        active_slots = TimeSlotModel.objects.filter(is_active=True).order_by("sort_order", "start_time")

        for s in active_slots:
            if s.start_time <= s.end_time:
                # normal range (12:00–16:00)
                if s.start_time <= t < s.end_time:
                    slot = s
                    break
            else:
                # overnight (22:00–02:00)
                if t >= s.start_time or t < s.end_time:
                    slot = s
                    break

        if not slot:
            self.add_error("time", "Diese Uhrzeit ist nicht verfügbar.")
            return cleaned

        cleaned["slot"] = slot  # 👈 attach slot
        self.instance.slot = slot   # ✅ ensures it is persisted on save

        # If whole day is closed
        if BlockedDayModel.objects.filter(date=d, is_closed=True).exists():
            self.add_error("date", "Das Restaurant ist heute ausgebucht.")
            return cleaned

        # Per-day per-slot blocks (boss blocks N seats or closes slot)
        block = (
            DaySlotBlockModel.objects
            .select_related("blocked_day")
            .filter(blocked_day__date=d, slot=slot)
            .first()
        )

        if block and block.is_closed:
            self.add_error("time", "Dieser Zeitraum ist an diesem Tag nicht verfügbar.")
            return cleaned

        blocked_seats = block.blocked_seats if block else 0
        allowed_capacity = max(slot.capacity - blocked_seats, 0)

        # Capacity check (UX level)
        total_seats = (
            ReservationModel.objects
            .filter(date=d, slot=slot)
            .aggregate(total=Sum("party_size"))["total"] or 0
        )
        qs = ReservationModel.objects.filter(date=d, slot=slot)

        # ✅ if editing existing reservation, exclude it from totals
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        total_seats = qs.aggregate(total=Sum("party_size"))["total"] or 0

        if total_seats + party_size > allowed_capacity:
            remaining = max(allowed_capacity - total_seats, 0)
            self.add_error(
                "time",
                f"Dieser Zeitraum ist leider ausgebucht. Verfügbar: {remaining} Plätze."
            )
        return cleaned


