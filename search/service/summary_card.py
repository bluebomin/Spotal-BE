from openai import OpenAI
from django.conf import settings
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_summary_card(details, reviews):
    prompt = f"""
    아래는 '{details.get("name")}' 가게의 실제 구글맵 리뷰 일부입니다:

    {reviews[:5]}

    위 리뷰들을 바탕으로 사용자에게 보여줄 요약카드를 작성해줘.

    조건:
    - 1문장, 간결하게
    - 리뷰 내용을 반영해 가게의 특징·분위기를 설명
    - 없는 사실은 절대 추가하지 마
    - 가게 위치, 영업시간, 전화번호는 언급하지 마
    - 무조건 한국말로만 요약 써줘
    - 리뷰를 기반으로 그 가게의 대표 메뉴나 특징을 언급해도 좋아
    - 예시: "55년 넘게 연탄불 납작 불고기로 사랑받은 용산의 명소"
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # 사실 기반
    )

    return response.choices[0].message.content.strip()


# 감정태그생성


ALLOWED_TAGS = ["정겨움", "편안함", "조용함", "활기참", "소박함", "세심함"]

def generate_emotion_tags(details, reviews):
    prompt = f"""
    아래는 '{details.get("name")}' 가게의 구글맵 리뷰입니다:

    {reviews[:5]}

    위 리뷰를 참고해서 아래 감정 태그 중 1~3개를 골라줘:
    - 정겨움
    - 편안함
    - 조용함
    - 활기참
    - 소박함
    - 세심함

    반드시 쉼표(,)로만 구분해서 출력해.
    예시: 정겨움, 편안함
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw_text = response.choices[0].message.content.strip()

    # 쉼표, 줄바꿈, 대시(-) 등 모든 구분자로 분리
    candidates = re.split(r'[,\\n\\-]+', raw_text)

    # 허용된 태그만 필터링 + 중복 제거
    tags = [t.strip() for t in candidates if t.strip() in ALLOWED_TAGS]
    tags = list(dict.fromkeys(tags))  # 중복 제거, 순서 보존

    return tags
