# 급식체 유행어 목록. 급식체일 때 서버가 요청 레벨에 맞는 항목 중 0~1개를 골라 뜻·쓰임과 함께 프롬프트에 넘긴다.
# 유행어를 추가·삭제하려면 이 파일의 SLANG 목록만 고치면 된다.
# 실존 인물·팀·집단을 가리키거나 놀리는 표현은 넣지 않는다.
from typing import NamedTuple


class Slang(NamedTuple):
    expression: str  # 표현 그대로
    meaning: str  # 뜻
    usage: str  # 어디에 어떻게 쓰는지 설명 (예시 문장을 적으면 LLM이 그대로 베끼므로 설명으로 쓴다)
    min_level: int = 1  # 쓸 수 있는 황당함 레벨 범위 (기본: 모든 레벨)
    max_level: int = 10


SLANG = [
    Slang(
        expression="엄..",
        meaning="말문이 막히거나 어이없을 때 문장 앞에 붙이는 추임새",
        usage="어이없거나 말문이 막히는 순간, 본문 문장 맨 앞에 추임새로 붙임",
    ),
    Slang(
        expression="줴줴이야~",
        meaning='GG를 찰지게 외치는 말. "끝났다, 망했다"는 뜻',
        usage="신뢰도가 낮을 때 코멘트 끝에 붙임",
        min_level=9,  # "망했다"는 뜻이라 신뢰도가 낮은 레벨 9~10에서만
        max_level=10,
    ),
]

SLANG_RATE = 0.5  # 급식체 요청 중 유행어를 넣는 비율. 목록 길이와 상관없이 일정하게 유지한다
