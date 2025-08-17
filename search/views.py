from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .service.summary_card import generate_summary_card, generate_emotion_tags
from .serializers import SearchShopSerializer
from community.models import Emotion

import requests


# Google API Helper
def get_place_id(query):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    candidates = res.get("candidates", [])
    return candidates[0]["place_id"] if candidates else None

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,reviews,business_status,types,photos",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})

def get_photo_url(photo_ref, maxwidth=400):
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo_ref}&key={settings.GOOGLE_API_KEY}"


@api_view(['GET'])
def store_card(request):
    query = request.GET.get("q")
    if not query:
        return Response({"error": "검색어(q)가 필요합니다."}, status=400)

    # 1. 구글 Place ID 찾기
    place_id = get_place_id(query)
    if not place_id:
        return Response({"error": "구글맵에서 가게를 찾을 수 없습니다."}, status=404)

    # 2. 구글 Place 상세 정보
    details = get_place_details(place_id)
    reviews = [r["text"] for r in details.get("reviews", [])]

    # 3. GPT 요약 카드 / 감정 태그 생성
    summary = generate_summary_card(details, reviews)
    tags = generate_emotion_tags(details, reviews)

    # 4. Emotion 모델 매핑
    emotion_ids = []
    for name in (tags or []):
        emotion_obj, _ = Emotion.objects.get_or_create(name=name)
        emotion_ids.append(emotion_obj.pk)

    # 5. 사진 URL 처리
    photo = details.get("photos", [])
    photo_url = None
    if photo:
        photo_url = get_photo_url(photo[0]["photo_reference"])  # ✅ 첫 번째 사진만



    # 5. DB 저장
    shop_data = {
        "emotion_ids": emotion_ids,
        "name": details.get("name"),
        "address": details.get("formatted_address"),
        "status": details.get("business_status"),
        "uptaenm" : details.get("types", [None])[0] or "기타" 
    }
    serializer = SearchShopSerializer(data=shop_data)
    serializer.is_valid(raise_exception=True)
    shop = serializer.save()

    # 6. 응답
    return Response({
        "store": serializer.data,
        "summary_card": summary,
        "google_rating": details.get("rating"),
        "photos": photo_url,
    }, status=200)


    