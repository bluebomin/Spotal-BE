from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from .models import Place, SavedPlace, AISummary
from .serializers import *
from rest_framework.views import APIView
from .services.recommendation_service import generate_recommendations

# Create your views here.

# 추천가게 생성 
class RecommendationView(APIView):
    """추천 가게 생성 & 응답 API"""
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name")
        address = request.data.get("address")
        emotion_names = request.data.get("emotion_tags", [])

        if not name or not address or not emotion_names:
            return Response(
                {"error": "name, address, emotion_tags는 필수 입력값입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 추천 로직 실행 (Google + GPT)
            candidate_places = generate_recommendations(name, address, emotion_names)[:8]  # 최대 8개 추천

            response_data = []
            for place_data in candidate_places:
                # Place 저장
                place = Place.objects.create(
                    name=place_data["name"],
                    address=place_data["address"],
                    image_url=place_data.get("image_url", ""),
                    location=place_data["location_obj"]
                )
                place.emotions.set(place_data["emotion_objs"])

                # AISummary 저장
                AISummary.objects.create(shop=place, summary=place_data["summary"])

                # 직렬화해서 응답 데이터에 추가
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
        # 해당 Place의 최신 요약 가져오기
        last_summary = saved_place.shop.ai_summary.order_by("-created_date").first()
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