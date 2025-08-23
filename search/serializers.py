from rest_framework import serializers
from community.serializers import EmotionSerializer
from .models import SearchShop
from community.models import Emotion

class SearchShopSerializer(serializers.ModelSerializer):
    emotion_ids = serializers.PrimaryKeyRelatedField(
        source='emotion_id',
        queryset=Emotion.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    
    emotions = EmotionSerializer(source='emotion_id', many=True, read_only=True)
    previous_address = serializers.SerializerMethodField()
    previous_lat = serializers.SerializerMethodField()
    previous_lng = serializers.SerializerMethodField()

    class Meta:
        model = SearchShop
        fields = ['shop_id', 'emotion_ids','emotions', 'name', 'address', 'status', 'uptaenm','previous_address', 'previous_lat', 'previous_lng']
        read_only_fields = ['shop_id']

    def get_previous_address(self, obj):
        # obj가 dict일 수도 있고 모델 인스턴스일 수도 있음
        return self.context.get('previous_address', None)
    
    def get_previous_lat(self, obj):
        return self.context.get('previous_lat', None)
    def get_previous_lng(self, obj):
        return self.context.get('previous_lng', None)
    
   