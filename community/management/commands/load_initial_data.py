import os
import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from community.models import Emotion, Location  # 모델 경로 맞게 수정

class Command(BaseCommand):
    help = 'Load initial emotions and locations from CSV files'

    def handle(self, *args, **kwargs):
        # CSV 경로 지정
        emotion_csv_path = os.path.join(settings.BASE_DIR, 'data', 'emotion.csv')
        location_csv_path = os.path.join(settings.BASE_DIR, 'data', 'location.csv')

        # 감정 데이터 로드
        with open(emotion_csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Emotion.objects.get_or_create(emotion_id=row['emotion_id'], name=row['name'])

        # 위치 데이터 로드
        with open(location_csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Location.objects.get_or_create(location_id=row['location_id'], name=row['name'])

        self.stdout.write(self.style.SUCCESS('CSV 데이터 로드 완료'))
