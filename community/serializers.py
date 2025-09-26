from rest_framework import serializers
from .models import *
from .ImageSerializers import *

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields ='__all__'

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
    board_id = serializers.PrimaryKeyRelatedField(
    source ='board',
    queryset=Board.objects.all(),
    required=False,
    write_only=True
    )
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
    board = BoardSerializer(read_only=True)
    emotions = EmotionSerializer(source='emotion_id', many=True, read_only=True)
    location = LocationSerializer(read_only=True) #read_only=True는 출력에만
    images = serializers.SerializerMethodField() 
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    profile_image_url = serializers.SerializerMethodField() 
    comment_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Memory
        fields = [
            'memory_id', 'user_id',"nickname", "profile_image_url", 'content','board_id',
            'emotion_id', 'location_id',        # 입력용
            'board','emotions', 'location', 'comment_count',             # 출력용
            'created_at', 'updated_at','images'
        ]
        

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
    
    def get_profile_image_url(self, obj):
        if obj.user and obj.user.profile_image_url:
            return obj.user.profile_image_url
        return None
    
    def get_comment_count(self, obj):
        return obj.comments.count()

class BookmarkSerializer(serializers.ModelSerializer):
    memory_content = serializers.CharField(source="memory.content", read_only=True)

    class Meta:
        model = Bookmark
        fields = ["bookmark_id", "memory", "user", "memory_content", "created_date"]
        

class CommentSerializer(serializers.ModelSerializer):
    memory_id = serializers.PrimaryKeyRelatedField(source='memory', queryset=Memory.objects.all(),required=False)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    profile_image_url = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['comment_id', 'memory_id', 'user_id', 'nickname', 'profile_image_url', 'content', 'created_at', 'updated_at', 'parent', 'replies']
       

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []
    
    def get_profile_image_url(self, obj):
        if obj.user and obj.user.profile_image_url:
            return obj.user.profile_image_url
        return None
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not self.context.get("include_replies",False):
            ret.pop("replies",None)
        return ret