from rest_framework import serializers
from .models import *
from community.models import *


# AI 요약 정보
class AISummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = AISummary
        fields = ("summary_id", "summary", "created_date")
        read_only_fields = ("summary_id", "created_date")

# AI 추천 가게 정보
class PlaceSerializer(serializers.ModelSerializer):
    emotions = serializers.SlugRelatedField( # emotions 여러 개 내려줄 수 있도록 수정
        many=True,
        read_only=True,
        slug_field="name"   # Emotion 모델의 name 필드 사용
    )   
    location = serializers.CharField(source="location.name", read_only=True)
    ai_summary = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            "shop_id",
            "name",
            "address",
            "emotions",      # [ "정겨움", "힐링" ] 
            "location",      # "청파동"
            "ai_summary",
            "image_url",
            "created_date",
            "modified_date",
        )
        read_only_fields = ("shop_id", "created_date", "modified_date")

    def get_ai_summary(self, obj):
        # Place와 연결된 AISummary 중 최신 하나 가져오기
        summary = obj.ai_summary.order_by("-created_date").first()
        return summary.summary if summary else None




# 사용자가 보관한 추천 가게 (SavedPlace)

# 1. 저장(Create/Update)용
class SavedPlaceCreateSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all())

    class Meta:
        model = SavedPlace
        fields = ("saved_id", "shop", "user", "created_date")
        read_only_fields = ("saved_id", "created_date") # user는 body에서 직접 넘기도록 


# 2. 조회(Read)용
class SavedPlaceSerializer(serializers.ModelSerializer):
    shop = PlaceSerializer(read_only=True)  # Place 전체 정보 반환

    class Meta:
        model = SavedPlace
        fields = ("saved_id", "shop", "user", "created_date")
        read_only_fields = ("saved_id", "created_date")
