from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('store/',views.yongsan_store_card, name='search_store'),    
]