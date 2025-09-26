# 구글맵 API 연동

import requests
from django.conf import settings
from .cache_service import CacheService

API_KEY = settings.GOOGLE_API_KEY


def get_place_details(place_id, place_name=None):
    """
    Google Places Details API로 특정 place_id의 상세 정보 가져오기 (캐싱 적용)
    """
    # 캐시에서 먼저 조회
    cached_result = CacheService.cache_google_place_details(place_id)
    if cached_result:
        return cached_result
    
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
    result = data.get("result", {})
    
    # 결과를 캐시에 저장
    CacheService.set_google_place_details(place_id, result)
    
    return result


def get_similar_places(address, emotion_names, allowed_types=None, max_results=8):
    query = f"{address} 맛집" if "cafe" not in (allowed_types or []) else f"{address} 카페"
    
    # 캐시에서 먼저 조회
    cached_results = CacheService.cache_google_places_search(query, address, allowed_types or [])
    if cached_results:
        return cached_results[:max_results]

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

        # cafe 모드 / 비-cafe 모드
        if "cafe" in (allowed_types or []):
            if "cafe" not in types:
                continue
        else:
            if "cafe" in types:
                continue

        # 점수 계산
        score = 0
        if any(keyword in r.get("name", "") for keyword in emotion_names):
            score += 2
        if "cafe" in types:
            score += 3
        score += r.get("rating", 0)
        score += len(r.get("reviews", [])) * 0.5

        results.append({
            "place_id": r.get("place_id"),
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "photo_reference": r["photos"][0]["photo_reference"] if r.get("photos") else "",
            "_score": score,
        })

    # 점수 순 정렬
    results = sorted(results, key=lambda x: x["_score"], reverse=True)

    # 결과를 캐시에 저장
    CacheService.set_google_places_search(query, address, allowed_types or [], results)

    return results[:max_results]



def get_photo_url(photo_reference, maxwidth=400):
    """
    Google Place Photo API로 사진 URL 생성
    """
    return (
        f"https://maps.googleapis.com/maps/api/place/photo"
        f"?maxwidth={maxwidth}&photoreference={photo_reference}&key={API_KEY}"
    )
