import os
from rest_framework import viewsets, status, generics
from .models import *
from .serializers import *
from .ImageSerializer import * 
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError 
from django.conf import settings
from django.core.files.storage import default_storage
from .utils import s3_key_from_url
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from django.contrib.auth import get_user_model


User = get_user_model()


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
    permission_classes = [AllowAny] 

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('pk')
    serializer_class = LocationSerializer
    permission_classes = [AllowAny] 

class MemoryViewSet(BaseResponseMixin,viewsets.ModelViewSet):
    queryset = Memory.objects.all().order_by('-created_at')
    serializer_class = MemorySerializer
    parser_classes = [MultiPartParser, FormParser]  # 이미지 + 텍스트 같이 받으려면 필요
    permission_classes = [AllowAny]
    


    @action(detail=False, methods=['get'], url_path='tag-options')
    # 커뮤니티 글 작성 시 감정/위치 태그 목록 조회 (프론트)
    def tag_options(self, request):
        emotions = Emotion.objects.all().order_by('pk')
        locations = Location.objects.all().order_by('pk')
        boards = Board.objects.all().order_by('pk')
        return Response({
            'emotions': EmotionSerializer(emotions, many=True).data,
            'locations': LocationSerializer(locations, many=True).data,
            'boards': BoardSerializer(boards, many=True).data
        })

    # 커뮤니티 글 목록 조회 (필터링 / 위치, 감정, 게시글분류 포함)
    def get_queryset(self):
        qs = super().get_queryset() \
            .select_related('location','board') \
            .prefetch_related('emotion_id')

        params = self.request.query_params

        # 위치 필터
        loc = params.get('location_id')
        if loc is not None:
            if not str(loc).isdigit():
                raise ValidationError({"location_id": "정수 ID여야 합니다."})
            loc = int(loc)
            if not Location.objects.filter(pk=loc).exists():
                raise ValidationError({"location_id": f"존재하지 않는 위치 ID {loc}"})
            qs = qs.filter(location_id=loc)

        # 감정 필터
        raw = params.get('emotion_ids')
        if raw:
            try:
                ids = [int(x) for x in raw.split(',') if x.strip()]
            except ValueError:
                raise ValidationError({"emotion_ids": "정수 ID 목록이어야 합니다."})
            

            missing = [i for i in ids if not Emotion.objects.filter(pk=i).exists()]
            if missing:
                raise ValidationError({"emotion_ids": f"존재하지 않는 감정 ID: {missing}"})

            qs = qs.annotate(
                sel_count=Count('emotion_id', filter=Q(emotion_id__in=ids), distinct=True)
            ).filter(sel_count=len(ids))

            # 보드 필터
            board = params.get('board_id')
            if board is not None:
                if not str(board).isdigit():
                    raise ValidationError({"board_id": "정수 ID여야 합니다."})
                board = int(board)
                if not Board.objects.filter(pk=board).exists():
                    raise ValidationError({"board_id": f"존재하지 않는 보드 ID {board}"})
                qs = qs.filter(board_id=board)

        return qs

    def create(self, request, *args, **kwargs):
        
        # 1. memory 저장
        memory_serializer = self.get_serializer(data=request.data)
        memory_serializer.is_valid(raise_exception=True)

        # user_id를 body로 전달받는 식으로 변경, (다음 7줄의 코드)
        # 원인: AllowAny로 수정해서 request.user가 AnonymousUser가 되는 문제 발생
        user_id = request.data.get("user_id") 
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": f"user_id {user_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

        # request.user 대신 user 객체 저장
        memory_instance = memory_serializer.save(user=user)


        image_urls = []
        image_files = request.FILES.getlist('images')  # form-data에서 images[] 로 받음

        # 2. 이미지 업로드 & DB 저장
        for img_file in image_files:
            file_path = default_storage.save(f"community/{img_file.name}", img_file)  # S3 저장
            file_url = default_storage.url(file_path)  # S3 URL 생성

            Image.objects.create(
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
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # 1) 기본 필드 업데이트
        ser = self.get_serializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        memory = ser.save()

        # 2) 삭제 ID 파싱 (deleted_image_ids / delete_image_ids 둘 다 허용)
        delete_ids = request.data.getlist("deleted_image_ids") or request.data.getlist("delete_image_ids") or []
        try:
            delete_ids = list(map(int, delete_ids))
        except Exception:
            delete_ids = []

        raw = request.data.get("deleted_image_ids")
        if isinstance(raw, str) and raw.strip().startswith("["):
            import json
            try:
                delete_ids = list(map(int, json.loads(raw)))
            except Exception:
                pass

        if delete_ids:
            for img in instance.images.filter(pk__in=delete_ids):
                key = s3_key_from_url(img.image_url, bucket=settings.AWS_STORAGE_BUCKET_NAME)
                if key:
                    try:
                        default_storage.delete(key)
                    except Exception:
                        pass
                img.delete()

        # 3) 새 이미지 업로드 (모두 저장)
        new_files = request.FILES.getlist("images")
        for f in new_files:
            path = default_storage.save(f"community/{f.name}", f)
            url  = default_storage.url(path)
            Image.objects.create(
                memory=memory,
                image_url=url,
                image_name=os.path.basename(f.name),
            )

        # 4) ✅ 루프 밖에서 항상 한 번만 반환 (새 파일이 0장이어도 반환됨)
        return Response(self.get_serializer(memory).data, status=status.HTTP_200_OK)
        

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

# 커뮤니티 댓글
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]
    

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        parent_id = self.request.data.get("parent")
        
        if not user_id:
            raise ValidationError({"user_id": "user_id is required"})
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user_id": f"user_id {user_id} not found"})
        if parent_id:
            parent = Comment.objects.get(pk=parent_id) if parent_id else None
            serializer.save(user=user,parent=parent,memory=parent.memory)
        else:
            serializer.save(user=user)

    def get_queryset(self):
        qs = Comment.objects.all().order_by('-created_at')
    
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return qs
        memory_id = self.request.query_params.get('memory_id')
        if memory_id is None:
            raise ValidationError({"memory_id": "memory_id query parameter is required"})
        else :
            qs = qs.filter(memory_id=memory_id,parent__isnull=True)
        return qs
    
    # 댓글을 조회할 때만(GET 요청일 때만) 답글 리스트를 반환하도록 수정
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['list','retrieve']:
            context['include_replies'] = True
        return context


    
# 커뮤니티 이미지만 처리
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-pk')
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

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
@permission_classes([AllowAny])
def my_community(request):
    # 1) user_id 필수
    user_id = request.query_params.get("user_id")
    if not user_id or not str(user_id).isdigit():
        return Response({"error": "user_id is required and must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
    user_id = int(user_id)

    # 2) 기본 쿼리셋
    qs = (
        Memory.objects
        .filter(user_id=user_id)
        .select_related('location')
        .prefetch_related('emotion_id')   # 모델에서 사용중인 related name에 맞추세요
        .order_by('-created_at')
    )

    # 3) 위치 필터 (단일)
    loc = request.query_params.get('location_id')
    if loc:
        if not str(loc).isdigit():
            raise ValidationError({"location_id": "정수 ID여야 합니다."})
        loc = int(loc)
        if not Location.objects.filter(pk=loc).exists():
            raise ValidationError({"location_id": f"존재하지 않는 위치 ID {loc}"})
        qs = qs.filter(location_id=loc)

    # 4) 감정 필터 (다중: emotion_ids=1,3,5)
    raw = request.query_params.get('emotion_ids')
    if raw:
        try:
            ids = [int(x) for x in raw.split(',') if x.strip()]
        except ValueError:
            raise ValidationError({"emotion_ids": "정수 ID 목록이어야 합니다."})

        missing = [i for i in ids if not Emotion.objects.filter(pk=i).exists()]
        if missing:
            raise ValidationError({"emotion_ids": f"존재하지 않는 감정 ID: {missing}"})

        # 선택한 모든 감정을 가진 항목만
        qs = qs.annotate(
            sel_count=Count('emotion_id', filter=Q(emotion_id__in=ids), distinct=True)
        ).filter(sel_count=len(ids))

    serializer = MemorySerializer(qs, many=True)
    return Response(
        {"message": "내가 쓴 글 조회 성공", "data": serializer.data},
        status=status.HTTP_200_OK
    )


# 북마크 생성
class BookmarkCreateView(generics.CreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [AllowAny] 

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        if not user_id:
            raise ValidationError({"user_id": "user_id is required"})

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user_id": f"user_id {user_id} not found"})

        serializer.save(user=user)


# 북마크 목록 조회
class BookmarkListView(generics.ListAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if not user_id:
            raise ValidationError({"user_id": "user_id query parameter is required"})

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user_id": f"user_id {user_id} not found"})

        return Bookmark.objects.filter(user=user).order_by("-created_date")


# 북마크 삭제
class BookmarkDeleteView(generics.DestroyAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [AllowAny]
    lookup_field = "bookmark_id"

    def get_queryset(self):
        user_id = self.request.data.get("user_id") or self.request.query_params.get("user_id")
        if not user_id:
            raise ValidationError({"user_id": "user_id is required"})

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise ValidationError({"user_id": f"user_id {user_id} not found"})

        return Bookmark.objects.filter(user=user)