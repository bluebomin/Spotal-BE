from django.contrib import admin
from .models import Memory, Image, Bookmark, Emotion, Location

@admin.register(Emotion)
class EmotionAdmin(admin.ModelAdmin):
    list_display = ['emotion_id', 'name']
    search_fields = ['name']

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['location_id', 'name']
    search_fields = ['name']

@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ['memory_id', 'user', 'content', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['content', 'user__email']

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_id', 'memory', 'image_url', 'image_name']
    list_filter = ['memory']
    search_fields = ['memory__content', 'image_name']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['bookmark_id', 'user', 'memory', 'created_date']
    list_filter = ['created_date', 'user']
    search_fields = ['user__email', 'memory__content']
