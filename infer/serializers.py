from rest_framework import serializers
from .models import UserInferenceSession, InferenceRecommendation, Place, AISummary
from community.serializers import LocationSerializer, EmotionSerializer

class PlaceSerializer(serializers.ModelSerializer):
    """장소 정보 시리얼라이저"""
    emotions = EmotionSerializer(many=True, read_only=True)
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'image_url', 
            'emotions', 'location', 'created_date', 'modified_date'
        ]
        read_only_fields = ['shop_id', 'created_date', 'modified_date']

class AISummarySerializer(serializers.ModelSerializer):
    """AI 요약 시리얼라이저"""
    place = PlaceSerializer(read_only=True)
    
    class Meta:
        model = AISummary
        fields = ['summary_id', 'place', 'summary', 'created_date', 'modified_date']
        read_only_fields = ['summary_id', 'created_date', 'modified_date']

class UserInferenceSessionSerializer(serializers.ModelSerializer):
    """사용자 추론 세션 시리얼라이저"""
    selected_location = LocationSerializer(read_only=True)
    selected_emotions = EmotionSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserInferenceSession
        fields = [
            'session_id', 'user', 'selected_location', 'selected_emotions', 
            'created_at'
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
    """추론 추천 결과 시리얼라이저"""
    session = UserInferenceSessionSerializer(read_only=True)
    place = PlaceSerializer(read_only=True)
    
    class Meta:
        model = InferenceRecommendation
        fields = ['recommendation_id', 'session', 'place', 'created_at']
        read_only_fields = ['recommendation_id', 'session', 'place', 'created_at']
