# 메인 추천 로직 

from community.models import Emotion, Location
from search.service.summary_card import generate_summary_card, generate_emotion_tags, extract_keywords
from search.service.address import normalize_korean_address
from .google_service import get_similar_places
from .utils import extract_neighborhood


def generate_recommendations(name, address, emotion_names):
    """
    입력받은 가게명, 주소, 감정태그(string 배열) 기반으로 추천 가게 리스트 생성
    """
    # 1. 구글맵 API에서 후보 가게 가져오기
    candidate_places = get_similar_places(address, emotion_names)

    recommended = []

    # 2. Emotion 모델 객체 가져오기 (string 배열 → DB 객체)
    base_emotion_objs = Emotion.objects.filter(name__in=emotion_names)

    for place in candidate_places:
        details = {"name": place["name"]}
        reviews = place.get("reviews", [])
        uptaenms = place.get("types", [])

        # 주소를 한국어로 정규화
        raw_address = place["address"]
        korean_address = normalize_korean_address(raw_address)

        # GPT 요약 생성 (search 앱 함수 사용)
        summary = generate_summary_card(details, reviews, uptaenms)

        # 감정태그 자동 생성 (search 앱 함수 사용)
        auto_emotions = generate_emotion_tags(details, reviews, uptaenms)
        auto_emotion_objs = Emotion.objects.filter(name__in=auto_emotions)

        # 입력 감정 + 자동 감정 합치기
        all_emotions = list(base_emotion_objs) + list(auto_emotion_objs)

        # 동네(Location) 추출
        neighborhood_name = extract_neighborhood(korean_address)
        location_obj, _ = Location.objects.get_or_create(name=neighborhood_name)

        # 추천 데이터 구성
        recommended.append({
            "name": place["name"],
            "address": korean_address,
            "image_url": place.get("image_url", ""),
            "summary": summary,
            "emotion_objs": all_emotions,
            "location_obj": location_obj,
        })

    return recommended
