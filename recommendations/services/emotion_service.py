# services/emotion_service.py
from openai import OpenAI
from django.conf import settings
from community.models import Emotion
import json

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def expand_emotions_with_gpt(emotion_tags):
    """
    입력된 emotion_tags와 비슷한 감정을 GPT를 통해 확장
    DB에 실제 존재하는 Emotion 객체 리스트 반환
    """

    all_emotions = list(Emotion.objects.values_list("name", flat=True))

    prompt = f"""
    당신은 감정 분류 전문가입니다. 
    아래는 사용할 수 있는 감정 태그 목록입니다 (이 목록 외 단어는 절대 사용하지 마세요):

    {", ".join(all_emotions)}

    입력된 감정 태그: {", ".join(emotion_tags)}

    규칙:
    - 반드시 위 목록에 존재하는 감정 태그만 결과로 선택하세요.
    - 입력된 감정과 가장 비슷하거나 함께 쓰일 만한 감정을 3~5개 고르세요.
    - 반드시 JSON 배열 형식으로만 출력하세요. (예: ["정겨움", "편안함", "아늑함"])
    - 설명, 불필요한 텍스트, 주석 없이 결과만 출력하세요.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,   # 낮춰서 안정성 ↑
        max_tokens=150
    )

    result_text = completion.choices[0].message.content.strip()

    try:
        expanded_names = json.loads(result_text)  # JSON 파싱
    except json.JSONDecodeError:
        # 혹시라도 JSON 실패하면 fallback으로 콤마 split
        expanded_names = [name.strip() for name in result_text.split(",")]

    # DB에 실제 존재하는 감정만 필터링
    return Emotion.objects.filter(name__in=expanded_names)
