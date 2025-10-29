from django.contrib import admin
from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'opening_hours')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'address')
