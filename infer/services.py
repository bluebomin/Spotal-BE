from openai import OpenAI
from django.conf import settings
import logging
import requests
from search.models import SearchShop
from community.models import Emotion, Location
from search.service.address import normalize_korean_address
from search.service.summary_card import generate_summary_card, generate_emotion_tags
from search.service.search import get_place_details, get_place_id

logger = logging.getLogger(__name__)

def call_gpt_api(prompt, model="gpt-4o-mini"):
    """GPT API 호출 함수"""
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"GPT API 호출 실패: {str(e)}")
        return None

def get_place_photo_url(photo_reference, max_width=400):
    """Google Places API로 가게 사진 URL 생성"""
    try:
        base_url = "https://maps.googleapis.com/maps/api/place/photo"
        params = {
            'maxwidth': max_width,
            'photoreference': photo_reference,
            'key': settings.GOOGLE_API_KEY
        }
        
        # 실제 사진 URL을 반환하지 않고, 프론트엔드에서 사용할 수 있는 URL 생성
        photo_url = f"{base_url}?maxwidth={max_width}&photoreference={photo_reference}&key={settings.GOOGLE_API_KEY}"
        return photo_url
        
    except Exception as e:
        logger.error(f"사진 URL 생성 실패: {str(e)}")
        return None

def get_google_places_by_location(location_name, max_results=8):
    """Google Maps API로 특정 지역의 고평점 가게들 조회"""
    try:
        # Google Places API - Text Search
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # 검색 쿼리 구성 (지역명 + 음식점/카페 등)
        query = f"{location_name} 음식점 카페"
        
        params = {
            'query': query,
            'key': settings.GOOGLE_API_KEY,
            'language': 'ko',
            'region': 'kr',
            'type': 'restaurant',
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'OK':
            logger.error(f"Google Places API 오류: {data['status']}")
            return []
        
        # 평점 4.0+ 가게만 필터링 (더 엄격한 기준으로 생성 시간 단축)
        min_rating = 3.6
        high_rated_places = []
        for place in data['results']:
            if 'rating' in place and place['rating'] >= min_rating:
                # 사진 URL 생성
                image_url = ""
                if 'photos' in place and place['photos']:
                    photo_ref = place['photos'][0]['photo_reference']
                    image_url = get_place_photo_url(photo_ref)
                
                high_rated_places.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'rating': place['rating'],
                    'address': place.get('formatted_address', ''),
                    'types': place.get('types', []),
                    'photos': place.get('photos', []),
                    'photo_reference': photo_ref,  
                    'image_url': image_url,  # 최종 url이고, 있어도 무방
                    'price_level': place.get('price_level', 0),
                    'geometry': place.get('geometry', {}),
                    'user_ratings_total': place.get('user_ratings_total', 0)
                })
        
        # 평점순 정렬
        high_rated_places.sort(key=lambda x: x['rating'], reverse=True)
        
        logger.info(f"{location_name}에서 평점 {min_rating}+ 가게 {len(high_rated_places)}개 발견")
        return high_rated_places[:max_results]
        
    except Exception as e:
        logger.error(f"Google Maps API 호출 실패: {str(e)}")
        return []

def get_place_details_with_reviews(place_id, place_name=None):
    """Google Places API로 가게 상세 정보와 리뷰 조회 - search 앱 서비스 활용"""
    try:
        # search 앱의 get_place_details 함수 사용 (이전함 상태 처리 포함)
        place_details = get_place_details(place_id, place_name)
        
        if not place_details:
            return None
        
        # search 앱에서 반환하는 status를 infer 앱의 status로 매핑
        search_status = place_details.get('business_status')
        if search_status == '운영중':
            place_details['status'] = 'operating'
        elif search_status == '폐업함':
            place_details['status'] = 'closed'
        elif search_status == '이전함':
            place_details['status'] = 'moved'
        else:
            place_details['status'] = 'operating'  # 기본값
        
        return place_details
        
    except Exception as e:
        logger.error(f"Place Details API 호출 실패: {str(e)}")
        return None

def enrich_place_with_details(place_basic, place_details):
    """기본 정보와 상세 정보를 결합하여 가게 정보를 풍부하게 만듦"""
    try:
        # 주소 정규화 (search 앱 서비스 활용)
        normalized_address = normalize_korean_address(place_details.get('formatted_address', ''))
        
        # 리뷰 데이터 추출
        reviews = []
        if 'reviews' in place_details:
            for review in place_details['reviews'][:5]:  # 상위 5개 리뷰만
                reviews.append({
                    'text': review.get('text', ''),
                    'rating': review.get('rating', 0),
                    'time': review.get('time', 0)
                })
        
        # 사진 URL 처리 (place_basic에서 가져오기)
        image_url = place_basic.get('image_url', '')
        photo_reference = place_basic.get('photo_reference', '')
        
        # 운영 상태는 place_details에서 가져오기 (search 앱에서 이미 매핑됨)
        status = place_details.get('status', 'operating')
        
        # 가게 정보 단순화
        enriched_place = {
            'name': place_basic.get('name', ''),
            'address': normalized_address,
            'status': status,  # place_details에서 가져온 상태값 사용
            'summary': '',
            'emotion_tags': [],  # search 앱에서 생성된 감정 태그 사용
            'google_rating': place_basic.get('rating', 0),
            'place_id': place_basic.get('place_id', ''),
            'types': place_basic.get('types', []),
            'reviews': reviews,  # 실제 리뷰 데이터
            'user_ratings_total': place_details.get('user_ratings_total', 0),
            'image_url': image_url,  # 사진 URL 추가
            'photo_reference': photo_reference
        }
        
        return enriched_place
        
    except Exception as e:
        logger.error(f"가게 정보 풍부화 중 오류: {e}")
        return place_basic

def generate_gpt_emotion_based_recommendations(places, emotions, location):
    """감정 기반 가게 추천 생성 - search 앱 서비스 활용 + 다양성 확보"""
    try:
        enriched_places = []
        
        for place in places:
            # search 앱의 summary_card 서비스 활용
            place_details = {
                'name': place['name'],
                'address': place['address'],
                'rating': place.get('google_rating', 0)
            }
            
            # 실제 리뷰 데이터 사용 (더 이상 가짜 데이터 아님)
            reviews = []
            if 'reviews' in place and place['reviews']:
                reviews = [review.get('text', '') for review in place['reviews']]
            else:
                reviews = [f"평점: {place.get('google_rating', 0)}점"]
            
            # search 앱 서비스로 요약과 감정 태그 생성
            summary = generate_summary_card(place_details, reviews, place.get('types', []))
            emotion_tags = generate_emotion_tags(place['name'], place.get('reviews', []), place.get('types', []))
            
            # 가게 정보에 요약과 감정 태그 추가
            place['summary'] = summary
            place['emotion_tags'] = emotion_tags
            enriched_places.append(place)
        
        # 다양성 확보를 위한 개선된 프롬프트
        overall_prompt = f"""
        {location}에서 {', '.join(emotions)} 감정을 느낄 수 있는 가게들을 추천해드립니다.
        
        **추억의 가게 찾기 목적:**
        이 추천은 사용자가 추억의 가게를 찾는 것이 목적입니다.
        우선 사용자는 동네를 선택하고, 찾고자 하는 가게에서 그 당시에 느꼈던 감정을 선택할 것입니다.
        그러면 해당당 동네에서 구글 리뷰를 통해 해당 감정을 느꼈을 만한 가게를 찾아주어야 합니다.

        추천된 가게들:
        {chr(10).join([f"- {place['name']}: {place['summary']}" for place in enriched_places])}
        
        **중요한 지침:**
        1. 사용자가 찾고자 하는 가게가 현재재 운영중인지 폐업중인지 모를 수 있으므로 운영중인 가게만 추천하면 안 됩니다. 
        2. 폐업한 가게라면 "그곳에서의 추억", "그 시절의 분위기" 등을 강조하면 됩니다.
        3. 운영중인 가게라면 "지금도 그 감정을 느낄 수 있는 곳"임을 강조해 주세요. 
        4. 각 가게마다 서로 다른 추억과 경험을 제공할 수 있음을 표현하세요
        5. 사용자가 과거의 기억을 되살릴 수 있는 다양한 선택지를 제시하세요
        6. 같은 감정이라도 가게마다 다른 방식으로 표현됨을 강조하세요
        7. 각 가게의 고유한 분위기와 특징을 구체적으로 설명하세요
        8. 최소 3개는 추천해줘야 한다.
        
        **다양성 확보 요청:**
        - 각 가게가 {', '.join(emotions)} 감정을 어떻게 다르게 표현하는지 구체적으로 분석
        - 단조로운 설명을 피하고, 각 가게만의 특별한 분위기나 특징을 강조
        - 사용자가 다양한 선택지를 가질 수 있도록 각 가게의 차별점을 부각
        
        이 가게들은 {', '.join(emotions)} 감정을 대표하는 곳들이지만,
        각각 다른 추억과 의미를 가지고 있습니다.
        사용자가 자신의 추억 속 가게를 찾을 수 있도록 
        각 가게의 고유한 매력과 의미를 구체적이고 상세하게 설명해주세요.
        """
        
        overall_recommendation = call_gpt_api(overall_prompt)
        
        return {
            'places': enriched_places,
            'overall_recommendation': overall_recommendation or f"{location}의 {', '.join(emotions)} 가게 추천이 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"GPT 추천 생성 중 오류: {e}")
        return None

def get_inference_recommendations(location_ids, emotion_ids, max_results=10):  # location_id → location_ids로 변경
    """사용자 선택 기반 추천 시스템 메인 함수 - 추천 로직에 집중"""
    try:
        # 1. 동네와 감정 정보 가져오기
        locations = Location.objects.filter(pk__in=location_ids)
        emotions = Emotion.objects.filter(pk__in=emotion_ids)
        
        if not locations.exists() or not emotions.exists():
            return None, "동네 또는 감정 정보를 찾을 수 없습니다."
        
        location_names = [location.name for location in locations]
        emotion_names = [emotion.name for emotion in emotions]
        
        # 2. 여러 동네에서 Google Maps API로 가게 조회
        all_places = []
        for location_name in location_names:
            places = get_google_places_by_location(location_name, max_results // len(location_names))
            if places:
                all_places.extend(places)
        
        if not all_places:
            return None, f"{', '.join(location_names)} 지역에서 가게를 찾을 수 없습니다."
        
        # 3. 각 가게의 상세 정보 보강 (실제 리뷰 포함, 상위 3개만)
        enriched_places = []
        for place in all_places[:6]:  # 상위 3개만 처리하여 시간 단축
            # Google Places API에서 상세 정보와 리뷰 가져오기
            place_details = get_place_details_with_reviews(place['place_id'], place['name'])
            enriched_place = enrich_place_with_details(place, place_details)
            enriched_places.append(enriched_place)
        
        # 4. GPT가 감정 기반으로 최종 추천 (infer 앱만의 추천 로직)
        gpt_recommendations = generate_gpt_emotion_based_recommendations(
            enriched_places, emotion_names, ', '.join(location_names)
        )
        
        if not gpt_recommendations:
            return None, "GPT 추천 생성에 실패했습니다."
        
        # 5. 최종 결과 반환 (추천 결과 구조화)
        return {
            'location': ', '.join(location_names),  # 여러 동네명을 쉼표로 구분
            'emotions': emotion_names,
            'total_places_found': len(all_places),
            'gpt_recommendation': gpt_recommendations['overall_recommendation'],
            'top_places': gpt_recommendations['places']
        }, None
        
    except Exception as e:
        logger.error(f"추천 시스템 실행 실패: {str(e)}")
        return None, f"추천 시스템 오류: {str(e)}"

def get_inference_recommendations_with_custom_rating(location_ids, emotion_ids, max_results=6):
    """사용자가 결과 수를 조정할 수 있는 버전"""
    return get_inference_recommendations(location_ids, emotion_ids, max_results)
