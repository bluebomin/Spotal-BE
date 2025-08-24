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
    다음은 사용자가 좋아하는 가게에 대해 자주 저장한 감정 리스트입니다: {", ".join(emotion_list)}

    이 정보를 바탕으로, 사용자가 좋아하는 가게의 분위기 취향을 사람의 특징으로 요약하세요.

    조건:
    - 반드시 한 문장, [감정 특징]을 좋아하는 [별명] 형태로 작성하세요.
    - 기호(-, *, 숫자 등), 마크다운, 따옴표는 절대 쓰지 마세요.
    - 가게가 주체가 아니라 사람의 성격처럼 끝나야 합니다.
    - 문장은 반드시 '사람을 나타내는 명사'로 끝나야 합니다.
      (예: "탐험가", "플래너", "애호가", "수집가", "여행자")
    - 공간을 나타내는 명사형으로 절대 끝내지 마세요. 지금 당신이 하는 건 사람에 대한 소개입니다. 
      (“공간, 장소, 가게” 같은 단어는 절대 쓰지 말 것)
    - 재치 있고 자연스럽게 표현하세요. 문장은 짧고 간결하게. 
    - 감정 태그들은 사람의 특징이 아닌, 그 사람이 좋아하는 '가게'의 특징임을 명심하세요. 
    '전통적인' 이라는 태그가 많이 보인다고 해서, 그 사람의 성격이 전통적이라는 게 아니라, 그 사람이 좋아하는 가게의 특징이 전통적이라는 겁니다. 

    올바른 예시:
    - 따뜻함을 좋아하는 감성탐험가
    - 현대적 감각을 즐기는 스마트 플래너
    - 전통을 소중히 여기는 클래식 애호가
    - 정겨움과 세심함을 사랑하는 편안한 안식처 애호가

    잘못된 예시 (이렇게 쓰면 안 됨):
    - 편안함을 좋아하는 아기자기한 공간 ❌
    - 정겨움과 소박함을 사랑하는 편안한 안식처 ❌
    """


    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=80
        )
        detail_text = completion.choices[0].message.content.strip()

        # 안전장치: 만약 '공간', '장소', '가게' 같은 단어로 끝나면 fallback 적용
        if detail_text.endswith(("공간", "장소", "가게")):
            detail_text = "따뜻함을 좋아하는 감성탐험가"
            
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
