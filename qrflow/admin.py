from django.contrib import admin
from .models import Location, Feedback

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "place_id")
    search_fields = ("name", "slug", "place_id")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("location_slug", "email", "created_at")
    list_filter = ("location_slug", "created_at")
    search_fields = ("location_slug", "email", "what_went_wrong")