from rest_framework import serializers
from .models import Place, AISummary, SavedPlace


# AI 추천 가게 정보
class PlaceSerializer(serializers.ModelSerializer):
    emotion_name = serializers.CharField(source="emotion.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)

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
            "created_date",
            "modified_date",
        )
        read_only_fields = ("shop_id", "created_date", "modified_date")


# AI 요약 정보
class AISummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = AISummary
        fields = ("summary_id", "shop", "summary")
        read_only_fields = ("summary_id")


# 사용자가 보관한 추천 가게
class SavedPlaceSerializer(serializers.ModelSerializer):
    shop = PlaceSerializer(read_only=True)  # 가게 정보도 같이 보여줌 

    class Meta:
        model = SavedPlace
        fields = ("saved_id", "shop", "created_date")
        read_only_fields = ("saved_id", "created_date")
