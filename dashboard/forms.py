from django import forms
from django.forms import inlineformset_factory

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
            "date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-input",
            }),
            "slot": forms.Select(attrs={
                "class": "form-input",
                "id": "id_slot",
            }),
            "time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-input",
                "id": "id_time",
            }),
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
