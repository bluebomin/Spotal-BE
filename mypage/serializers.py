from rest_framework import serializers
from community.models import Bookmark, Memory, Image
from recommendations.models import SavedPlace
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "detail"]

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image_url"]

class CommunitySummarySerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True) 
    class Meta:
        model = Memory
        fields = ["images"]

class BookmarkSerializer(serializers.ModelSerializer):
    post = CommunitySummarySerializer(source="memory") 
    class Meta:
        model = Bookmark
        fields = ["created_date", "post"]



class SavedPlaceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="shop.name", read_only=True)
    address = serializers.CharField(source="shop.address", read_only=True)
    image_url = serializers.CharField(source="shop.image_url", read_only=True)
    emotions = serializers.SlugRelatedField(
        source="shop.emotions",
        many=True,
        read_only=True,
        slug_field="name"
    )
    summary = serializers.CharField(source="summary_snapshot", read_only=True)

    class Meta:
        model = SavedPlace
        fields = [
            "name",
            "address",
            "image_url",
            "emotions",
            "summary",
        ]
