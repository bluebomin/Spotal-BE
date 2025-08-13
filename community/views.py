
from rest_framework import viewsets
from .models import memory
from .serializer import MemorySerializer, EmotionSerializer, LocationSerializer 
from .models import emotion, location
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError   


#Viewset

class EmotionViewSet(viewsets.ModelViewSet):
    queryset = emotion.objects.all().order_by('pk')
    serializer_class = EmotionSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = location.objects.all().order_by('pk')
    serializer_class = LocationSerializer

class MemoryViewSet(viewsets.ModelViewSet):
    queryset = memory.objects.all().order_by('-created_at')
    serializer_class = MemorySerializer

    @action(detail=False, methods=['get'], url_path='tag-options')
    def tag_options(self, request):
        emotions = emotion.objects.all().order_by('pk')
        locations = location.objects.all().order_by('pk')
        return Response({
            'emotions': EmotionSerializer(emotions, many=True).data,   # ✅ 인스턴스화
            'locations': LocationSerializer(locations, many=True).data # ✅ 인스턴스화
        })

    # ✅ 커스텀 필터는 get_queryset에서 처리 (400 밸리데이션 포함)
    def get_queryset(self):
        qs = super().get_queryset() \
            .select_related('location_id') \
            .prefetch_related('emotion_id')

        params = self.request.query_params

        # 위치 필터
        loc = params.get('location_id')
        if loc is not None:
            if not str(loc).isdigit():
                raise ValidationError({"location_id": "정수 ID여야 합니다."})
            loc = int(loc)
            if not location.objects.filter(pk=loc).exists():
                raise ValidationError({"location_id": "존재하지 않는 위치 ID입니다."})
            qs = qs.filter(location_id=loc)  # ✅ FK 이름이 location_id이므로 그대로 비교

        # 감정 필터
        raw = params.get('emotion_ids')
        if raw:
            try:
                ids = [int(x) for x in raw.split(',') if x.strip()]
            except ValueError:
                raise ValidationError({"emotion_ids": "정수 ID 목록이어야 합니다."})
            if not ids:
                raise ValidationError({"emotion_ids": "최소 1개 이상의 ID를 입력하세요."})

            # 존재 여부 확인
            missing = [i for i in ids if not emotion.objects.filter(pk=i).exists()]
            if missing:
                raise ValidationError({"emotion_ids": f"존재하지 않는 감정 ID: {missing}"})

            # 필터링은 AND 조건으로
            qs = qs.annotate(
                sel_count=Count('emotion_id', filter=Q(emotion_id__in=ids), distinct=True)
            ).filter(sel_count=len(ids))

        return qs