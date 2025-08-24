from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from .models import Place, SavedPlace, AISummary
from .serializers import *
from rest_framework.views import APIView
from search.service.summary_card import generate_summary_card, generate_emotion_tags
from search.service.address import translate_to_korean
from .services.google_service import get_similar_places, get_place_details, get_photo_url
from .services.utils import extract_neighborhood
from .services.emotion_service import expand_emotions_with_gpt   
from infer.models import AISummary as InferAISummary


# Create your views here.

# 추천가게 생성 
class RecommendationView(APIView):
    """추천 가게 생성 & 응답 API"""
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name")
        address = request.data.get("address")
        emotion_tags = request.data.get("emotion_tags", [])

        # --- 필수 입력값 체크 ---
        if not name or not address or not emotion_tags:
            return Response(
                {"error": "name, address, emotion_tags는 필수 입력값입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- 업태 구분 (카테고리) ---
        category_str = request.data.get("category", "")
        if "cafe" in category_str.lower():
            allowed_types = ["cafe"]
        else:
            allowed_types = ["restaurant", "food"]

        try:
            # 1. GPT 기반 감정 확장
            emotions = expand_emotions_with_gpt(emotion_tags)   # -> Emotion 객체 QuerySet
            emotion_names = [e.name for e in emotions]          # → 문자열 리스트로 변환

            # 2. 구글맵에서 유사 가게 검색
            candidate_places = get_similar_places(
                address,
                emotion_names,
                allowed_types=allowed_types
            )[:8]

            response_data = []

            # 3. 후보 가게 상세 처리
            for c in candidate_places:
                place_id = c.get("place_id")
                place_name = c.get("name")

                # 구글 Place 상세 정보 가져오기
                details = get_place_details(place_id, place_name)
                reviews = [r["text"] for r in details.get("reviews", [])]
                uptaenms = details.get("types", [])

                # 주소/이름 한국어 정규화
                name_ko = translate_to_korean(details.get("name")) if details.get("name") else None
                address_ko = translate_to_korean(details.get("formatted_address")) if details.get("formatted_address") else None

                # GPT 요약 + 감정태그 생성
                if reviews:  
                    summary = generate_summary_card(details, reviews, uptaenms) or "요약 준비중입니다"
                else:
                    neighborhood = extract_neighborhood(address_ko or c.get("address"))
                    summary = f"{place_name}은 {neighborhood}에 위치한 가게입니다"

                tags = generate_emotion_tags(details, reviews, uptaenms) or []

                # Emotion 모델 매핑 (입력 감정 + 자동 생성 감정)
                emotion_objs = list(emotions)  # GPT 확장된 감정
                for tag_name in tags:
                    obj, _ = Emotion.objects.get_or_create(name=tag_name)
                    emotion_objs.append(obj)

                # Location 매핑
                neighborhood_name = extract_neighborhood(address_ko)
                location_obj, _ = Location.objects.get_or_create(name=neighborhood_name)

                # Place 저장
                place = Place.objects.create(
                    name=name_ko or place_name,
                    address=address_ko or c.get("address"),
                    image_url=c.get("image_url", ""),
                    location=location_obj,
                )
                place.emotions.set(emotion_objs)

                # AISummary 저장
                AISummary.objects.create(shop=place, summary=summary)

                # 직렬화 데이터 추가
                response_data.append(PlaceSerializer(place).data)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"추천 생성 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




# --------------- Place (추천가게) ----------------



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

    # summary_snapshot에 최신 ai요약 저장해 놓기 
    def perform_create(self, serializer):
        saved_place = serializer.save()

        # 추천 로직에 따라 최신요약 저장 로직 분기
        last_summary = None
        if saved_place.rec == 1:
            # 추천1에서 저장한 경우
            last_summary = saved_place.shop.ai_summary.order_by("-created_date").first()
        elif saved_place.rec == 2:
            # 추천2에서 저장한 경우
            last_summary = InferAISummary.objects.filter(place_id=saved_place.shop_id).order_by("-created_date").first()

        if last_summary:
            saved_place.summary_snapshot = last_summary.summary
            saved_place.save()



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
    serializer_class = SavedPlaceCreateSerializer
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