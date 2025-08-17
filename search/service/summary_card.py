from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_summary_card(details, reviews):
    prompt = f"""
    아래는 '{details.get("name")}' 가게의 실제 구글맵 리뷰 일부입니다:

    {reviews[:5]}

    위 리뷰들을 바탕으로 사용자에게 보여줄 요약카드를 작성해줘.

    조건:
    - 1문장, 간결하게
    - 리뷰 내용을 반영해 가게의 특징·분위기를 설명
    - 없는 사실은 절대 추가하지 마
    - 가게 위치, 영업시간, 전화번호는 언급하지 마
    - 예시: "55년 넘게 연탄불 납작 불고기로 사랑받은 용산의 명소"
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # 사실 기반
    )

    return response.choices[0].message.content.strip()


# 감정태그생성
def generate_emotion_tags(details, reviews):
    prompt = f"""
    아래는 '{details.get("name")}' 가게의 실제 구글맵 리뷰 일부입니다:

    {reviews[:5]}
    
    구글 맵 바탕으로 감정 태그를 생성해줘.
    감정 태그의 종류는 다음과 같아:
    - 정겨움
    - 편안함
    - 조용함
    - 활기참
    - 소박함
    - 세심함 
    
    감정 태그는 2-3개 정도로 작성해줘.
    가장 유사해 보이는 태그 상위순서대로 작성해줘.
    예시 : 정겨움, 편안함
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip().split(', ')
