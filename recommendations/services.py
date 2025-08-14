from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def call_gpt_api(prompt, model="gpt-3.5-turbo"):
    """
    GPT API를 호출하는 함수
    
    Args:
        prompt (str): GPT에게 보낼 프롬프트
        model (str): 사용할 GPT 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        str: GPT 응답 텍스트
        None: 에러 발생 시
    """
    try:
        logger.info(f"GPT API 호출 시작: 모델={model}, 프롬프트 길이={len(prompt)}")
        
        # OpenAI 클라이언트 생성
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI 클라이언트 생성 성공")
        
        # GPT API 호출 (새로운 문법)
        logger.info("GPT API 호출 중...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # 응답 최대 길이 제한
            temperature=0.7  # 창의성 조절 (0.0: 보수적, 1.0: 창의적)
        )
        logger.info("GPT API 호출 성공")
        
        # 응답 추출 (새로운 문법)
        gpt_response = response.choices[0].message.content
        logger.info(f"GPT 응답 추출 성공: {len(gpt_response)}자")
        
        return gpt_response
        
    except Exception as e:
        logger.error(f"GPT API 호출 실패: {type(e).__name__}: {e}")
        return None

def get_store_recommendation(closed_store_info, nearby_stores):
    """
    폐업한 가게와 유사한 가게 추천
    
    Args:
        closed_store_info (str): 폐업한 가게 정보 (키워드, 특징 등)
        nearby_stores (list): 주변 가게 목록
    
    Returns:
        str: 추천 가게 정보
    """
    prompt = f"""
    다음 폐업한 가게와 유사한 분위기나 특징을 가진 가게를 추천해주세요.
    
    폐업한 가게 정보: {closed_store_info}
    
    주변 가게들: {', '.join(nearby_stores)}
    
    위 가게들 중에서 폐업한 가게와 가장 유사한 가게 3개를 추천하고, 
    각각의 추천 이유를 간단히 설명해주세요.
    
    응답 형식:
    - 추천 가게1: [가게명] - [추천 이유]
    - 추천 가게2: [가게명] - [추천 이유]
    - 추천 가게3: [가게명] - [추천 이유]
    """
    
    return call_gpt_api(prompt)
