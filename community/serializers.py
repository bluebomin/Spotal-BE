from rest_framework import serializers
from .models import *
from .ImageSerializer import ImageSerializer

class EmotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emotion
        fields = '__all__' 


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class MemorySerializer(serializers.ModelSerializer):
    # 입력용: PK 목록/단일 PK를 받아서 모델의 실제 필드(emotion_id/location_id)에 매핑
    emotion_id = serializers.PrimaryKeyRelatedField(
    queryset=Emotion.objects.all(),
    many=True,
    required=False,
    write_only=True
    )
    location_id = serializers.PrimaryKeyRelatedField(
    source='location',  # ForeignKey 필드명과 맞추기
    queryset=Location.objects.all(),
    required=False,
    allow_null=True,
    write_only=True
    )

    # 출력용: 태그 상세를 함께 내려주고 싶을 때
    emotions = EmotionSerializer(source='emotion_id', many=True, read_only=True)
    location = LocationSerializer(read_only=True) #read_only=True는 출력에만
    images = serializers.SerializerMethodField() 
    nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = Memory
        fields = [
            'memory_id', 'user_id',"nickname",  'content',
            'emotion_id', 'location_id',        # 입력용
            'emotions', 'location',              # 출력용
            'created_at', 'updated_at','images'
        ]
        read_only_fields = ['user_id']

    def validate(self, attrs):
        # 감정 최대 3개 제한
        emotions = attrs.get('emotion_id', None)  # source에서 매핑된 키 사용
        if emotions is None and self.instance is not None:
            emotions = self.instance.emotion_id.all()
        if emotions is not None and len(emotions) > 3:
            raise serializers.ValidationError({"emotion_id": "감정 태그는 최대 3개까지 선택 가능합니다."})
        return attrs
    
    def get_images(self, obj):
        return [
            {
                "image_id": img.image_id,
                "image_url": img.image_url
            }
            for img in obj.images.all()
            ]




class BookmarkSerializer(serializers.ModelSerializer):
    memory_content = serializers.CharField(source="memory.content", read_only=True)

    class Meta:
        model = Bookmark
        fields = ["bookmark_id", "memory", "user", "memory_content", "created_date"]
        read_only_fields = ["user", "created_date"]

class CommentSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = Comment
        fields = ['comment_id', 'memory', 'user', 'nickname', 'content', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']