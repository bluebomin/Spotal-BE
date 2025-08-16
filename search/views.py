import requests
from django.http import JsonResponse
from django.conf import settings



from urllib.parse import quote

def search_store_realtime(api_key, query):
    start = 1
    limit = 1000
    results = []
    api_key = quote(api_key)  # 서비스키 인코딩

    while True:
        end = start + limit - 1
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/LOCALDATA_072404_YS/{start}/{end}/"
        response = requests.get(url)

        # 응답 확인 (디버깅용)
        print("URL:", url, "STATUS:", response.status_code)

        try:
            data = response.json()
        except Exception:
            print("RAW:", response.text[:200])  # JSON 아닐 때 원인 출력
            break  # 반복 중단 (더 이상 가져올 수 없음)

        rows = data.get("LOCALDATA_072404_YS", {}).get("row", [])
        if not rows:
            break

        # 부분 검색
        for store in rows:
            if (
                query in (store.get("BPLCNM") or "")
                or query in (store.get("SITEWHLADDR") or "")
                or query in (store.get("RDNWHLADDR") or "")
            ):
                results.append(store)

        start += limit

    return results





def yongsan_store_status(request):
    query = request.GET.get("q")
    if not query:
        return JsonResponse({"error": "검색어(q)가 필요합니다."}, status=400)

    stores = search_store_realtime(settings.PUBLIC_DATA_API_KEY, query)

    if not stores:
        return JsonResponse({"message": f"'{query}' 에 해당하는 업소가 없습니다."}, status=404)

    result = [
        {
            "name": s.get("BPLCNM"),
            "status": s.get("TRDSTATENM"),
            "jibun": s.get("SITEWHLADDR"),
            "road": s.get("RDNWHLADDR"),
        }
        for s in stores   # stores는 dict 리스트
    ]

    return JsonResponse(result, safe=False)
