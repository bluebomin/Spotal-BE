from rest_framework import serializers
from .models import UserInferenceSession, Place, AISummary

class PlaceSerializer(serializers.ModelSerializer):
    """장소 정보 시리얼라이저 - recommendations와 동일한 구조"""
    emotions = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='emotions'
    )
    location = serializers.CharField(source='location.name', read_only=True)
    ai_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'emotions', 'location',
            'ai_summary', 'image_url', 'created_date', 'modified_date'
        ]
        read_only_fields = ['shop_id', 'created_date', 'modified_date']
    
    def get_ai_summary(self, obj):
        """Place와 연결된 AISummary 중 최신 하나 가져오기"""
        summary = obj.ai_summary.order_by("-created_date").first()
        return summary.summary if summary else None

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

class RecommendationResultSerializer(serializers.ModelSerializer):
    """추천 결과 응답용 시리얼라이저 - recommendations와 동일한 구조"""
    emotions = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='emotions'
    )
    location = serializers.CharField(source='location.name', read_only=True)
    ai_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'emotions', 'location',
            'ai_summary', 'image_url', 'created_date', 'modified_date'
        ]
        read_only_fields = ['shop_id', 'created_date', 'modified_date']
    
    def get_ai_summary(self, obj):
        """Place와 연결된 AISummary 중 최신 하나 가져오기"""
        summary = obj.ai_summary.order_by("-created_date").first()
        return summary.summary if summary else None
