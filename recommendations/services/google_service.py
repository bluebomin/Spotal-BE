# 구글맵 API 연동

import requests
from django.conf import settings

API_KEY = settings.GOOGLE_API_KEY

def get_similar_places(address, emotion_tags):
    """
    Google Places API를 이용해 용산구 내 영업 중인 가게 검색
    TODO: emotion_tags를 직접 반영하려면 리뷰 분석까지 필요 → GPT에 위임 가능
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": "용산구 맛집",  # 기본 검색 (추후 emotion 반영 가능)
        "key": API_KEY,
        "language": "ko" # 한국어 주소 반환하도록 
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []
    for r in data.get("results", []):
        if r.get("business_status") != "OPERATIONAL":
            continue  # 현재 영업 중만

        results.append({
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "image_url": f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={r['photos'][0]['photo_reference']}&key={API_KEY}"
            if "photos" in r else "", # 사진이 있으면 -> url 생성
            # 없으면 -> 빈 문자열 반환 
        })

    return results
