from django.conf import settings
import requests
import pandas as pd
import os
from rapidfuzz import fuzz


CSV_PATH = os.path.join(settings.BASE_DIR, "data", "용산구이전가게.csv")
history_df = pd.read_csv(CSV_PATH)

# Google API Helper
def get_place_id(query):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id,name",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    candidates = res.get("candidates", [])
    if not candidates:
        return None

    place_name = candidates[0]["name"]

    # 문자열 유사도 계산 (0~100 사이)
    similarity = fuzz.ratio(query.lower(), place_name.lower())
    print(f"[DEBUG] 검색어={query}, 구글결과={place_name}, 유사도={similarity}")

    # 유사도가 60% 이상일 때만 인정 (기준은 상황에 맞게 조정 가능)
    if similarity < 60:
        return None

    return candidates[0]["place_id"]

def get_place_details(place_id, place_name=None):
    previous_address = None
    if place_name:
        match = history_df[history_df['상호명'].str.contains(place_name, case=False, na=False)]
        print("검색 키워드:", place_name)   # ← 검색어 확인

        if not match.empty:
            previous_address = match.iloc[0]['이전 전 주소']
        
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,reviews,business_status,types,photos",
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

    result['previous_address']=previous_address
    result["business_status"] = status   
    print("찾은 이전주소:", previous_address)

    return result

def get_photo_url(photo_ref, maxwidth=400):
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo_ref}&key={settings.GOOGLE_API_KEY}"