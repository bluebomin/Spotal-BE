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

    # 리뷰 타입이 str 리스트라면 dict 리스트로 고치도록 
    if reviews and isinstance(reviews, list):
        normalized_reviews = []
        for r in reviews:
            if isinstance(r, str):
                normalized_reviews.append({"text": r})
            elif isinstance(r, dict):
                normalized_reviews.append(r)
        reviews = normalized_reviews

    # 리뷰가 없거나 모두 공백인 경우
    if not reviews or all(not r.get("text", "").strip() for r in reviews):

        prompt = f"""
        '{details.get("name")}' 은/는 어떤 곳인지 설명해 주세요.
        업태 구분명({', '.join(uptaenms)}) / '{details.get("rating")}'과 '{details.get("formatted_address")}'을 참고할 수 있습니다.
        조건:
        - 반드시 1문장, 간결하게 작성
        - 문장은 '~~한 곳이에요', '~~로 사랑받는 곳이에요', '~~을 즐길 수 있는 곳이에요'로 끝낼 것


        예시:
        - "두툼한 삼겹살과 푸짐한 반찬으로 회식에 인기 있는 곳이에요"
        - "시원한 콩나물국밥으로 아침 손님에게 사랑받는 곳이에요!"
        - "환승이 편리하고 주변 상권 접근성이 좋은 교통 요지 입니다"
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5  # 약간의 창의성 허용
        )
        summary = response.choices[0].message.content.strip()
        summary = re.sub(r'^"(.*)"$', r'\1', summary)  # 양쪽 큰따옴표 제거

        return summary
   
   # reviews를 dict 리스트로 수정
    review_texts = [r.get("text", "") for r in reviews]
    keywords = extract_keywords(review_texts)
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
    summary = re.sub(r'^"(.*)"$', r'\1', summary)  # 양쪽 큰따옴표 제거


    return summary


# 감정태그생성

ALLOWED_TAGS = ["정겨움", "편안함", "조용함", "활기참", "소박함", "세심함", "정성스러움", "깔끔함", "친절함", "고즈넉함",
                "현대적임", "전통적임", "독특함", "화려함", "낭만적임", "가족적임", "전문적임","아늑함","편리함","트렌디함"]

def generate_emotion_tags(place_name, reviews, types):
    """리뷰를 기반으로 감정 태그 생성"""

    # reviews 타입이 str이었다면 dict로. 
    if reviews and isinstance(reviews, list):
        normalized_reviews = []
        for r in reviews:
            if isinstance(r, str):
                normalized_reviews.append({"text": r})
            elif isinstance(r, dict):
                normalized_reviews.append(r)
        reviews = normalized_reviews
    
    # 리뷰가 없으면 업태별 기본 감정 태그 반환
    if not reviews or len(reviews) == 0:
        print(f"[DEBUG] 리뷰가 없음, 업태별 기본 감정 태그 사용")
        return get_default_emotion_tags_by_types(types)
    
    # 리뷰가 있으면 GPT로 감정 태그 생성
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 리뷰 텍스트들을 하나로 합치기
        review_text = "\n".join([review.get('text', '') for review in reviews[:5]])
        
        prompt = f"""
        다음 가게의 리뷰를 읽고, 이 가게에서 느낄 수 있는 감정을 나타내는 한국어 단어 2개를 추출해주세요.
        
        가게명: {place_name}
        업태: {', '.join(types)}
        리뷰:
        {review_text}
        
        감정 태그는 쉼표로 구분해서 답변해주세요. 예: 친절함, 아늑함
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )
        
        emotion_text = response.choices[0].message.content.strip()
        
        # 응답을 감정 태그 리스트로 변환
        emotion_candidates = [tag.strip() for tag in emotion_text.split(',')]

        # 최종 감정 태그 (최대 2개)
        final_emotions = emotion_candidates[:2]
       
        return final_emotions
        
    except Exception as e:
        print(f"[DEBUG] GPT API 호출 중 오류: {e}")
        # GPT 실패 시에도 업태별 기본 감정 태그 반환
        return get_default_emotion_tags_by_types(types)


def get_default_emotion_tags_by_types(types):
    """업태별로 기본 감정 태그 반환"""
 
    # 업태별 기본 감정 태그 매핑
    type_emotion_map = {
        'restaurant': ['맛있음'],
        'food': ['맛있음'],
        'cafe': ['편안함'],
        'bar': ['활기참'],
        'bakery': ['정겨움'],
        'store': ['편리함'],
        'shopping_mall': ['활기참'],
        'amusement_park': ['즐거움'],
        'park': ['평온함'],
        'museum': ['지적임'],
        'library': ['조용함'],
        'gym': ['활기참'],
        'spa': ['편안함'],
        'hotel': ['편안함'],
        'hospital': ['안전함'],
        'school': ['지적임'],
        'university': ['지적임'],
        'bank': ['안전함'],
        'post_office': ['편리함'],
        'police': ['안전함'],
        'fire_station': ['안전함'],
        'gas_station': ['편리함'],
        'car_wash': ['편리함'],
        'car_rental': ['편리함'],
        'airport': ['활기참'],
        'train_station': ['활기참'],
        'bus_station': ['활기참'],
        'subway_station': ['활기참'],
        'taxi_stand': ['편리함'],
        'parking': ['편리함'],
        'point_of_interest': ['정겨움'],
        'establishment': ['정겨움']
    }
    
    # 업태에 맞는 감정 태그 찾기
    for place_type in types:
        if place_type in type_emotion_map:
            emotion_tags = type_emotion_map[place_type]
            print(f"[DEBUG] 업태 '{place_type}'에 맞는 기본 감정 태그: {emotion_tags}")
            return emotion_tags
    
    # 기본값
    print(f"[DEBUG] 매칭되는 업태가 없음, 기본값 '정겨움' 반환")
    return ['정겨움']
