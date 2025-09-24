# 성능 모니터링 도구
import time
import logging
from functools import wraps
from django.core.cache import cache

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """API 호출 성능 모니터링"""
    
    @staticmethod
    def monitor_api_call(func_name: str):
        """API 호출 시간 측정 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # 성능 로그 기록
                    logger.info(f"[PERFORMANCE] {func_name}: {execution_time:.2f}초")
                    
                    # 캐시 히트율 통계 업데이트
                    PerformanceMonitor._update_cache_stats(func_name, execution_time)
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"[PERFORMANCE] {func_name} 실패: {execution_time:.2f}초 - {str(e)}")
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def _update_cache_stats(func_name: str, execution_time: float):
        """캐시 통계 업데이트"""
        try:
            stats_key = f"perf_stats:{func_name}"
            stats = cache.get(stats_key, {
                'total_calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'cache_hits': 0,
                'cache_misses': 0
            })
            
            stats['total_calls'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['total_calls']
            
            # 캐시 히트/미스 판단 (빠른 실행 = 캐시 히트로 추정)
            if execution_time < 0.1:  # 100ms 미만이면 캐시 히트로 간주
                stats['cache_hits'] += 1
            else:
                stats['cache_misses'] += 1
            
            cache.set(stats_key, stats, 86400)  # 24시간 저장
            
        except Exception as e:
            logger.error(f"캐시 통계 업데이트 실패: {e}")
    
    @staticmethod
    def get_performance_stats():
        """성능 통계 조회"""
        try:
            # 모든 성능 통계 키 조회
            cache_keys = cache._cache.keys() if hasattr(cache._cache, 'keys') else []
            perf_keys = [key for key in cache_keys if key.startswith('perf_stats:')]
            
            stats = {}
            for key in perf_keys:
                func_name = key.replace('perf_stats:', '')
                stats[func_name] = cache.get(key, {})
            
            return stats
        except Exception as e:
            logger.error(f"성능 통계 조회 실패: {e}")
            return {}
    
    @staticmethod
    def log_api_call_summary():
        """API 호출 요약 로그"""
        stats = PerformanceMonitor.get_performance_stats()
        
        logger.info("=== API 성능 요약 ===")
        for func_name, stat in stats.items():
            if stat:
                hit_rate = (stat.get('cache_hits', 0) / stat.get('total_calls', 1)) * 100
                logger.info(f"{func_name}: 평균 {stat.get('avg_time', 0):.2f}초, "
                           f"캐시 히트율 {hit_rate:.1f}%, "
                           f"총 호출 {stat.get('total_calls', 0)}회")
        logger.info("==================")

# 성능 모니터링 데코레이터들
monitor_google_api = PerformanceMonitor.monitor_api_call("Google_Maps_API")
monitor_gpt_api = PerformanceMonitor.monitor_api_call("GPT_API")
monitor_cache_hit = PerformanceMonitor.monitor_api_call("Cache_Hit")
