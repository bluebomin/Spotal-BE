from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # gpt api 테스트 
    path('test-gpt/', views.test_gpt, name='test_gpt'),
    path('recommend-stores/', views.recommend_stores, name='recommend_stores'),
    
    # ai 추천장소
    path("places/create/", views.PlaceCreateView.as_view(), name="place-create"), # 장소 생성
    path("places/<int:shop_id>/", views.PlaceDetailView.as_view(), name="place-detail"), # 장소 세부조회

    # 장소 보관
    path("saved-places/create/", views.SavedPlaceCreateView.as_view(), name="savedplace-create"), # 장소 보관하기
    path("saved-places/", views.SavedPlaceListView.as_view(), name="savedplace-list"), # 보관한 장소 목록 조회
    path("saved-places/<int:saved_id>/delete/", views.SavedPlaceDeleteView.as_view(), name="savedplace-delete"), # 보관한 장소 삭제

    # AISummary 
    path("places/<int:shop_id>/summary/", views.AISummaryDetailView.as_view(), name="aisummary-detail"), # ai 요약만 따로 확인 
    path("places/<int:shop_id>/summary/create/", views.AISummaryCreateUpdateView.as_view(), name="aisummary-create"), # ai 요약만 새로 생성
]
