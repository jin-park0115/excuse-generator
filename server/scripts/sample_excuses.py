# 프롬프트 품질 확인용 스크립트. 상황 3개 × 레벨 1·5·10 × 말투 2개 = 18개를 실제 Gemini로 생성해 출력한다.
# 실행: server 폴더에서 `python -m scripts.sample_excuses`
import asyncio

import llm
from schemas import ExcuseRequest

SITUATIONS = ["지각", "약속 취소", "과제 미제출"]
LEVELS = [1, 5, 10]
TONES = ["공손한 직장인체", "사극체"]
DELAY_SECONDS = 4  # ponytail: Gemini 무료 티어 분당 호출 한도(429) 회피용, 유료 키면 0으로


async def main() -> None:
    n = 0
    for situation in SITUATIONS:
        for level in LEVELS:
            for tone in TONES:
                n += 1
                req = ExcuseRequest(situation=situation, absurdity=level, tone=tone)  # type: ignore[arg-type]
                try:
                    r = await llm.generate_excuse(req)
                    print(f"[{n:2}] {situation} / 레벨 {level} / {tone}  (신뢰도 {r.credibility})")
                    print(f"     {r.excuse}")
                    print(f"     → {r.comment}\n")
                except (llm.LLMError, llm.LLMTimeout) as e:
                    print(f"[{n:2}] {situation} / 레벨 {level} / {tone}  실패: {type(e).__name__} {e.__cause__}\n")
                await asyncio.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
