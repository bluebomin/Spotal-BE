from django.db import models
from django.conf import settings
from recommendations.models import Place

# Create your models here.

class AISummary(models.Model):
    """GPT 기반 추천 결과 요약"""
    summary_id = models.BigAutoField(primary_key=True)
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="infer_ai_summary"
    )
    summary = models.TextField(verbose_name='GPT 추천 텍스트')
    emotion_tags = models.JSONField(default=list, blank=True, verbose_name='생성된 감정 태그')
    reviews_snapshot = models.JSONField(default=list, blank=True, verbose_name='요약 생성 시점의 리뷰 스냅샷')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "infer_ai_summary"

    def __str__(self):
        return f"Summary for {self.place.name}"


class UserInferenceSession(models.Model):
    """사용자의 추론 세션 (동네 + 감정 선택)"""
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    selected_location = models.ManyToManyField('community.Location', verbose_name='선택된 동네들')
    selected_emotions = models.ManyToManyField('community.Emotion', verbose_name='선택된 감정들')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "user_inference_session"
        ordering = ['-created_at']
        verbose_name = "사용자 추론 세션"
        verbose_name_plural = "사용자 추론 세션들"
    
    def __str__(self):
        location_names = ", ".join([location.name for location in self.selected_location.all()])
        emotion_names = ", ".join([emotion.name for emotion in self.selected_emotions.all()])
        return f"{location_names} - {emotion_names} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class InferenceRecommendation(models.Model):
    """추론 세션별 추천 결과"""
    recommendation_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(UserInferenceSession, on_delete=models.CASCADE, related_name='recommendations')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='inference_recommendations', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "inference_recommendation"
        ordering = ['-created_at']
        verbose_name = "추론 추천 결과"
        verbose_name_plural = "추론 추천 결과들"
    
    def __str__(self):
        if self.place:
            return f"추천 결과 {self.recommendation_id} - {self.place.name} ({self.session})"
        else:
            return f"추천 결과 {self.recommendation_id} - {self.session}"
