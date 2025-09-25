from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from django.core.files.storage import default_storage
from uuid import uuid4
from datetime import date
import os

class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 시리얼라이저"""
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'nickname', 'password', 'detail']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """회원가입 시 사용자 생성"""
        user = User.objects.create_user(
            email=validated_data['email'],
            nickname=validated_data['nickname'],
            password=validated_data['password'],
            detail=validated_data.get('detail', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    """로그인 시리얼라이저"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        """로그인 검증"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('이메일 또는 비밀번호가 올바르지 않습니다.')
            if not user.is_active:
                raise serializers.ValidationError('비활성화된 계정입니다.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('이메일과 비밀번호를 모두 입력해주세요.')
        
        return attrs
    
class LogoutSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class NicknameCheckSerializer(serializers.Serializer):
    """닉네임 중복확인 시리얼라이저"""
    nickname = serializers.CharField(max_length=255)
    
    def validate_nickname(self, value):
        """닉네임 중복 확인"""
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')
        return value

class EmailCheckSerializer(serializers.Serializer):
    """이메일 중복확인 시리얼라이저"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """이메일 중복 확인"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('이미 사용 중인 이메일입니다.')
        return value 
    

# 유저 프로필 이미지 업로드 부분
from rest_framework import serializers
from .models import User
from django.core.files.storage import default_storage
from uuid import uuid4
from datetime import date
import os


class UserProfileSerializer(serializers.ModelSerializer):
    # 업로드 전용 (PUT 시만 사용)
    profile_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "nickname", "detail", "profile_image", "profile_image_url"]
        read_only_fields = ["profile_image_url"]

    def validate_profile_image(self, file):
        max_mb = 5
        if file.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"{max_mb}MB 이하만 업로드 가능합니다.")
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if getattr(file, "content_type", None) not in allowed:
            raise serializers.ValidationError("JPEG/PNG/WebP만 허용됩니다.")
        return file

    def update(self, instance, validated_data):
        file = validated_data.pop("profile_image", None)

        if file:
            ext = os.path.splitext(file.name)[1]
            key = f"users/profiles/{date.today():%Y/%m/%d}/{uuid4().hex}{ext}"
            saved_key = default_storage.save(key, file)
            name = os.path.basename(saved_key)

            instance.profile_image_url = default_storage.url(saved_key)
            instance.profile_image_name = name

        # ❗ 이미지 삭제 시 profile_image_url null 보장
        if instance.profile_image_url is None:
            instance.profile_image_url = None

        return super().update(instance, validated_data)
