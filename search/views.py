
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import quote
from .service.search import search_store_realtime
from .service.summary_card import generate_summary_card, generate_emotion_tags


# 가게 요약 카드 
def yongsan_store_card(request):
    query = request.GET.get("q")
    if not query:
        return JsonResponse({"error": "검색어(q)가 필요합니다."}, status=400)

    api_key = settings.PUBLIC_DATA_API_KEY

    # 공공데이터 API에서 가져옴
    foods = search_store_realtime(api_key, query, dataset="LOCALDATA_072404_YS")
    cafes = search_store_realtime(api_key, query, dataset="LOCALDATA_072405_YS")
    bakeries = search_store_realtime(api_key, query, dataset="LOCALDATA_072218_YS")
    results = foods + cafes + bakeries

    if not results:
        return JsonResponse({"error": "검색 결과가 없습니다."}, status=404)

    # 공공데이터에서 가져온 결과 → 바로 요약카드 생성
    cards = []
    for store in results:
        try:
            summary = generate_summary_card(store)
            tags = generate_emotion_tags(store)
            cards.append({
                "store": {
                    "name": store.get("BPLCNM"),
                    "status": store.get("TRDSTATENM"),
                    "address": store.get("SITEWHLADDR") or store.get("RDNWHLADDR"),
                    "업태구분명": store.get("UPTAENM"),
                    },
                    "summary_card": summary,
                    "emotion_tags": tags
            })
        except Exception as e:
            return JsonResponse({"error": f"요약 카드 생성 중 오류 발생: {str(e)}"}, status=500)

    return JsonResponse(cards, safe=False)
