from openai import OpenAI
from django.conf import settings
import logging
import requests
from search.models import SearchShop
from community.models import Emotion, Location
from search.service.address import normalize_korean_address

logger = logging.getLogger(__name__)

def call_gpt_api(prompt, model="gpt-3.5-turbo"):
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


####### min_rating -> 최소 평점, max_results -> 추천 가게 개수 
def get_google_places_by_location_and_rating(location_name, min_rating=3.5, max_results=10):
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
            'type': 'restaurant',  # 음식점 타입
            'maxprice': 4,  # 가격대 제한 (1-4)
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'OK':
            logger.error(f"Google Places API 오류: {data['status']}")
            return []
        
        # 평점 기준으로 필터링
        high_rated_places = []
        for place in data['results']:
            if 'rating' in place and place['rating'] >= min_rating:
                high_rated_places.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'rating': place['rating'],
                    'address': place.get('formatted_address', ''),
                    'types': place.get('types', []),
                    'photos': place.get('photos', []),
                    'price_level': place.get('price_level', 0),
                    'geometry': place.get('geometry', {}),
                    'user_ratings_total': place.get('user_ratings_total', 0)
                })
        
        # 평점순 정렬 (높은 순)
        high_rated_places.sort(key=lambda x: x['rating'], reverse=True)
        
        logger.info(f"{location_name}에서 평점 {min_rating} 이상 가게 {len(high_rated_places)}개 발견")
        return high_rated_places[:max_results]
        
    except Exception as e:
        logger.error(f"Google Maps API 호출 실패: {str(e)}")
        return []

def get_place_details_with_reviews(place_id):
    """Google Places API로 가게 상세 정보와 리뷰 조회"""
    try:
        # Place Details API
        url = f"https://maps.googleapis.com/maps/api/place/details/json"
        
        params = {
            'place_id': place_id,
            'key': settings.GOOGLE_API_KEY,
            'language': 'ko',
            'fields': 'name,formatted_address,rating,reviews,types,photos,price_level,geometry,user_ratings_total,opening_hours,website,formatted_phone_number'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'OK':
            return None
        
        return data['result']
        
    except Exception as e:
        logger.error(f"Place Details API 호출 실패: {str(e)}")
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

def enrich_place_with_details(place_basic, place_details):
    """기본 정보와 상세 정보를 결합하여 가게 정보를 풍부하게 만듦"""
    try:
        # 주소 정규화 (한국어로 변환)
        normalized_address = normalize_korean_address(place_details.get('formatted_address', ''))
        
        # 가게 정보 단순화 (필요한 정보만)
        enriched_place = {
            'name': place_basic.get('name', ''),
            'address': normalized_address,
            'status': '운영 중',  # 기본값
            'summary': '',  # GPT가 생성할 예정
            'emotion_tags': [],  # GPT가 생성할 예정
            'google_rating': place_basic.get('rating', 0),
            'place_id': place_basic.get('place_id', '')
        }
        
        return enriched_place
        
    except Exception as e:
        print(f"가게 정보 풍부화 중 오류: {e}")
        return place_basic

def generate_gpt_emotion_based_recommendations(places, emotions, location):
    """GPT를 사용하여 감정 기반 가게 추천 생성"""
    try:
        # 가게별 요약과 감정 태그 생성
        enriched_places = []
        
        for place in places:
            # GPT로 가게별 요약과 감정 태그 생성
            prompt = f"""
            다음 가게에 대해 간단한 요약과 감정 태그를 생성해주세요:
            
            가게명: {place['name']}
            주소: {place['address']}
            구글 평점: {place['google_rating']}
            
            요청된 감정: {', '.join(emotions)}
            
            다음 형식으로 응답해주세요:
            요약: (가게의 특징을 1-2문장으로 간단히)
            감정태그: (요청된 감정 중 가장 적합한 2-3개를 쉼표로 구분)
            """
            
            gpt_response = call_gpt_api(prompt)
            
            # GPT 응답 파싱
            summary = ""
            emotion_tags = []
            
            if gpt_response:
                lines = gpt_response.split('\n')
                for line in lines:
                    if line.startswith('요약:'):
                        summary = line.replace('요약:', '').strip()
                    elif line.startswith('감정태그:'):
                        tags_text = line.replace('감정태그:', '').strip()
                        emotion_tags = [tag.strip() for tag in tags_text.split(',')]
            
            # 가게 정보에 요약과 감정 태그 추가
            place['summary'] = summary
            place['emotion_tags'] = emotion_tags
            enriched_places.append(place)
        
        # 전체 추천 설명 생성
        overall_prompt = f"""
        {location}에서 {', '.join(emotions)} 감정을 느낄 수 있는 가게들을 추천해드립니다.
        
        추천된 가게들:
        {chr(10).join([f"- {place['name']}: {place['summary']}" for place in enriched_places])}
        
        이 가게들은 {', '.join(emotions)} 감정을 잘 표현하는 곳들입니다. 
        각 가게의 특징과 분위기를 고려하여 방문해보시기 바랍니다.
        """
        
        overall_recommendation = call_gpt_api(overall_prompt)
        
        return {
            'places': enriched_places,
            'overall_recommendation': overall_recommendation or f"{location}의 {', '.join(emotions)} 가게 추천이 완료되었습니다."
        }
        
    except Exception as e:
        print(f"GPT 추천 생성 중 오류: {e}")
        return None

def get_inference_recommendations(location_id, emotion_ids, min_rating=4.8):
    """사용자 선택 기반 추천 시스템 메인 함수 - Google Maps API + GPT"""
    try:
        # 1. 동네와 감정 정보 가져오기
        location = Location.objects.get(pk=location_id)
        emotions = Emotion.objects.filter(pk__in=emotion_ids)
        
        if not location or not emotions.exists():
            return None, "동네 또는 감정 정보를 찾을 수 없습니다."
        
        location_name = location.name
        emotion_names = [emotion.name for emotion in emotions]
        
        # 2. Google Maps API로 고평점 가게 조회
        high_rated_places = get_google_places_by_location_and_rating(
            location_name, min_rating, max_results=20
        )
        
        if not high_rated_places:
            return None, f"{location_name} 지역에서 평점 {min_rating} 이상의 가게를 찾을 수 없습니다."
        
        # 3. 각 가게의 상세 정보 보강
        enriched_places = []
        for place in high_rated_places:
            place_details = get_place_details_with_reviews(place['place_id'])
            enriched_place = enrich_place_with_details(place, place_details)
            enriched_places.append(enriched_place)
        
        # 4. GPT가 감정 기반으로 최종 추천
        gpt_recommendations = generate_gpt_emotion_based_recommendations(
            enriched_places, emotion_names, location_name
        )
        
        if not gpt_recommendations:
            return None, "GPT 추천 생성에 실패했습니다."
        
        # 5. 최종 결과 반환 
        return {
            'location': location_name,
            'emotions': emotion_names,
            'min_rating': min_rating,
            'total_high_rated_found': len(high_rated_places),
            'gpt_recommendations': gpt_recommendations['overall_recommendation'],
            'top_places': gpt_recommendations['places']
        }, None
        
    except Exception as e:
        logger.error(f"추천 시스템 실행 실패: {str(e)}")
        return None, f"추천 시스템 오류: {str(e)}"

def get_inference_recommendations_with_custom_rating(location_id, emotion_ids, min_rating=4.8):
    """사용자가 평점 기준을 조정할 수 있는 버전"""
    return get_inference_recommendations(location_id, emotion_ids, min_rating)