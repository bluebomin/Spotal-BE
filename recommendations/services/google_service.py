# 구글맵 API 연동

import requests
from django.conf import settings

API_KEY = settings.GOOGLE_API_KEY


def get_place_details(place_id, place_name=None):
    """
    Google Places Details API로 특정 place_id의 상세 정보 가져오기
    """
    params = {
        "place_id": place_id,
        "key": API_KEY,
        "language": "ko",
        "fields": "name,formatted_address,geometry,types,rating,photos,reviews"
    }
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/details/json", 
        params=params
    )
    data = response.json()
    return data.get("result", {})


def get_similar_places(address, emotion_names, allowed_types=None, max_results=10):
    query = f"용산구 {address} {' '.join(emotion_names)}"
    params = {
        "query": query,
        "key": API_KEY,
        "language": "ko"
    }
    response = requests.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
    data = response.json()

    results = []
    for r in data.get("results", []):
        types = r.get("types", [])

        # 업태 필터 적용
        if allowed_types and not any(t in allowed_types for t in types):
            continue

        results.append({
            "place_id": r.get("place_id"),
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "image_url": get_photo_url(r["photos"][0]["photo_reference"]) if r.get("photos") else "",
        })

        if len(results) >= max_results:
            break

    return results



def get_photo_url(photo_reference, maxwidth=400):
    """
    Google Place Photo API로 사진 URL 생성
    """
    return (
        f"https://maps.googleapis.com/maps/api/place/photo"
        f"?maxwidth={maxwidth}&photoreference={photo_reference}&key={API_KEY}"
    )
