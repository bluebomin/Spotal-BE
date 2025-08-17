from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .service.search import search_store_realtime
from .service.summary_card import generate_summary_card, generate_emotion_tags
from .serializers import SearchShopSerializer
from .models import SearchShop
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
        "fields": "name,formatted_address,rating,review,photo",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})


@api_view(['GET'])
def yongsan_store_card(request):
    query = request.GET.get("q")
    if not query:
        return JsonResponse({"error": "검색어(q)가 필요합니다."}, status=400)

    api_key = settings.PUBLIC_DATA_API_KEY

    # 1. 공공데이터 API로 기본 정보 가져오기
    foods = search_store_realtime(api_key, query, dataset="LOCALDATA_072404_YS")
    cafes = search_store_realtime(api_key, query, dataset="LOCALDATA_072405_YS")
    bakeries = search_store_realtime(api_key, query, dataset="LOCALDATA_072218_YS")
    results = foods + cafes + bakeries

    if not results:
        return JsonResponse({"error": "검색 결과가 없습니다."}, status=404)

    cards = []
    for store in results:
        try:
            # 2. Google Places API로 리뷰 가져오기
            place_id = get_place_id(store.get("BPLCNM"))
            reviews, details = [], {}
            if place_id:
                details = get_place_details(place_id)
                reviews = [r["text"] for r in details.get("reviews", [])]

            # 3. GPT 요약 카드 생성
            summary = generate_summary_card(details, reviews)

            # 4. GPT 감정 태그 생성
            tags = generate_emotion_tags(details, reviews)
            emotion_ids = []
            for name in (tags or []):
                emotion_obj, _ = Emotion.objects.get_or_create(name=name)
                emotion_ids.append(emotion_obj.pk)

            # 5. DB 저장
            shop_data = {
                "emotion_ids": emotion_ids,
                "name": store.get("BPLCNM"),
                "address": store.get("SITEWHLADDR") or store.get("RDNWHLADDR"),
                "status": store.get("TRDSTATENM"),
                "uptaenm": store.get("UPTAENM"),
                
            }
            serializer = SearchShopSerializer(data=shop_data)
            serializer.is_valid(raise_exception=True)
            shop = serializer.save()

            # 6. 카드 응답
            cards.append({
                "store": serializer.data,
                "summary_card": summary,
                "emotion_tags": tags,
                "google_rating": details.get("rating"),
                
            })

        except Exception as e:
            return JsonResponse({"error": f"요약 카드 생성 중 오류 발생: {str(e)}"}, status=500)

    return Response(cards, status=200)
