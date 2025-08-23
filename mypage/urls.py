from django.urls import path
from .views import MyPageView

app_name = 'mypage'

urlpatterns = [
    path("<int:user_id>/", MyPageView.as_view(), name="mypage"),
]
