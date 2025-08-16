# serializers.py
from django.core.files.storage import default_storage
from rest_framework import serializers
from uuid import uuid4
from datetime import date
import os
from .models import image, memory

class ImageSerializer(serializers.ModelSerializer):
    # 응답용 가짜 id 필드 (모델 필드 아님) -> pk를 그대로 노출
    id = serializers.ReadOnlyField(source="pk")

    # 업로드용 파일 필드 (모델 필드 아님)
    image = serializers.ImageField(write_only=True)
    memory_id = serializers.PrimaryKeyRelatedField(
        queryset=memory.objects.all(),
        write_only=True,  # 입력용이므로 읽기 전용 아님
        required=True
    )

    class Meta:
        model = image
        fields = ["id", "image", "image_url", "image_name","memory_id"]  # 모델 외 커스텀 필드 포함 OK
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
        saved_key = default_storage.save(key, file)

        url = default_storage.url(saved_key)
        name = os.path.basename(saved_key)

        instance = image.objects.create(
            image_url=url,
            image_name=name,
            # image_key=saved_key,  # 모델에 image_key 추가했으면 함께 저장 추천
            memory_id=mem.pk,
            **validated_data
        )
        return instance
