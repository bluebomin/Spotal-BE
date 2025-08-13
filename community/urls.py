from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


app_name = 'community'

router_community = DefaultRouter()
router_community.register(r'emotions', EmotionViewSet, basename='emotion')
router_community.register(r'locations', LocationViewSet, basename='location')
router_community.register(r'memories', MemoryViewSet, basename='memory')
router_community.register(r'images', ImageViewSet, basename='image')

urlpatterns = [
    path('', include(router_community.urls)),
]