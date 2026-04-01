from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from .models import SiteSettings


class SiteSettingsAdminForm(forms.ModelForm):
    new_dashboard_password = forms.CharField(
        required=False,
        label="New dashboard password",
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the current dashboard password.",
    )

    confirm_dashboard_password = forms.CharField(
        required=False,
        label="Confirm dashboard password",
        widget=forms.PasswordInput(render_value=False),
        help_text="Enter the same password again for confirmation.",
    )

    class Meta:
        model = SiteSettings
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_dashboard_password")
        confirm_password = cleaned_data.get("confirm_dashboard_password")

        if new_password or confirm_password:
            if not new_password:
                self.add_error("new_dashboard_password", "Please enter the new dashboard password.")
            if not confirm_password:
                self.add_error("confirm_dashboard_password", "Please confirm the new dashboard password.")
            if new_password and confirm_password and new_password != confirm_password:
                self.add_error("confirm_dashboard_password", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        new_password = self.cleaned_data.get("new_dashboard_password")
        if new_password:
            instance.dashboard_password_hash = make_password(new_password)
            instance.dashboard_password_version = (instance.dashboard_password_version or 0) + 1

        if commit:
            instance.save()

        return instance


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsAdminForm

    list_display = ("booking_days_in_advance", "opening_time", "closing_time", "updated_at")

    fieldsets = (
        ("Reservation Settings", {
            "fields": ("booking_days_in_advance", "opening_time", "closing_time"),
        }),
        ("Dashboard Access", {
            "fields": ("new_dashboard_password", "confirm_dashboard_password"),
            "description": "Set a new dashboard password here. Saving a new password will log out all currently active dashboard users.",
        }),
        ("System Fields", {
            "fields": ("dashboard_password_version",),
        }),
    )

    readonly_fields = ("dashboard_password_version",)

    exclude = ("dashboard_password_hash",)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()