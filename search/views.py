import requests
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import quote

def search_store_realtime(api_key, query, dataset="LOCALDATA_072404_YS"):
    start = 1
    limit = 1000
    results = []
    api_key = quote(api_key)  # 서비스키 인코딩

    while True:
        end = start + limit - 1
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{dataset}/{start}/{end}/"
        response = requests.get(url)

        try:
            data = response.json()
        except Exception:
            break

        # ✅ dataset 변수 활용 (음식점/카페 구분)
        rows = data.get(dataset, {}).get("row", [])
        if not rows:
            break

        # 부분 검색 (대소문자 구분 없애기)
        for store in rows:
            name = (store.get("BPLCNM") or "").lower()
            jibun = (store.get("SITEWHLADDR") or "").lower()
            road = (store.get("RDNWHLADDR") or "").lower()

            if query.lower() in name or query.lower() in jibun or query.lower() in road:
                results.append(store)

        start += limit

    return results


def yongsan_store_status(request):
    query = request.GET.get("q")
    if not query:
        return JsonResponse({"error": "검색어(q)가 필요합니다."}, status=400)

    api_key = settings.PUBLIC_DATA_API_KEY

    foods = search_store_realtime(api_key, query, dataset="LOCALDATA_072404_YS")
    cafes = search_store_realtime(api_key, query, dataset="LOCALDATA_072405_YS")

    results = foods + cafes

    if not results:
        return JsonResponse({"error": "검색 결과가 없습니다."}, status=404)

    result = [
        {
            "name": s.get("BPLCNM"),
            "status": s.get("TRDSTATENM"),
            "jibun": s.get("SITEWHLADDR"),
            "road": s.get("RDNWHLADDR"),
        }
        for s in results  
    ]

    return JsonResponse(result, safe=False)
