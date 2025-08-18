from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def translate_to_korean(text: str) -> str:
    if not text:
        return None

    prompt = f"""
    다음 입력을 한국어 주소/가게명으로 정리해 주세요.
    규칙:
    1. 입력이 이미 한국어라면 절대 수정하지 말고 그대로 출력하세요.
    2. 입력이 영어일 경우, 번역하지 말고 영어 단어와 주소를 한국어 발음/표기법에 맞게 변환하세요.
    3. 영어와 한국어가 섞여 있거나, 주소가 영어식 순서(번지 → 도로 → 구 → 시 → 국가)로 되어 있다면
    반드시 한국식 주소 체계 순서(시/구/동/도로명/번지)로 재배열하세요.
    4. 의미를 해석하거나 의역하지 말고, 단어와 숫자를 그대로 한국어 표기에 맞게 바꾸세요.
    5. 결과는 반드시 자연스러운 한국어 주소 형식으로 출력하세요.

    예시:
    입력: 14 한강대로 84길, 용산구, 서울특별시, 대한민국
    출력: 서울특별시 용산구 한강대로84길 14

    입력: Starbucks Itaewon
    출력: 스타벅스 이태원

    입력: 서울특별시 용산구 이태원동 34-2
    출력: 서울특별시 용산구 이태원동 34-2

    입력: {text}
    출력:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()
