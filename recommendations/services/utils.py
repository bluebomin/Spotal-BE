# 동네 태그 등 공통 함수

import re

def extract_neighborhood(address: str) -> str:
    """
    주소 문자열에서 '동' 단위까지만 추출
    - '청파동1가' → '청파동'
    - '이태원동,' → '이태원동'
    - 못 찾으면 '용산구' 다음 단어 반환
    """
    if not address:
        return ""

    parts = address.split()

    # 뒤에서부터 검사
    for p in reversed(parts):
        # 불필요한 특수문자 제거
        token = re.sub(r"[^가-힣0-9]", "", p)

        if token.endswith("동") or token.endswith("가") or token.endswith("촌"):
            # "청파동1가" → "청파동" 으로 정규화
            if "동" in token:
                return token.split("동")[0] + "동"
            return token

    # 못 찾으면 '용산구' 다음 단어 사용
    if "용산구" in parts:
        idx = parts.index("용산구")
        if idx + 1 < len(parts):
            token = re.sub(r"[^가-힣0-9]", "", parts[idx + 1])
            if "동" in token:
                return token.split("동")[0] + "동"
            return token

    return parts[-1].strip(",")
