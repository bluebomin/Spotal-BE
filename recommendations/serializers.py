from rest_framework import serializers
from .models import Place, AISummary, SavedPlace


# AI 요약 정보
class AISummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = AISummary
        fields = ("summary_id", "summary")
        read_only_fields = ("summary_id",)

# AI 추천 가게 정보
class PlaceSerializer(serializers.ModelSerializer):
    emotion_name = serializers.CharField(source="emotion.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    ai_summary = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            "shop_id",
            "name",
            "address",
            "emotion",       # id
            "emotion_name",  # name (정겨움, 세심함 등)
            "location",      # id
            "location_name", # name (효창동, 후암동 등)
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
