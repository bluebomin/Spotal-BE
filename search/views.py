from rest_framework.decorators import api_view
from rest_framework.response import Response
from .service.summary_card import generate_summary_card, generate_emotion_tags
from .serializers import SearchShopSerializer
from community.models import Emotion
from .service.search import *
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from .service.address import *


@api_view(['GET'])
@permission_classes([AllowAny]) 
def store_card(request):
    query = request.GET.get("q")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if not query:
        return Response({"message": "검색어(q)가 필요합니다."}, status=400)
    if not lat or not lng:
        return Response({"message": "위도(lat), 경도(lng)가 필요합니다."}, status=400)

    # float 변환 (문자열 → 숫자)
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response({"message": "위도(lat), 경도(lng)는 숫자여야 합니다."}, status=400)

    # 1. 구글 Place ID 찾기 (위치 기반 + 유사도)
    place_id, place_name = get_place_id(query, lat, lng, threshold=90)
    if not place_id:
        return Response({"message": "구글맵에서 가게를 찾을 수 없습니다."}, status=200)

    # 2. 구글 Place 상세 정보
    details = get_place_details(place_id, place_name)
    reviews = [r["text"] for r in details.get("reviews", [])]
    uptaenms = details.get("types", [])
    

    # 영문 → 한국어 변환 처리 (GPT API)
    name = details.get("name")
    address = details.get("formatted_address")

    name_ko = translate_to_korean(name) if name else None
    address_ko = translate_to_korean(address) if address else None

    # 3. GPT 요약 카드 / 감정 태그 생성
    summary = generate_summary_card(details, reviews,uptaenms)
    tags = generate_emotion_tags(details, reviews, uptaenms)

    # 4. Emotion 모델 매핑
    emotion_ids = []
    for tag_name in (tags or []):
        emotion_obj, _ = Emotion.objects.get_or_create(name=tag_name)
        emotion_ids.append(emotion_obj.pk)

    # 5. 사진 URL 처리
    photo = details.get("photos", [])
    photo_url = None
    if photo:
        photo_url = get_photo_url(photo[0]["photo_reference"])  # 첫 번째 사진만

    # 6. DB 저장
    shop_data = {
        "emotion_ids": emotion_ids,
        "name": name_ko or details.get("name"),
        "address": address_ko or details.get("formatted_address"),
        "status": details.get("business_status"),
        "uptaenm": ", ".join(details.get("types", [])[:3]) or "기타"
    }
    serializer = SearchShopSerializer(
        data=shop_data,
        context={
            'previous_address': details.get('previous_address'),
            'previous_lat': details.get('previous_lat'),
            'previous_lng': details.get('previous_lng')
        }
    )

    serializer.is_valid(raise_exception=True)
    shop = serializer.save()

    # 7. 응답
    return Response({
        "message": "가게 정보 반환 성공",
        "store": serializer.data,
        "latitude": details["geometry"]["location"]["lat"],   # 위도
        "longitude": details["geometry"]["location"]["lng"],  # 경도
        "summary_card": summary,
        "google_rating": details.get("rating"),
        "photos": photo_url,
    }, status=200)
