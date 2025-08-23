from rest_framework import serializers
from .models import UserInferenceSession, InferenceRecommendation, Place, AISummary
from community.serializers import LocationSerializer, EmotionSerializer

class PlaceSerializer(serializers.ModelSerializer):
    """장소 정보 시리얼라이저"""
    # 중첩된 객체 대신 직접 필드 노출
    location_name = serializers.CharField(source='location.name', read_only=True)
    emotion_names = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='emotions'
    )
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'image_url', 
            'location_name', 'emotion_names', 'created_date', 'modified_date'
        ]
        read_only_fields = ['shop_id', 'created_date', 'modified_date']

class AISummarySerializer(serializers.ModelSerializer):
    """AI 요약 시리얼라이저"""
    # place 정보를 직접 필드로 노출
    shop_id = serializers.IntegerField(source='place.shop_id', read_only=True)
    place_name = serializers.CharField(source='place.name', read_only=True)
    place_address = serializers.CharField(source='place.address', read_only=True)
    place_image_url = serializers.CharField(source='place.image_url', read_only=True)
    
    class Meta:
        model = AISummary
        fields = [
            'summary_id', 'shop_id', 'place_name', 'place_address', 'place_image_url',
            'summary', 'created_date', 'modified_date'
        ]
        read_only_fields = ['summary_id', 'created_date', 'modified_date']

class UserInferenceSessionSerializer(serializers.ModelSerializer):
    """사용자 추론 세션 시리얼라이저"""
    # 중첩된 객체 대신 직접 필드 노출
    location_name = serializers.CharField(source='selected_location.name', read_only=True)
    emotion_names = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='selected_emotions'
    )
    
    class Meta:
        model = UserInferenceSession
        fields = [
            'session_id', 'user', 'location_name', 'emotion_names', 'created_at'
        ]
        read_only_fields = ['session_id', 'user', 'created_at']

class UserInferenceSessionCreateSerializer(serializers.ModelSerializer):
    """사용자 추론 세션 생성용 시리얼라이저"""
    selected_location = serializers.IntegerField(write_only=True)
    selected_emotions = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = UserInferenceSession
        fields = ['selected_location', 'selected_emotions']
    
    def validate_selected_emotions(self, value):
        """감정 태그 검증 (최대 3개)"""
        if len(value) > 3:
            raise serializers.ValidationError("감정 태그는 최대 3개까지 선택 가능합니다.")
        if len(value) == 0:
            raise serializers.ValidationError("최소 1개의 감정 태그를 선택해주세요.")
        return value

class InferenceRecommendationSerializer(serializers.ModelSerializer):
    """추론 추천 결과 시리얼라이저 - flat한 구조"""
    # session 정보를 직접 필드로 노출
    session_id = serializers.IntegerField(source='session.session_id', read_only=True)
    location_name = serializers.CharField(source='session.selected_location.name', read_only=True)
    emotion_names = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='session.selected_emotions'
    )
    
    # place 정보를 직접 필드로 노출
    shop_id = serializers.IntegerField(source='place.shop_id', read_only=True)
    place_name = serializers.CharField(source='place.name', read_only=True)
    place_address = serializers.CharField(source='place.address', read_only=True)
    place_image_url = serializers.CharField(source='place.image_url', read_only=True)
    
    class Meta:
        model = InferenceRecommendation
        fields = [
            'recommendation_id', 'session_id', 'location_name', 'emotion_names',
            'shop_id', 'place_name', 'place_address', 'place_image_url', 'created_at'
        ]
        read_only_fields = ['recommendation_id', 'created_at']

class FlatPlaceRecommendationSerializer(serializers.Serializer):
    """프론트엔드용 추천 결과 시리얼라이저"""
    # 기본 정보
    place_id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    image_url = serializers.CharField()
    
    # 감정 및 요약
    emotion_tags = serializers.ListField(child=serializers.CharField())
    summary = serializers.CharField()
    
    # 메타 정보
    google_rating = serializers.FloatField()
    user_ratings_total = serializers.IntegerField()
    place_types = serializers.ListField(child=serializers.CharField())
    
    # 세션 정보
    session_id = serializers.IntegerField()
    location_name = serializers.CharField()
    selected_emotions = serializers.ListField(child=serializers.CharField())
