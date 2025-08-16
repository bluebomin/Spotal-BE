from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_summary_card(store):
    prompt = f"""
    다음은 용산구 음식점/카페 데이터입니다.
    이 정보를 기반으로 사용자에게 보여줄 요약카드를 만들어줘.
    불필요한 값은 빼고, 핵심적인 정보만 간단히 설명해.
    예시는 "55년이 넘는 세월 동안 연탄불에 구운 납작 불고기로 사랑받았던 용산의 명소."
    이런 식이야.
    제공되는 데이터를 보고 웹서칭을 통해서 사실을 기반으로 만들어줘.
    사람들의 감성적인 리뷰를 바탕으로 적어줘.
    네이버리뷰나 구글리뷰, 블로그, 인스타그램 등을 참고해줘.
    어디에 위치해있고 영업을 하고 있는 지는 중요하지 않아. 
    그 가게에 대해 사람들이 어떤 감정을 느끼는지, 어떤 특징이 있는지에 대해 작성해줘.
    요약 카드는 길지 않게, 1문장으로 간결하게 작성해줘.
    사실에 기반해서 작성해야해. 
    예시로 알려준 거 그대로 사용하지 말고 진짜 그 식당에 대한 정보를 바탕으로 작성해줘.

    제공되는 데이터는 다음과 같아:

    데이터:
    이름: {store.get("BPLCNM")}
    영업상태: {store.get("TRDSTATENM")}
    지번주소: {store.get("SITEWHLADDR")}
    도로명주소: {store.get("RDNWHLADDR")}
    인허가일자: {store.get("APVPERMYMD")}
    업종명: {store.get("UPTAENM")}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# 감정태그생성
def generate_emotion_tags(store):
    prompt = f"""
    용산구 요약 카드를 만들면서 본 네이버리뷰나 구글리뷰, 블로그, 인스타그램 등의 리뷰를 바탕으로
    감정 태그를 생성해줘.
    감정 태그의 종류는 다음과 같아:
    - 정겨움
    - 편안함
    - 조용함
    - 활기참
    - 소박함
    - 세심함 
    
    감정 태그는 1-3개 정도로 작성해줘.
    가장 유사해 보이는 태그 상위순서대로 작성해줘.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip().split(', ')
