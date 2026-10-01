# Gemini 호출, 응답 JSON 파싱, 1회 재시도를 담당한다. API 키는 환경변수 GEMINI_API_KEY로만 읽는다.
import asyncio
import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT, build_user_prompt
from schemas import ExcuseRequest, ExcuseResponse

load_dotenv(Path(__file__).parent / ".env")

# 모델이 과부하(503)일 때는 .env에서 GEMINI_MODEL로 바꿀 수 있다
MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"
TIMEOUT_SECONDS = 15


class LLMError(Exception):
    """LLM 호출 실패 또는 응답 파싱 실패 (재시도 후)."""


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


def parse_response(text: str, credibility: int) -> ExcuseResponse:
    """코드펜스(```)를 지우고 JSON을 읽는다. credibility는 LLM 값 대신 서버가 뽑은 값을 쓴다."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    data = json.loads(text)
    data["credibility"] = credibility
    return ExcuseResponse.model_validate(data)


async def _generate_with_retry(req: ExcuseRequest) -> ExcuseResponse:
    credibility = pick_credibility(req.absurdity)  # 재시도해도 같은 점수를 쓴다
    user = build_user_prompt(req, credibility)
    for attempt in range(2):  # 처음 1번 + 재시도 1번
        try:
            return parse_response(await _call_model(SYSTEM_PROMPT, user), credibility)
        except LLMError:
            raise  # 키 없음 등 설정 문제는 재시도해도 소용없다
        except Exception as e:  # API 오류(503 등), JSON 파싱·검증 실패 모두 1회 재시도
            if attempt == 1:
                raise LLMError(type(e).__name__) from e
    raise AssertionError("unreachable")


async def generate_excuse(req: ExcuseRequest) -> ExcuseResponse:
    """핑계를 만든다. 재시도까지 포함해 15초를 넘기면 LLMTimeout."""
    try:
        return await asyncio.wait_for(_generate_with_retry(req), TIMEOUT_SECONDS)
    except asyncio.TimeoutError as e:
        raise LLMTimeout() from e
