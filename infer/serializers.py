from rest_framework import serializers
from .models import UserInferenceSession, Place, AISummary

class PlaceSerializer(serializers.ModelSerializer):
    """장소 정보 시리얼라이저 - recommendations와 동일한 구조"""
    emotions = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='emotions.all'  # .all을 추가하여 쿼리셋을 명시적으로 가져옴
    )
    location = serializers.CharField(source='location.name', read_only=True)
    ai_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'emotions', 'location',
            'ai_summary', 'image_url', 'status', 'created_date', 'modified_date'
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
    location_names = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='selected_location'
    )
    emotion_names = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='selected_emotions'
    )
    
    class Meta:
        model = UserInferenceSession
        fields = [
            'session_id', 'user', 'location_names', 'emotion_names', 'created_at'
        ]
        read_only_fields = ['session_id', 'user', 'created_at']

class UserInferenceSessionCreateSerializer(serializers.ModelSerializer):
    """사용자 추론 세션 생성용 시리얼라이저"""
    selected_location = serializers.SerializerMethodField()
    selected_emotions = serializers.SerializerMethodField()
    
    class Meta:
        model = UserInferenceSession
        fields = ['selected_location', 'selected_emotions']
    
    def get_selected_location(self, obj):
        # 이 메서드는 사용되지 않지만 필수
        return []
    
    def get_selected_emotions(self, obj):
        # 이 메서드는 사용되지 않지만 필수
        return []
    
    def validate(self, data):
        """전체 데이터 검증"""
        # request.data에서 직접 값을 가져오기
        request = self.context.get('request')
        if request:
            selected_location = request.data.get('selected_location')
            selected_emotions = request.data.get('selected_emotions')
            
            # 단일 정수값을 리스트로 변환
            if isinstance(selected_location, int):
                selected_location = [selected_location]
            if isinstance(selected_emotions, int):
                selected_emotions = [selected_emotions]
            
            # 검증
            if not selected_location or len(selected_location) == 0:
                raise serializers.ValidationError("최소 1개의 동네를 선택해주세요.")
            if len(selected_location) > 3:
                raise serializers.ValidationError("동네는 최대 3개까지 선택 가능합니다.")
            
            if not selected_emotions or len(selected_emotions) == 0:
                raise serializers.ValidationError("최소 1개의 감정 태그를 선택해주세요.")
            if len(selected_emotions) > 3:
                raise serializers.ValidationError("감정 태그는 최대 3개까지 선택 가능합니다.")
            
            # 검증된 데이터를 validated_data에 추가
            data['selected_location'] = selected_location
            data['selected_emotions'] = selected_emotions
        
        return data

class RecommendationResultSerializer(serializers.ModelSerializer):
    """추천 결과 응답용 시리얼라이저 - recommendations와 동일한 구조"""
    emotions = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name',
        source='emotions.all'  # .all을 추가하여 쿼리셋을 명시적으로 가져옴
    )
    location = serializers.CharField(source='location.name', read_only=True)
    ai_summary = serializers.SerializerMethodField()
    rec = serializers.SerializerMethodField()
    
    class Meta:
        model = Place
        fields = [
            'shop_id', 'name', 'address', 'emotions', 'location',
            'ai_summary', 'image_url', 'status', 'created_date', 'modified_date', 'rec'
        ]
        read_only_fields = ['shop_id', 'created_date', 'modified_date']
    
    def get_ai_summary(self, obj):
        """Place와 연결된 AISummary 중 최신 하나 가져오기"""
        summary = obj.ai_summary.order_by("-created_date").first()
        return summary.summary if summary else None
    
    def get_rec(self, obj):
        return 2 
