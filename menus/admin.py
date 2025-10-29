from django.contrib import admin
from .models import MenuDocument

@admin.register(MenuDocument)
class MenuDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'is_active', 'sort_order')
    list_filter = ('location', 'is_active')
    search_fields = ('title',)
    ordering = ('location', 'sort_order', 'title')
