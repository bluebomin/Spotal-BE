# serializers.py
from django.core.files.storage import default_storage
from rest_framework import serializers
from uuid import uuid4
from datetime import date
import os
from .models import Image, Memory

class ImageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="pk")

    image = serializers.ImageField(write_only=True)
    memory_id = serializers.PrimaryKeyRelatedField(
        queryset=Memory.objects.all(),
        write_only=True,
        required=True
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["id", "image", "image_url", "image_name", "memory_id"]
        read_only_fields = ["id", "image_url", "image_name"]

    def validate_image(self, file):
        max_mb = 5
        if file.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"파일은 {max_mb}MB 이하만 허용됩니다.")
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if getattr(file, "content_type", None) not in allowed:
            raise serializers.ValidationError("JPEG/PNG/WebP만 업로드 가능합니다.")
        return file

    def create(self, validated_data):
        file = validated_data.pop("image")
        mem = validated_data.pop("memory_id")
        ext = os.path.splitext(file.name)[1]

        key = f"community/images/{date.today():%Y/%m/%d}/{uuid4().hex}{ext}"
        saved_key = default_storage.save(key, file)  # S3 Key만 저장
        name = os.path.basename(saved_key)

        instance = Image.objects.create(
            image_url=saved_key,   # URL 대신 Key 저장
            image_name=name,
            memory_id=mem.pk,
            **validated_data
        )
        return instance

    def get_image_url(self, obj):
        # ✅ 매번 serializer 호출 시 presigned URL 새로 생성
        return default_storage.url(obj.image_url)
