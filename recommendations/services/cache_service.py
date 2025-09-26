# 캐싱 서비스 - API 호출 최적화
from django.core.cache import cache
import hashlib
import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """API 호출 결과를 캐싱하여 성능 최적화"""
    
    # 캐시 만료 시간 (초)
    CACHE_TIMEOUTS = {
        'google_places_search': 3600,  # 1시간
        'google_place_details': 7200,  # 2시간  
        'gpt_summary': 86400,          # 24시간
        'gpt_emotion_tags': 86400,     # 24시간
        'gpt_emotion_expansion': 86400, # 24시간
    }
    
    @staticmethod
    def _generate_cache_key(prefix: str, data: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 데이터를 정렬하여 일관된 키 생성
        sorted_data = json.dumps(data, sort_keys=True)
        hash_key = hashlib.md5(sorted_data.encode()).hexdigest()
        return f"{prefix}:{hash_key}"
    
    @staticmethod
    def get_cached_result(cache_key: str) -> Optional[Any]:
        """캐시에서 결과 조회"""
        try:
            result = cache.get(cache_key)
            if result:
                logger.info(f"캐시 히트: {cache_key}")
            return result
        except Exception as e:
            logger.error(f"캐시 조회 실패: {e}")
            return None
    
    @staticmethod
    def set_cached_result(cache_key: str, data: Any, timeout: int) -> bool:
        """캐시에 결과 저장"""
        try:
            cache.set(cache_key, data, timeout)
            logger.info(f"캐시 저장: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")
            return False
    
    @classmethod
    def cache_google_places_search(cls, query: str, location: str, allowed_types: List[str]) -> Optional[List[Dict]]:
        """Google Places 검색 결과 캐싱"""
        cache_data = {
            'query': query,
            'location': location,
            'allowed_types': allowed_types
        }
        cache_key = cls._generate_cache_key('google_places_search', cache_data)
        
        # 캐시에서 조회
        result = cls.get_cached_result(cache_key)
        if result:
            return result
        
        return None
    
    @classmethod
    def set_google_places_search(cls, query: str, location: str, allowed_types: List[str], results: List[Dict]) -> bool:
        """Google Places 검색 결과 캐싱"""
        cache_data = {
            'query': query,
            'location': location,
            'allowed_types': allowed_types
        }
        cache_key = cls._generate_cache_key('google_places_search', cache_data)
        
        return cls.set_cached_result(cache_key, results, cls.CACHE_TIMEOUTS['google_places_search'])
    
    @classmethod
    def cache_google_place_details(cls, place_id: str) -> Optional[Dict]:
        """Google Place 상세 정보 캐싱"""
        cache_data = {'place_id': place_id}
        cache_key = cls._generate_cache_key('google_place_details', cache_data)
        
        return cls.get_cached_result(cache_key)
    
    @classmethod
    def set_google_place_details(cls, place_id: str, details: Dict) -> bool:
        """Google Place 상세 정보 캐싱"""
        cache_data = {'place_id': place_id}
        cache_key = cls._generate_cache_key('google_place_details', cache_data)
        
        return cls.set_cached_result(cache_key, details, cls.CACHE_TIMEOUTS['google_place_details'])
    
    @classmethod
    def cache_gpt_summary(cls, place_name: str, reviews: List[str], types: List[str]) -> Optional[str]:
        """GPT 요약 결과 캐싱"""
        cache_data = {
            'place_name': place_name,
            'reviews': reviews,
            'types': types
        }
        cache_key = cls._generate_cache_key('gpt_summary', cache_data)
        
        return cls.get_cached_result(cache_key)
    
    @classmethod
    def set_gpt_summary(cls, place_name: str, reviews: List[str], types: List[str], summary: str) -> bool:
        """GPT 요약 결과 캐싱"""
        cache_data = {
            'place_name': place_name,
            'reviews': reviews,
            'types': types
        }
        cache_key = cls._generate_cache_key('gpt_summary', cache_data)
        
        return cls.set_cached_result(cache_key, summary, cls.CACHE_TIMEOUTS['gpt_summary'])
    
    @classmethod
    def cache_gpt_emotion_tags(cls, place_name: str, reviews: List[str], types: List[str]) -> Optional[List[str]]:
        """GPT 감정 태그 결과 캐싱"""
        cache_data = {
            'place_name': place_name,
            'reviews': reviews,
            'types': types
        }
        cache_key = cls._generate_cache_key('gpt_emotion_tags', cache_data)
        
        return cls.get_cached_result(cache_key)
    
    @classmethod
    def set_gpt_emotion_tags(cls, place_name: str, reviews: List[str], types: List[str], tags: List[str]) -> bool:
        """GPT 감정 태그 결과 캐싱"""
        cache_data = {
            'place_name': place_name,
            'reviews': reviews,
            'types': types
        }
        cache_key = cls._generate_cache_key('gpt_emotion_tags', cache_data)
        
        return cls.set_cached_result(cache_key, tags, cls.CACHE_TIMEOUTS['gpt_emotion_tags'])
    
    @classmethod
    def cache_gpt_emotion_expansion(cls, emotion_tags: List[str]) -> Optional[List[str]]:
        """GPT 감정 확장 결과 캐싱"""
        cache_data = {'emotion_tags': emotion_tags}
        cache_key = cls._generate_cache_key('gpt_emotion_expansion', cache_data)
        
        return cls.get_cached_result(cache_key)
    
    @classmethod
    def set_gpt_emotion_expansion(cls, emotion_tags: List[str], expanded_emotions: List[str]) -> bool:
        """GPT 감정 확장 결과 캐싱"""
        cache_data = {'emotion_tags': emotion_tags}
        cache_key = cls._generate_cache_key('gpt_emotion_expansion', cache_data)
        
        return cls.set_cached_result(cache_key, expanded_emotions, cls.CACHE_TIMEOUTS['gpt_emotion_expansion'])
