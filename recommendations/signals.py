from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.db.models import Count
from openai import OpenAI

from .models import SavedPlace

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_user_detail(user):
    """
    유저의 SavedPlace 기록을 기반으로 감정 분포를 집계하고,
    GPT API를 사용하여 User.detail을 갱신합니다.
    """
    # 유저가 저장한 감정 데이터 집계
    top_emotions = (
        SavedPlace.objects.filter(user=user)
        .values("shop__emotions__name")
        .annotate(count=Count("shop__emotions"))
        .order_by("-count")
    )
    emotion_list = [e["shop__emotions__name"] for e in top_emotions[:3]]

    # 감정 데이터가 없으면 detail 비움
    if not emotion_list:
        user.detail = ""
        user.save(update_fields=["detail"])
        return

    # GPT 프롬프트 작성
    prompt = f"""
    이 사용자가 추억의 가게에서 느끼는 감정으로 자주 저장한 감정은 {", ".join(emotion_list)} 입니다.
    이 감정 성향을 가진 사람이 좋아하는 가게의 성격·분위기를 짧게 요약해 주세요.
    이 감정 리스트는 사용자가 좋아하는 가게에 가서 느끼고 싶어하는 감정들입니다. 사용자 본인의 성격은 아닐 수도 있으니 말을 정확히 하세요.
    결과는 한국어 한 문장으로 명사 단위로 끝내주세요.
    
    재치 있게 잘 못 쓰겠으면 다음 템플릿을 참고하세요.

    [사용자가 좋아하는 가게의 감성의 특징]을 좋아하는 [사용자가 좋아하는 가게의 특징]

    # 사용자가 좋아하는 가게의 감성의 특징은  {", ".join(emotion_list)} 을 분석하면 알 수 있습니다.
    # 사용자가 좋아하는 가게의 특징은 감성적인 걸 좋아하면 '감성탐험가', 편리하고 현대적인 걸 좋아하면 '스마트 플래너' 등 

    !! 주의 !! 
    말이 되게 써 줘. 특히 가게의 특징이 사람의 특징이라고 말하지 않도록 주의해 줘.
    예를 들어 편안함을 제공하는 스마트 플래너라고 하면 안 돼. 제공하는 주체는 가게이지, 사람이 아니니까!!!

    예시: 따뜻함을 좋아하는 감성탐험가
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=80
        )
        detail_text = completion.choices[0].message.content.strip()
    except Exception as e:
        detail_text = f"(AI 생성 실패: {str(e)})"

    # User.detail 업데이트
    user.detail = detail_text
    user.save(update_fields=["detail"])


@receiver(post_save, sender=SavedPlace)
def update_user_detail_on_save(sender, instance, created, **kwargs):
    """
    SavedPlace 생성 시 유저 detail 갱신
    """
    if created:
        generate_user_detail(instance.user)


@receiver(post_delete, sender=SavedPlace)
def update_user_detail_on_delete(sender, instance, **kwargs):
    """
    SavedPlace 삭제 시 유저 detail 갱신
    """
    generate_user_detail(instance.user)
