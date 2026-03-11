from django import forms
from reservations.models import TimeSlotModel

from reservations.models import BlockedDayModel


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
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-input"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-input"}),
            "label": forms.TextInput(attrs={"class": "form-input"}),
            "slug": forms.TextInput(attrs={"class": "form-input"}),
            "capacity": forms.NumberInput(attrs={"class": "form-input", "min": "1"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }