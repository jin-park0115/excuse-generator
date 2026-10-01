# 급식체 유행어 목록. 급식체일 때 서버가 여기서 0~1개를 골라 뜻·쓰임과 함께 프롬프트에 넘긴다.
# 유행어를 추가·삭제하려면 이 파일의 SLANG 목록만 고치면 된다.
# 실존 인물·팀·집단을 가리키거나 놀리는 표현은 넣지 않는다.
from typing import NamedTuple


class Slang(NamedTuple):
    expression: str  # 표현 그대로
    meaning: str  # 뜻
    usage: str  # 어울리는 쓰임 예시


SLANG = [
    Slang(
        expression="엄..",
        meaning="말문이 막히거나 어이없을 때 문장 앞에 붙이는 추임새",
        usage="엄.. 나도 내가 왜 늦었는지 모르겠음",
    ),
    Slang(
        expression="줴줴이야~",
        meaning='GG를 찰지게 외치는 말. "끝났다, 망했다"는 뜻',
        usage="신뢰도가 낮을 때 코멘트에: 이 핑계는 줴줴이야~",
    ),
]

SLANG_RATE = 0.5  # 급식체 요청 중 유행어를 넣는 비율. 목록 길이와 상관없이 일정하게 유지한다
