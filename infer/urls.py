from django.urls import path
from . import views

app_name = 'infer'

urlpatterns = [
    # 추론 옵션 조회
    path('options/', views.get_inference_options, name='inference-options'),
    
    # 추론 세션 생성 및 GPT 추천
    path('create-session/', views.create_inference_session, name='create-inference-session'),
    
    # 특정 추론 세션 조회
    path('session/<int:session_id>/', views.get_inference_session, name='get-inference-session'),
    
    # 사용자 추론 히스토리
    path('history/', views.get_user_inference_history, name='user-inference-history'),
]
