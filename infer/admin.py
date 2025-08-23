from django.contrib import admin
from .models import UserInferenceSession, InferenceRecommendation, Place, AISummary

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['shop_id', 'name', 'location', 'created_date']
    list_filter = ['location', 'created_date']
    search_fields = ['name', 'address']
    filter_horizontal = ['emotions']

@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['summary_id', 'place', 'created_date']
    list_filter = ['created_date']
    search_fields = ['place__name', 'summary']

@admin.register(UserInferenceSession)
class UserInferenceSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'selected_location', 'created_at']
    list_filter = ['selected_location', 'created_at']
    search_fields = ['user__username', 'selected_location__name']
    filter_horizontal = ['selected_emotions']

@admin.register(InferenceRecommendation)
class InferenceRecommendationAdmin(admin.ModelAdmin):
    list_display = ['recommendation_id', 'session', 'place', 'created_at']
    list_filter = ['created_at']
    search_fields = ['place__name', 'session__selected_location__name']
