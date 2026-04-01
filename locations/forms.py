from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.forms import inlineformset_factory
from core_settings.models import SiteSettings
from locations.models import Location
from reservations.models import (
    TimeSlotModel,
    BlockedDayModel,
    DaySlotBlockModel,
    ReservationModel,
)


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlotModel
        fields = [
            "label",
            "slug",
            "start_time",
            "end_time",
            "capacity",
            "sort_order",
            "is_active",
        ]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-input"}),
            "slug": forms.TextInput(attrs={"class": "form-input"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-input"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-input"}),
            "capacity": forms.NumberInput(attrs={"class": "form-input", "min": "1"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }


class BlockedDayForm(forms.ModelForm):
    class Meta:
        model = BlockedDayModel
        fields = [
            "date",
            "reason",
            "is_closed",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "reason": forms.TextInput(attrs={"class": "form-input", "placeholder": "Optional reason"}),
            "is_closed": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }


BlockedDaySlotBlockFormSet = inlineformset_factory(
    BlockedDayModel,
    DaySlotBlockModel,
    fields=["slot", "blocked_seats", "is_closed", "reason"],
    extra=0,
    can_delete=True,
    widgets={
        "slot": forms.Select(attrs={"class": "form-input"}),
        "blocked_seats": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
        "is_closed": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        "reason": forms.TextInput(attrs={"class": "form-input", "placeholder": "Optional reason"}),
    },
)


class ReservationForm(forms.ModelForm):
    class Meta:
        model = ReservationModel
        fields = [
            "name",
            "email",
            "phone",
            "date",
            "slot",
            "time",
            "party_size",
            "message",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "e.g. John Smith",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "guest@example.com",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "+49 ...",
            }),
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-input",
                }
            ),
            "slot": forms.Select(attrs={
                "class": "form-input",
                "id": "id_slot",
            }),
            "time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "type": "time",
                    "class": "form-input",
                    "id": "id_time",
                    "step": "60",
                }
            ),
            "party_size": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "1",
                "placeholder": "e.g. 4",
            }),
            "message": forms.Textarea(attrs={
                "class": "form-input",
                "rows": "3",
                "placeholder": "Any special requests, allergies, or notes...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["time"].input_formats = ["%H:%M"]
        self.fields["date"].input_formats = ["%Y-%m-%d"]

        today = date.today()

        if self.instance and self.instance.pk and self.instance.date and self.instance.date < today:
            self.fields["date"].widget.attrs["min"] = self.instance.date.strftime("%Y-%m-%d")
        else:
            self.fields["date"].widget.attrs["min"] = today.strftime("%Y-%m-%d")

    def clean(self):
        cleaned_data = super().clean()

        reservation_date = cleaned_data.get("date")
        slot = cleaned_data.get("slot")
        party_size = cleaned_data.get("party_size")

        if not reservation_date or not slot:
            return cleaned_data

        blocked_day = (
            BlockedDayModel.objects
            .prefetch_related("slot_blocks__slot")
            .filter(date=reservation_date)
            .first()
        )

        if not blocked_day:
            return cleaned_data

        # Whole day closed
        if blocked_day.is_closed:
            raise ValidationError({
                "date": "This day is blocked for reservations."
            })

        slot_block = next(
            (block for block in blocked_day.slot_blocks.all() if block.slot_id == slot.id),
            None
        )

        if not slot_block:
            return cleaned_data

        # Selected slot fully closed
        if slot_block.is_closed:
            raise ValidationError({
                "slot": f'"{slot.label}" is blocked on this date.'
            })

        # Optional capacity restriction for partially blocked seats
        if party_size:
            slot_capacity = slot.capacity or 0
            blocked_seats = slot_block.blocked_seats or 0
            allowed_capacity = max(slot_capacity - blocked_seats, 0)

            existing_qs = ReservationModel.objects.filter(
                date=reservation_date,
                slot=slot,
            )

            if self.instance and self.instance.pk:
                existing_qs = existing_qs.exclude(pk=self.instance.pk)

            already_reserved = existing_qs.aggregate(
                total=Sum("party_size")
            )["total"] or 0

            if already_reserved + party_size > allowed_capacity:
                remaining = max(allowed_capacity - already_reserved, 0)
                raise ValidationError({
                    "party_size": (
                        f'Only {remaining} seat(s) are available for "{slot.label}" on this date.'
                    )
                })

        return cleaned_data

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = [
            "name",
            "slug",
            "address",
            "phone",
            "email",
            "opening_hours",
            "menu_pdf",
            "order_url",
            "map_url",
            "hero_image",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Ming Europa Center"}),
            "slug": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. europa-center"}),
            "address": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Street, postal code, city"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "+49 ..."}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "location@example.com"}),
            "opening_hours": forms.TextInput(attrs={"class": "form-input", "placeholder": "Mon–Sun, 12:00–22:00"}),
            "menu_pdf": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://.../menu.pdf"}),
            "order_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
            "map_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://maps.google.com/..."}),
            "hero_image": forms.ClearableFileInput(attrs={"class": "form-input"}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "booking_days_in_advance",
            "opening_time",
            "closing_time",
        ]
        widgets = {
            "booking_days_in_advance": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "0",
                "placeholder": "e.g. 30",
            }),
            "opening_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-input",
            }),
            "closing_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-input",
            }),
        }