from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("booking_days_in_advance", "opening_time", "closing_time", "updated_at")

    def has_add_permission(self, request):
        # Only allow creating if none exists
        return not SiteSettings.objects.exists()
