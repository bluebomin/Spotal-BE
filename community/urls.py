from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from . import views


app_name = 'community'

router_community = DefaultRouter()
router_community.register(r'emotions', EmotionViewSet, basename='emotion')
router_community.register(r'locations', LocationViewSet, basename='location')
router_community.register(r'memories', MemoryViewSet, basename='memory')
router_community.register(r'images', ImageViewSet, basename='image')
router_community.register(r'comments', CommentViewSet, basename='comment')  


urlpatterns = [
    path('', include(router_community.urls)),
    path('my/', my_community, name='my_community'),  # 내 커뮤니티 글 조회
    path("bookmarks/create/", views.BookmarkCreateView.as_view(), name="bookmark-create"),
    path("bookmarks/", views.BookmarkListView.as_view(), name="bookmark-list"),
    path("bookmarks/<int:bookmark_id>/delete/", views.BookmarkDeleteView.as_view(), name="bookmark-delete"),
]