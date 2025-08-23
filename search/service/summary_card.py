from openai import OpenAI
from django.conf import settings
import re

def extract_keywords(reviews):
    if not reviews:
        return []

    text = "\n".join(reviews[:10])  # 리뷰 최대 10개만 사용

    prompt = f"""
    다음 리뷰에서 대표 음식, 음료, 서비스 관련 키워드 1~3개만 뽑아줘.
    조건:
    - 반드시 명사만 출력 (메뉴 이름, 음식, 음료, 서비스 특징)
    - '음식', '맛', '분위기' 같은 추상적/일반적 단어는 제외
    - 실제 메뉴 이름(예: 삼겹살, 콩나물국밥, 아메리카노 등)이나 서비스 특징(예: 친절함, 청결)만 남겨
    - 반드시 쉼표(,)로 구분해서 출력
    - 반드시 사실에 기반해서만 출력

    리뷰:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()

    # 쉼표 기준 분리 + 불필요한 공백 제거
    candidates = [kw.strip() for kw in raw.split(",") if kw.strip()]

    # 한글/영문 명사만 허용 (숫자, 특수문자 제거)
    keywords = [re.sub(r"[^가-힣A-Za-z ]", "", kw) for kw in candidates]

    # 너무 짧은 단어 (1글자) 제거 + 중복 제거
    keywords = list(dict.fromkeys([kw for kw in keywords if len(kw) > 1]))

    return keywords


client = OpenAI(api_key=settings.OPENAI_API_KEY)
def generate_summary_card(details, reviews, uptaenms):
    keywords = extract_keywords(reviews)
    uptaenms_list = uptaenms if isinstance(uptaenms, list) else [str(uptaenms)]

    # point_of_interest, establishment만 있으면 요약카드 생성하지 않음
    if set(uptaenms_list).issubset({"point_of_interest", "establishment"}):
        return ""

    prompt = f"""
    아래는 '{details.get("name")}' 의 구글맵 리뷰입니다:


    {reviews[:5]}
    키워드: {keywords}

    조건:
    - 반드시 1문장, 간결하게 작성
    - 리뷰에 나온 키워드({keywords}) 중 최소 1개는 반드시 포함해야 한다
    - 없는 사실은 절대 추가하지 마
    - "맛있는 음식", "다양한 음식", "좋은 분위기" 같은 추상적 표현 금지
    - 그 가게의 대표 메뉴에 대해 언급할 것
    - 업태 구분명은 참고만 하고, 문장에 직접 "음식점, 카페, 역" 같은 단어는 쓰지 마
    - 장소가 가게일 수도 있고 아닐 수도 있으므로 '가게'라는 단어를 쓰지 마
    - 리뷰가 1개뿐이어도, 핵심 키워드를 반드시 포함해 요약
    - 문장은 '~~한 곳이에요', '~~로 사랑받는 곳이에요', '~~을 즐길 수 있는 곳이에요'로 끝낼 것

    예시:
    - "두툼한 삼겹살과 푸짐한 반찬으로 회식에 인기 있는 곳이에요"
    - "시원한 콩나물국밥으로 아침 손님에게 사랑받는 곳이에요!"
    - "환승이 편리하고 주변 상권 접근성이 좋은 교통 요지 입니다"
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # 사실 기반 요약
    )

    summary = response.choices[0].message.content.strip()


    return summary

# 감정태그생성


ALLOWED_TAGS = ["정겨움", "편안함", "조용함", "활기참", "소박함", "세심함", "정성스러움", "깔끔함", "친절함", "고즈넉함",
                "현대적임", "전통적임", "독특함", "화려함", "낭만적임", "가족적임", "전문적임","아늑함","편리함","트렌디함"]

def generate_emotion_tags(details, reviews, uptaenms):

    prompt = f"""
    아래는 '{details.get("name")}' 가게의 구글맵 리뷰입니다:

    {reviews[:5]}
    {uptaenms}

    위 리뷰를 참고해서 아래 감정 태그 중 2개를 골라줘:
    - 정겨움
    - 편안함
    - 조용함
    - 활기참
    - 소박함
    - 세심함
    - 정성스러움
    - 깔끔함
    - 친절함
    - 고즈넉함
    - 현대적임
    - 전통적임
    - 독특함
    - 화려함
    - 낭만적임
    - 가족적임
    - 전문적임
    - 아늑함
    - 편리함
    - 트렌디함
    
    

    - 반드시 쉼표(,)로만 구분해서 출력해.
    - 항상 서로 다른 성격의 감정을 고르고, 동일한 패턴이 반복되지 않도록 해줘.
    - 같은 조합을 연속으로 추천하지 말 것.
    - 리뷰에 직접적으로 드러나지 않는 부분이라도 합리적으로 추측해서 감정을 다양하게 반영할 것.
  
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    raw_text = response.choices[0].message.content.strip()

    # 쉼표, 줄바꿈, 대시(-) 등 모든 구분자로 분리
    candidates = re.split(r'[,\\n\\-]+', raw_text)

    # 허용된 태그만 필터링 + 중복 제거
    tags = [t.strip() for t in candidates if t.strip() in ALLOWED_TAGS]
    tags = list(dict.fromkeys(tags))  # 중복 제거, 순서 보존

    return tags
