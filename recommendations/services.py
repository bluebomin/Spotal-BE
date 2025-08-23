from django.conf import settings
import openai

def call_gpt_api(prompt: str) -> str | None:
    """공통 GPT API 호출"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # 실제 사용하는 모델명에 맞게 수정
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT 호출 오류: {e}")
        return None



def generate_gpt_emotion_based_recommendations(place) -> str:
    """감정 기반 가게 추천 요약 생성"""
    prompt = f"""
    아래 가게에 대한 감정 기반 요약을 작성해주세요:

    가게명: {place.name}
    주소: {place.address}
    감정: {place.emotion.name if place.emotion else '정보 없음'}

    조건:
    - 1~2문장으로 작성
    - 감정을 반영해 분위기나 특징을 표현
    """
    summary = call_gpt_api(prompt)
    return summary or "요약 정보를 생성할 수 없습니다."
