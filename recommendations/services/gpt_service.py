# GPT 요약

from .gpt_client import client

def generate_summary(place):
    """
    GPT API로 가게 한줄 요약 생성
    """
    prompt = f"""
    아래는 가게 정보입니다:
    이름: {place['name']}
    주소: {place['address']}
    
    이 가게의 특징을 리뷰 기반으로 상상하여, 
    간결하고 매력적인 한줄 요약을 작성해 주세요.
조건:
- 주소는 반드시 한국어로 표현할 것
- 간결하고 매력적인 한 줄 요약을 작성할 것

결과는 한글로만 작성해 주세요.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=50
    )

    return completion.choices[0].message.content.strip()
