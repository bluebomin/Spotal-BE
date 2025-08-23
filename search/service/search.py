from django.conf import settings
import requests
import pandas as pd
import os
from rapidfuzz import fuzz

CSV_PATH = os.path.join(settings.BASE_DIR, "data", "용산구이전가게.csv")
history_df = pd.read_csv(CSV_PATH)

# Google API Helper
def get_place_id(query, lat, lng, threshold=60):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "rankby": "distance",
        "language": "ko",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    candidates = res.get("results", [])
    if not candidates:
        return None, None

    # 1. 정확히 일치하는 이름 있으면 최우선
    for c in candidates:
        if c["name"] == query:
            return c["place_id"], c["name"]

    # 2. 가장 가까운 후보
    nearest = candidates[0]
    place_name = nearest["name"]
    

    # 3. 유사도 검사
    similarity = fuzz.partial_ratio(query.lower(), place_name.lower())
    print(f"[DEBUG] 검색어={query}, 구글결과={place_name}, 유사도={similarity}")

    if similarity < threshold:
        best_match = max(
            candidates,
            key=lambda c: fuzz.ratio(query.lower(), c["name"].lower()),
        )
        best_name = best_match["name"]
        best_score = fuzz.ratio(query.lower(), best_name.lower())
        print(f"[DEBUG] Fallback 선택={best_name}, 유사도={best_score}")

        if best_score >= threshold:
            return best_match["place_id"], best_name
        else:
            return None, None

    return nearest["place_id"], place_name


def get_place_details(place_id, place_name=None):
    """
    place_id 기반 상세정보 조회 + 과거 이전주소 매핑
    """
    previous_address = None
    if place_name:
        match = history_df[history_df['상호명'].str.contains(place_name, case=False, na=False)]
        print("검색 키워드:", place_name)

        if not match.empty:
            previous_address = match.iloc[0]['이전 전 주소']

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,geometry,rating,types,photos,business_status,reviews",
        "language": "ko",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    result = res.get("result", {})

    # 상태 매핑
    if previous_address:
        status = "이전함"
    else:
        google_status = result.get("business_status")
        if google_status == "OPERATIONAL":
            status = "운영중"
        else:
            status = "폐업함"

    result["previous_address"] = previous_address
    result["business_status"] = status
    print("찾은 이전주소:", previous_address)

    return result


def get_photo_url(photo_ref, maxwidth=400):
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo_ref}&key={settings.GOOGLE_API_KEY}"
