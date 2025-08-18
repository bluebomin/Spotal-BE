from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from .services import call_gpt_api, get_store_recommendation
from .models import Place, SavedPlace, AISummary
from .serializers import PlaceSerializer, SavedPlaceSerializer, AISummarySerializer

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def test_gpt(request):
    """GPT API 테스트용 엔드포인트"""
    prompt = request.data.get('prompt', '안녕하세요! 간단한 인사말을 해주세요.')
    
    if not prompt:
        return Response({
            'error': '프롬프트를 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 디버깅: API 키 상태 확인
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        return Response({
            'error': 'OpenAI API 키가 설정되지 않았습니다.',
            'debug_info': 'OPENAI_API_KEY가 settings에 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # GPT API 호출
    response = call_gpt_api(prompt)
    
    if response is None:
        return Response({
            'error': 'GPT API 호출에 실패했습니다.',
            'debug_info': f'API 키: {api_key[:10]}... (앞 10자리만 표시)'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'prompt': prompt,
        'response': response,
        'message': 'GPT API 호출 성공!'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def recommend_stores(request):
    """가게 추천 API"""
    closed_store_info = request.data.get('closed_store_info', '')
    nearby_stores = request.data.get('nearby_stores', [])
    
    if not closed_store_info:
        return Response({
            'error': '폐업한 가게 정보를 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not nearby_stores:
        return Response({
            'error': '주변 가게 목록을 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # GPT를 통한 가게 추천
    recommendation = get_store_recommendation(closed_store_info, nearby_stores)
    
    if recommendation is None:
        return Response({
            'error': '가게 추천에 실패했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'closed_store_info': closed_store_info,
        'nearby_stores': nearby_stores,
        'recommendation': recommendation,
        'message': '가게 추천이 완료되었습니다!'
    }, status=status.HTTP_200_OK)



# --------------- Place (추천가게) ----------------

class PlaceCreateView(generics.CreateAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [AllowAny] # permission 걸고싶으면 permissions.IsAuthenticated로 다시 수정하기 

    
    def perform_create(self, serializer):
        place = serializer.save()
        AISummary.objects.create(shop=place, summary="gpt 요약이 들어갈 곳!!") ## 아직 gpt 연결 안 함! 더미데이터 넣어서 생성.


class PlaceDetailView(generics.RetrieveAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    lookup_field = "shop_id"
    permission_classes = [permissions.AllowAny]


# --------------- SavedPlace (감정보관함) ----------------

class SavedPlaceCreateView(generics.CreateAPIView):
    queryset = SavedPlace.objects.all()
    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavedPlaceListView(generics.ListAPIView):
    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user).order_by("-created_date")


class SavedPlaceDeleteView(generics.DestroyAPIView):
    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "saved_id"

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user)


# --------------- AISummary (요약) ----------------

class AISummaryDetailView(generics.RetrieveAPIView):
    serializer_class = AISummarySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "shop_id"

    def get_queryset(self):
        return AISummary.objects.all()