from rest_framework import serializers
from .models import User, Bookmark, SavedPlace, Community, Place, Image

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "nickname", "detail"]

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image_id", "image_url", "image_name"]

class CommunitySummarySerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True) 
    class Meta:
        model = Community
        fields = ["id", "images"]

class BookmarkSerializer(serializers.ModelSerializer):
    post = CommunitySummarySerializer(source="memory") 
    class Meta:
        model = Bookmark
        fields = ["id", "created_date", "post"]

'''
class PlaceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["id", "name", "status", "address", "summary", "image"]

class SavedPlaceSerializer(serializers.ModelSerializer):
    shop = PlaceSummarySerializer()

    class Meta:
        model = SavedPlace
        fields = ["id", "shop"]

'''
