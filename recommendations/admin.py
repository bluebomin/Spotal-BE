from django.contrib import admin
from .models import Place, AISummary, SavedPlace

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['shop_id', 'name', 'address', 'created_date']
    list_filter = ['created_date']
    search_fields = ['name', 'address']

@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['summary_id', 'shop', 'summary', 'created_date', 'modified_date']
    list_filter = ['created_date', 'modified_date']
    search_fields = ['shop__name', 'summary']

@admin.register(SavedPlace)
class SavedPlaceAdmin(admin.ModelAdmin):
    list_display = ['saved_id', 'user', 'shop', 'created_date']
    list_filter = ['created_date', 'user']
    search_fields = ['user__email', 'shop__name']
