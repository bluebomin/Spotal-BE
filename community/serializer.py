# serializers.py
from rest_framework import serializers
from .models import *
from .ImageSerializer import ImageSerializer

class EmotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = emotion
        fields = '__all__' 


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = location
        fields = '__all__'


class MemorySerializer(serializers.ModelSerializer):
    # 입력용: PK 목록/단일 PK를 받아서 모델의 실제 필드(emotion_id/location_id)에 매핑
    emotion_ids = serializers.PrimaryKeyRelatedField(
        source='emotion_id',              
        queryset=emotion.objects.all(),
        many=True,
        required=False
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=location.objects.all(),
        required=False,
        allow_null=True
    )

    # 출력용: 태그 상세를 함께 내려주고 싶을 때
    emotions = EmotionSerializer(source='emotion_id', many=True, read_only=True)
    location = LocationSerializer(source='location_id', read_only=True) #read_only=True는 출력에만

    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = memory
        fields = [
            'memory_id', 'user_id',  'content',
            'emotion_ids', 'location_id',        # 입력용
            'emotions', 'location',              # 출력용
            'created_at', 'updated_at','images'
        ]

    def validate(self, attrs):
        # 감정 최대 3개 제한
        emotions = attrs.get('emotion_id', None)  # source에서 매핑된 키 사용
        if emotions is None and self.instance is not None:
            emotions = self.instance.emotion_id.all()
        if emotions is not None and len(emotions) > 3:
            raise serializers.ValidationError({"emotion_ids": "감정 태그는 최대 3개까지 선택 가능합니다."})
        return attrs

