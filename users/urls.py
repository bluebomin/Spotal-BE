from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-nickname/', views.check_nickname, name='check_nickname'),
    path('check-email/', views.check_email, name='check_email'),
] 