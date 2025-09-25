from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer,
    LoginSerializer,
    NicknameCheckSerializer,
    EmailCheckSerializer,
    UserProfileSerializer
)
from .models import User


# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """회원가입 API"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # 회원가입 성공 시 자동 로그인
        login(request, user)
        # 토큰 생성
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'email': user.email,
                'nickname': user.nickname,
                'detail': user.detail
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """로그인 API"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        # 토큰 생성
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': '로그인이 완료되었습니다.',
            'user': {
                'id': user.id,
                'email': user.email,
                'nickname': user.nickname,
                'detail': user.detail
            },
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_nickname(request):
    """닉네임 중복확인 API"""
    serializer = NicknameCheckSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            'message': '사용 가능한 닉네임입니다.',
            'available': True
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': serializer.errors['nickname'][0],
        'available': False
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_email(request):
    """이메일 중복확인 API"""
    serializer = EmailCheckSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            'message': '사용 가능한 이메일입니다.',
            'available': True
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': serializer.errors['email'][0],
        'available': False
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """로그아웃 API"""
    # 세션 기반 로그아웃 (항상 실행)
    logout(request)
    return Response({
        'message': '로그아웃이 완료되었습니다.'
    }, status=status.HTTP_200_OK)


# 프로필 이미지 조회, 수정, 삭제
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def user_profile(request, user_id):
    """유저 프로필 조회 / 수정 / 삭제 API"""
    user = get_object_or_404(User, id=user_id)

    # 조회
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response({
            "message": "조회 성공",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    # 수정
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "프로필 이미지가 수정되었습니다.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 삭제
    elif request.method == 'DELETE':
        if user.profile_image_url:
            default_storage.delete(user.profile_image_url)
            user.profile_image_url = None
            user.profile_image_name = None
            user.save()
        return Response({"message": "프로필 이미지가 삭제되었습니다."}, status=status.HTTP_200_OK)