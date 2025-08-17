from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('store/',views.store_card, name='search_store'),    
]