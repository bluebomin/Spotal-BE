from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from .services import call_gpt_api
from .models import Place, SavedPlace, AISummary
from .serializers import *
from .services import call_gpt_api


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
    recommendation = call_gpt_api(closed_store_info, nearby_stores)
    
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
    permission_classes = [AllowAny]

    
    def perform_create(self, serializer):
        place = serializer.save()

        # GPT 요약 생성
        from .services import generate_gpt_emotion_based_recommendations
        summary_text = generate_gpt_emotion_based_recommendations(place)
        # AI Summary 저장 
        AISummary.objects.create(shop=place, summary=summary_text) 


class PlaceDetailView(generics.RetrieveAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    lookup_field = "shop_id"
    permission_classes = [permissions.AllowAny]


# --------------- SavedPlace (감정보관함) ----------------

class SavedPlaceCreateView(generics.CreateAPIView):
    queryset = SavedPlace.objects.all()
    serializer_class = SavedPlaceCreateSerializer
    permission_classes = [permissions.AllowAny]



class SavedPlaceListView(generics.ListAPIView):
    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.AllowAny]

    # user별 필터링해서 목록 보여줌. 
    def get_queryset(self):
        user_id = self.request.query_params.get("user")  # 쿼리 파라미터로 받기
        if user_id:
            return SavedPlace.objects.filter(user_id=user_id).order_by("-created_date")
        return SavedPlace.objects.all().order_by("-created_date")
        


class SavedPlaceDeleteView(generics.DestroyAPIView):
    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "saved_id"

    def get_queryset(self):
        return SavedPlace.objects.all()
    
    # 삭제되었다고 응답 띄우기
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data  
        self.perform_destroy(instance)
        return Response(
            {"message": "저장한 장소가 삭제되었습니다.", "deleted_place": data},
            status=status.HTTP_200_OK
        )


# --------------- AISummary (요약) ----------------

# AISummary만 따로 조회
class AISummaryDetailView(generics.RetrieveAPIView):
    serializer_class = AISummarySerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        shop_id = self.kwargs.get("shop_id")
        return AISummary.objects.get(shop__shop_id=shop_id)
    

# AISummary만 따로 생성 (요약 재생성 요청 시 필요)
class AISummaryCreateUpdateView(generics.CreateAPIView):

    serializer_class = AISummarySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, shop_id):
        try:
            place = Place.objects.get(shop_id=shop_id)
        except Place.DoesNotExist:
            return Response({"error": "해당 가게가 존재하지 않습니다."}, status=404)

        # GPT 요약 생성
        from .services import generate_gpt_emotion_based_recommendations
        summary_text = generate_gpt_emotion_based_recommendations(place)

        # 기존 요약 있으면 업데이트, 없으면 새로 생성
        aisummary, created = AISummary.objects.update_or_create(
            shop=place,
            defaults={"summary": summary_text}
        )

        return Response(
            {
                "message": "AI 요약 생성 완료" if created else "AI 요약 갱신 완료",
                "data": AISummarySerializer(aisummary).data
            },
            status=201 if created else 200
        )