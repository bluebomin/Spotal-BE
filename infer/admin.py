from django.contrib import admin
from .models import UserInferenceSession, InferenceRecommendation, AISummary

@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['summary_id', 'place', 'created_date']
    list_filter = ['created_date']
    search_fields = ['place__name', 'summary']

@admin.register(UserInferenceSession)
class UserInferenceSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'get_location_names', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    filter_horizontal = ['selected_location', 'selected_emotions']
    
    def get_location_names(self, obj):
        """선택된 동네명들을 문자열로 반환"""
        return ", ".join([location.name for location in obj.selected_location.all()])
    get_location_names.short_description = '선택된 동네들'

@admin.register(InferenceRecommendation)
class InferenceRecommendationAdmin(admin.ModelAdmin):
    list_display = ['recommendation_id', 'session', 'place', 'created_at']
    list_filter = ['created_at']
    search_fields = ['place__name']
