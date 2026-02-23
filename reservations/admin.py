from django.contrib import admin
from .models import (
    TimeSlotModel,
    ReservationModel,
    BlockedDayModel,
    DaySlotBlockModel,
    EmailSessionModel,
)


# =========================
# Time Slots
# =========================
@admin.register(TimeSlotModel)
class TimeSlotModelAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "slug",
        "start_time",
        "end_time",
        "capacity",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active",)
    search_fields = ("label", "slug")
    ordering = ("sort_order", "start_time")


# =========================
# Reservations
# =========================
@admin.register(ReservationModel)
class ReservationModelAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "time",
        "slot",
        "name",
        "party_size",
        "email",
        "phone",
        "created_at",
    )
    list_filter = ("date", "slot")
    search_fields = ("name", "email", "phone")
    ordering = ("-created_at",)
    date_hierarchy = "date"


# =========================
# Day Slot Blocks (Inline)
# =========================
class DaySlotBlockInline(admin.TabularInline):
    model = DaySlotBlockModel
    extra = 1
    autocomplete_fields = ("slot",)
    fields = ("slot", "blocked_seats", "is_closed", "reason")


# =========================
# Blocked Days
# =========================
@admin.register(BlockedDayModel)
class BlockedDayAdmin(admin.ModelAdmin):
    list_display = ("date", "is_closed", "reason", "created_at")
    list_filter = ("is_closed",)
    ordering = ("-date",)
    inlines = [DaySlotBlockInline]
    date_hierarchy = "date"


# =========================
# Email Sessions
# =========================
@admin.register(EmailSessionModel)
class EmailSessionAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "expires_at", "is_revoked")
    search_fields = ("email",)
    list_filter = ("is_revoked",)
    ordering = ("-created_at",)
