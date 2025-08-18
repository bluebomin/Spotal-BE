import os
from rest_framework import viewsets, status
from .models import *
from .serializer import *
from .ImageSerializer import * 
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError 
from django.conf import settings
from django.core.files.storage import default_storage
from .utils import s3_key_from_url
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated


# 커뮤니티 글 응답 메시지 추가를 위한 믹스인
class BaseResponseMixin:
    success_messages = {
        'create': "글 생성 성공",
        'update': "글 수정 성공",
        'partial_update': "글 수정 성공",
        'destroy': "글 삭제 성공",
        'retrieve': "글 조회 성공",
        'list': "글 목록 조회 성공",
    }

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code < 400:
            action = getattr(self, 'action', None)
            message = self.success_messages.get(action)
            if message:
                # 데이터가 None이면 빈 딕셔너리로
                if response.data is None:
                    response.data = {}
                # message + data 구조로 변환
                response.data = {
                    "message": message,
                    "data": response.data
                }
        return super().finalize_response(request, response, *args, **kwargs)


#Viewset
class EmotionViewSet(viewsets.ModelViewSet):
    queryset = Emotion.objects.all().order_by('pk')
    serializer_class = EmotionSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('pk')
    serializer_class = LocationSerializer

class MemoryViewSet(BaseResponseMixin,viewsets.ModelViewSet):
    queryset = Memory.objects.all().order_by('-created_at')
    serializer_class = MemorySerializer
    parser_classes = [MultiPartParser, FormParser]  # 이미지 + 텍스트 같이 받으려면 필요
    permission_classes = [IsAuthenticated]
    


    @action(detail=False, methods=['get'], url_path='tag-options')
    # 커뮤니티 글 작성 시 감정/위치 태그 목록 조회 (프론트)
    def tag_options(self, request):
        emotions = Emotion.objects.all().order_by('pk')
        locations = Location.objects.all().order_by('pk')
        return Response({
            'emotions': EmotionSerializer(emotions, many=True).data,
            'locations': LocationSerializer(locations, many=True).data
        })

    # 커뮤니티 글 목록 조회 (필터링)
    def get_queryset(self):
        qs = super().get_queryset() \
            .select_related('location') \
            .prefetch_related('emotion_id')

        params = self.request.query_params

        # 위치 필터
        loc = params.get('location_id')
        if loc is not None:
            if not str(loc).isdigit():
                raise ValidationError({"location_id": "정수 ID여야 합니다."})
            loc = int(loc)
            if not location.objects.filter(pk=loc).exists():
                raise ValidationError({"location_id": f"존재하지 않는 위치 ID {loc}"})
            qs = qs.filter(location_id=loc)

        # 감정 필터
        raw = params.get('emotion_ids')
        if raw:
            try:
                ids = [int(x) for x in raw.split(',') if x.strip()]
            except ValueError:
                raise ValidationError({"emotion_ids": "정수 ID 목록이어야 합니다."})
            

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
        memory_instance = memory_serializer.save(user=request.user)

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
        response_data = {
            "data": memory_serializer.data,
            
        }

        headers = self.get_success_headers(memory_serializer.data)
        return Response(memory_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 연결된 이미지 S3 삭제
        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        for img in instance.images.all():  # related_name='images'
            key = s3_key_from_url(img.image_url, bucket=bucket)
            if key:
                try:
                    default_storage.delete(key)
                except Exception:
                    pass
            img.delete()  # DB에서 이미지 정보 삭제

        # 글 삭제
        instance.delete()

        return Response({},status=status.HTTP_200_OK)


# 커뮤니티 이미지만 처리
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-pk')
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    # 이미지 삭제
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

#view
@api_view(['GET'])
def my_community(request):
    if request.method == 'GET':
        user = request.user
        memories = Memory.objects.filter(user_id=user).order_by('-created_at')
        serializer = MemorySerializer(memories, many=True)
        return Response(
        {
            "message": "내가 쓴 글 조회 성공",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )
    return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)