from rest_framework import serializers
from community.models import Bookmark
from recommendations.models import SavedPlace
from recommendations.services.google_service import get_photo_url
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["nickname", "detail"]
        read_only_fields = ["detail"] # 우선 세부설명은 수정 못하도록 명시해둠. 


class BookmarkSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ["images"]

    def get_images(self, obj):
        return [image.image_url for image in obj.memory.images.all()]
    # 북마크된 커뮤니티 게시글(memory)에 연결된 이미지들의 url만 추출


class SavedPlaceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="shop.name", read_only=True)
    address = serializers.CharField(source="shop.address", read_only=True)
    image_url = serializers.SerializerMethodField() 
    emotions = serializers.SlugRelatedField(
        source="shop.emotions",
        many=True,
        read_only=True,
        slug_field="name"
    )
    summary = serializers.CharField(source="summary_snapshot", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = SavedPlace
        fields = [
            "name",
            "address",
            "image_url",
            "emotions",
            "summary",
            "status"
        ]

    # 우선 추천 1은 운영중 뜨도록 함
    def get_status(self, obj):
        return "운영중"
    
    def get_image_url(self, obj):
        if obj.shop.photo_reference:
            return get_photo_url(obj.shop.photo_reference)
        return None