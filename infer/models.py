from django.db import models
from django.conf import settings

# Create your models here.

class UserInferenceSession(models.Model):
    """사용자의 추론 세션 (동네 + 감정 선택)"""
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    selected_location = models.ForeignKey('community.Location', on_delete=models.CASCADE, verbose_name='선택된 동네')
    selected_emotions = models.ManyToManyField('community.Emotion', verbose_name='선택된 감정들')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "user_inference_session"
        ordering = ['-created_at']
        verbose_name = "사용자 추론 세션"
        verbose_name_plural = "사용자 추론 세션들"
    
    def __str__(self):
        emotion_names = ", ".join([emotion.name for emotion in self.selected_emotions.all()])
        return f"{self.selected_location.name} - {emotion_names} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class InferenceRecommendation(models.Model):
    """GPT 기반 추천 결과"""
    recommendation_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(UserInferenceSession, on_delete=models.CASCADE, related_name='recommendations')
    gpt_recommendation_text = models.TextField(verbose_name='GPT 추천 텍스트')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "inference_recommendation"
        ordering = ['-created_at']
        verbose_name = "추론 추천 결과"
        verbose_name_plural = "추론 추천 결과들"
    
    def __str__(self):
        return f"추천 결과 {self.recommendation_id} - {self.session}"
