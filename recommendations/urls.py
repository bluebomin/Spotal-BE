from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('test-gpt/', views.test_gpt, name='test_gpt'),
    path('recommend-stores/', views.recommend_stores, name='recommend_stores'),
]
