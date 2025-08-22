# 메인 추천 로직

from .google_service import get_similar_places
from .gpt_service import generate_summary
from .utils import extract_neighborhood
from community.models import Emotion, Location


def generate_recommendations(name, address, emotion_names):
    """
    입력받은 가게명, 주소, 감정태그 기반으로 추천 가게 리스트 생성
    """
    # 1. 구글맵 API에서 용산구 + 영업중 가게 검색
    candidate_places = get_similar_places(address, emotion_names)[:8] # 8개 추천

    recommended = []

    # 2. Emotion 모델 객체 가져오기
    emotion_objs = Emotion.objects.filter(name__in=emotion_names)

    for place in candidate_places:
        # GPT 요약 생성
        summary = generate_summary(place)

        # 동네(Location) 객체 추출 (ex. '청파동', '이태원동')
        neighborhood_name = extract_neighborhood(place["address"])
        location_obj, _ = Location.objects.get_or_create(name=neighborhood_name)

        recommended.append({
            "name": place["name"],
            "address": place["address"],
            "image_url": place.get("image_url", ""),
            "summary": summary,
            "emotion_objs": emotion_objs,      # ManyToMany에 연결
            "location_obj": location_obj,      # FK로 연결
        })

    return recommended

