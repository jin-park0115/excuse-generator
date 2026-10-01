# Gemini 호출, 응답 JSON 파싱, 1회 재시도를 담당한다. API 키는 환경변수 GEMINI_API_KEY로만 읽는다.
import asyncio
import json
import os
import random
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import ABSURD_TOPICS, COSMIC_TOPICS, EXAGGERATIONS, REALISTIC_TOPICS, SUSPICIOUS_TOPICS, SYSTEM_PROMPT, build_user_prompt
from schemas import ExcuseRequest, ExcuseResponse
from slang import SLANG, SLANG_RATE, Slang

load_dotenv(Path(__file__).parent / ".env")

# 모델이 과부하(503)일 때는 .env에서 GEMINI_MODEL로 바꿀 수 있다
MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"
TIMEOUT_SECONDS = 15

# 프롬프트만으로는 가끔 새는 규칙을 서버에서 한 번 더 검사한다. 걸리면 파싱 실패처럼 1회 재시도.
SCORE_IN_COMMENT = re.compile(r"\d|점짜리|신뢰도|퍼센트|%")
SAGEUK_WORDS = re.compile(r"사옵|사오|옵니다|옵소서|이옵|하오|소인")  # ponytail: 대표 사극 어미만, 새는 패턴 발견 시 추가
# ponytail: 샘플에서 실제로 나온 실존 인물 위주의 짧은 목록. 전부 막을 수는 없으니 새로 나오면 추가
# 비속어 중 평범한 단어와 헷갈리지 않는 것만 검사한다 ("개-" 접두어는 개찰구·개구리 등과 구분이 안 돼 프롬프트 규칙만 둠)
PROFANITY = re.compile(r"이딴")
REAL_PEOPLE = re.compile(r"세종|이순신|광종|태조|정조|영조|장영실|신사임당|아인슈타인|뉴턴|에디슨|나폴레옹|셰익스피어")


class LLMError(Exception):
    """LLM 호출 실패 또는 응답 파싱 실패 (재시도 후)."""


class RuleViolation(ValueError):
    """응답이 서버 검사 규칙을 어김. 메시지는 재시도 프롬프트에 그대로 붙여 LLM에게 무엇을 고칠지 알려준다."""


class LLMTimeout(Exception):
    """LLM 응답이 15초를 넘김."""


_client: genai.Client | None = None


async def _call_model(system: str, user: str) -> str:
    """Gemini에 프롬프트를 보내고 응답 텍스트를 돌려준다. 테스트에서는 이 함수를 가짜로 바꾼다."""
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY 환경변수가 없습니다 (server/.env 확인)")
        _client = genai.Client(api_key=key)
    res = await _client.aio.models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=1.0,
            response_mime_type="application/json",
            # 도구(함수)를 쓰지 않으므로 자동 함수 호출(AFC)을 꺼서 SDK 경고도 없앤다
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return res.text or ""


def credibility_range(absurdity: int) -> tuple[int, int]:
    """레벨별 신뢰도 범위 (PRD 섹션 6 표)."""
    if absurdity <= 3:
        return (70, 95)
    if absurdity <= 6:
        return (30, 70)
    if absurdity <= 9:
        return (5, 30)
    return (0, 5)


def pick_credibility(absurdity: int) -> int:
    """신뢰도는 LLM이 아니라 서버가 레벨별 범위 안에서 랜덤 정수로 뽑는다."""
    return random.randint(*credibility_range(absurdity))


def topic_pool(absurdity: int) -> list[str]:
    """레벨 구간별 소재 후보 목록 (prompts.py)."""
    if absurdity <= 3:
        return REALISTIC_TOPICS
    if absurdity <= 6:
        return SUSPICIOUS_TOPICS
    if absurdity <= 9:
        return ABSURD_TOPICS
    return COSMIC_TOPICS


def pick_topic(absurdity: int) -> str:
    """레벨에 맞는 소재 후보 중 하나를 랜덤으로 고른다 (LLM이 프롬프트 예시만 따라 하는 쏠림 방지)."""
    return random.choice(topic_pool(absurdity))


def pick_exaggeration(absurdity: int) -> str | None:
    """레벨 7~9일 때만 과장 방법 하나를 랜덤으로 고른다. 다른 레벨은 None."""
    return random.choice(EXAGGERATIONS) if 7 <= absurdity <= 9 else None


def pick_slang(tone: str, absurdity: int) -> Slang | None:
    """급식체일 때만, 이 레벨에서 쓸 수 있는 유행어 중 하나를 SLANG_RATE 확률로 고른다 (slang.py). 없으면 None."""
    candidates = [s for s in SLANG if s.min_level <= absurdity <= s.max_level]
    if tone != "급식체" or not candidates or random.random() >= SLANG_RATE:
        return None
    return random.choice(candidates)


def parse_response(text: str, credibility: int, tone: str) -> ExcuseResponse:
    """코드펜스(```)를 지우고 JSON을 읽는다. credibility는 LLM 값 대신 서버가 뽑은 값을 쓴다.
    코멘트에 점수 숫자가 있거나, 사극체가 아닌데 사극 어미가 섞이거나, 실존 인물이나 비속어("이딴")가 나오면 RuleViolation (재시도 대상)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    data = json.loads(text)
    data["credibility"] = credibility
    res = ExcuseResponse.model_validate(data)
    if SCORE_IN_COMMENT.search(res.comment):
        raise RuleViolation("코멘트에 숫자나 점수 표현을 썼다. 점수는 말하지 말고 느낌만 표현한다")
    if tone != "사극체" and SAGEUK_WORDS.search(res.excuse + res.comment):
        raise RuleViolation(f"{tone}인데 사극 어미가 섞였다. 끝까지 {tone}만 쓴다")
    if REAL_PEOPLE.search(res.excuse + res.comment):
        raise RuleViolation("실존 인물 이름을 썼다. 실존 인물은 등장시키지 않는다")
    if PROFANITY.search(res.excuse + res.comment):
        raise RuleViolation('"이딴" 같은 비속어를 썼다. 비속어 없이 재치 있게 쓴다')
    return res


async def _generate_with_retry(req: ExcuseRequest) -> ExcuseResponse:
    credibility = pick_credibility(req.absurdity)  # 재시도해도 같은 점수·소재·과장 방법·유행어를 쓴다
    user = build_user_prompt(
        req, credibility, pick_topic(req.absurdity), pick_exaggeration(req.absurdity), pick_slang(req.tone, req.absurdity)
    )
    for attempt in range(2):  # 처음 1번 + 재시도 1번
        try:
            return parse_response(await _call_model(SYSTEM_PROMPT, user), credibility, req.tone)
        except LLMError:
            raise  # 키 없음 등 설정 문제는 재시도해도 소용없다
        except Exception as e:  # API 오류(503 등), JSON 파싱·검증 실패 모두 1회 재시도
            if attempt == 1:
                raise LLMError(type(e).__name__) from e
            if isinstance(e, RuleViolation):
                # 같은 프롬프트로 다시 보내면 같은 실수를 반복하기 쉬워서, 무엇을 어겼는지 알려준다
                user += f"\n[다시 쓰기] 직전 답이 규칙을 어겼다: {e}. 이 점을 고쳐 처음부터 새로 써라."
    raise AssertionError("unreachable")


async def generate_excuse(req: ExcuseRequest) -> ExcuseResponse:
    """핑계를 만든다. 재시도까지 포함해 15초를 넘기면 LLMTimeout."""
    try:
        return await asyncio.wait_for(_generate_with_retry(req), TIMEOUT_SECONDS)
    except asyncio.TimeoutError as e:
        raise LLMTimeout() from e
