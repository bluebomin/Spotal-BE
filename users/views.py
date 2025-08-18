from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from .serializers import UserSerializer, LoginSerializer, NicknameCheckSerializer, EmailCheckSerializer

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
