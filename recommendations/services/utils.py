# 동네 태그 등 공통 함수

def extract_neighborhood(address: str) -> str:
    """
    주소에서 동네 태그 추출
    ex) '서울특별시 용산구 청파동 12-34, South Korea' → '청파동'
    """
    if not address:
        return ""

    parts = address.split()

    # 뒤에서부터 검사하면서 '동', '가', '촌'으로 끝나는 단어 찾기
    for p in reversed(parts):
        if p.endswith(("동", "가", "촌")):
            return p

    # 못 찾으면 '용산구' 다음 단어를 기본값으로
    if "용산구" in parts:
        idx = parts.index("용산구")
        if idx + 1 < len(parts):
            return parts[idx + 1]

    return parts[-1]  # fallback