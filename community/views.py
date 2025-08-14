
import os
from rest_framework import viewsets, status
from .models import memory
from .serializer import *
from .models import emotion, location
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError 
from .ImageSerializer import ImageSerializer  
from django.conf import settings
from django.core.files.storage import default_storage
from .utils import s3_key_from_url
from rest_framework.parsers import MultiPartParser, FormParser
from .models import image

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
    parser_classes = [MultiPartParser, FormParser]  # 이미지 + 텍스트 같이 받으려면 필요

    @action(detail=False, methods=['get'], url_path='tag-options')
    def tag_options(self, request):
        emotions = emotion.objects.all().order_by('pk')
        locations = location.objects.all().order_by('pk')
        return Response({
            'emotions': EmotionSerializer(emotions, many=True).data,
            'locations': LocationSerializer(locations, many=True).data
        })

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
            qs = qs.filter(location_id=loc)

        # 감정 필터
        raw = params.get('emotion_ids')
        if raw:
            try:
                ids = [int(x) for x in raw.split(',') if x.strip()]
            except ValueError:
                raise ValidationError({"emotion_ids": "정수 ID 목록이어야 합니다."})
            if not ids:
                raise ValidationError({"emotion_ids": "최소 1개 이상의 ID를 입력하세요."})

            missing = [i for i in ids if not emotion.objects.filter(pk=i).exists()]
            if missing:
                raise ValidationError({"emotion_ids": f"존재하지 않는 감정 ID: {missing}"})

            qs = qs.annotate(
                sel_count=Count('emotion_id', filter=Q(emotion_id__in=ids), distinct=True)
            ).filter(sel_count=len(ids))

        return qs

    def create(self, request, *args, **kwargs):
        # 1. memory 저장
        memory_serializer = self.get_serializer(data=request.data)
        memory_serializer.is_valid(raise_exception=True)
        memory_instance = memory_serializer.save()

        image_urls = []
        image_files = request.FILES.getlist('images')  # form-data에서 images[] 로 받음

        # 2. 이미지 업로드 & DB 저장
        for img_file in image_files:
            file_path = default_storage.save(f"community/{img_file.name}", img_file)  # S3 저장
            file_url = default_storage.url(file_path)  # S3 URL 생성

            image.objects.create(
                memory=memory_instance,
                image_url=file_url,
                image_name=os.path.basename(img_file.name)
            )
            image_urls.append(file_url)

        # 3. 응답 데이터 구성
        headers = self.get_success_headers(memory_serializer.data)
        response_data = memory_serializer.data
        response_data['images'] = image_urls

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # ✅ 연결된 이미지 S3 삭제
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        for img in instance.images.all():  # related_name='images'
            key = s3_key_from_url(img.image_url, bucket=bucket)
            if key:
                try:
                    default_storage.delete(key)
                except Exception:
                    pass
            img.delete()  # DB에서 이미지 정보 삭제

        # ✅ 글 삭제
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# 커뮤니티 이미지만 처리
class ImageViewSet(viewsets.ModelViewSet):
    queryset = image.objects.all().order_by('-pk')
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_destroy(self, instance):
        key = getattr(instance, 'image_key', None)
        if not key and getattr(instance, 'image_url', None):
            bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
            key = s3_key_from_url(instance.image_url, bucket=bucket)

        if key:
            try:
                default_storage.delete(key)
            except Exception:
                pass

        instance.delete()

