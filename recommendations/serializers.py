from rest_framework import serializers
from .models import *
from community.models import *
from .services.google_service import get_photo_url


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
    status = serializers.SerializerMethodField()
    rec = serializers.SerializerMethodField()  
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            "shop_id",
            "name",
            "address",
            "rec",
            "emotions",      # [ "정겨움", "힐링" ] 
            "location",      # "청파동"
            "ai_summary",
            "image_url", # 동적으로 생성되게 됨!! 
            "status",
            "created_date",
            "modified_date"
        )
        read_only_fields = ("shop_id", "created_date", "modified_date")

    def get_ai_summary(self, obj):
        request = self.context.get("request")
        rec = None
        if request:
            rec = request.query_params.get("rec") or request.data.get("rec")

        if str(rec) == "2":
            summary_obj = obj.infer_ai_summary.order_by("-created_date").first()
        else:
            summary_obj = obj.ai_summary.order_by("-created_date").first()

        return summary_obj.summary if summary_obj else None
    
    def get_status(self, obj):
        return obj.get_status_display() if obj.status else None

    def get_rec(self, obj):
        return 1 
    
    def get_image_url(self, obj):
        if obj.photo_reference:
            return get_photo_url(obj.photo_reference)
        return None




# 사용자가 보관한 추천 가게 (SavedPlace)

# 1. 저장(Create/Update)용
class SavedPlaceCreateSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all())

    class Meta:
        model = SavedPlace
        fields = ("saved_id", "shop", "user", "rec", "created_date")
        read_only_fields = ("saved_id", "created_date") # user는 body에서 직접 넘기도록 


# 2. 조회(Read)용
class SavedPlaceSerializer(serializers.ModelSerializer):
    shop_id = serializers.IntegerField(source="shop.shop_id", read_only=True)
    name = serializers.CharField(source="shop.name", read_only=True)
    address = serializers.CharField(source="shop.address", read_only=True)
    location = serializers.CharField(source="shop.location.name", read_only=True)
    summary = serializers.SerializerMethodField()
    emotions = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
        source="shop.emotions"   # Place.emotions → string 배열
    )
    status = serializers.SerializerMethodField()    
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SavedPlace
        fields = (
            "saved_id",
            "shop_id",
            "user_id",
            "name",
            "address",
            "emotions",
            "location",
            "image_url", # 동적 url로 바꿈!!! 
            "summary",
            "status",
            "created_date",
            "rec",
        )
        read_only_fields = ("saved_id", "created_date")

    def get_summary(self, obj):
        if obj.rec == 2:
            summary = obj.shop.infer_ai_summary.order_by("-created_date").first()
        else:
            summary = obj.shop.ai_summary.order_by("-created_date").first()
        return summary.summary if summary else None
    
    def get_status(self, obj):
        return "운영중"  
    
    def get_image_url(self, obj):
        if obj.shop.photo_reference:
            return get_photo_url(obj.shop.photo_reference)
        return None