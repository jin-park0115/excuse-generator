# /api/excuse 테스트. 실제 LLM은 부르지 않고 llm._call_model을 가짜 함수로 바꿔서 확인한다.
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import llm
from main import app

client = TestClient(app)
VALID = {"situation": "지각", "absurdity": 7, "tone": "사극체", "previous_excuse": None}
GOOD = json.dumps({"excuse": "소인, 학이 길을 막아…", "credibility": 12, "comment": "학이 나오는 순간 끝."}, ensure_ascii=False)


def fake_model(*responses: str, calls: list[str] | None = None):
    """주어진 응답을 차례로 돌려주는 가짜 LLM. 문자열 대신 예외를 넣으면 그 예외를 던진다."""
    queue = list(responses)

    async def _fake(system: str, user: str) -> str:
        if calls is not None:
            calls.append(user)
        r = queue.pop(0)
        if isinstance(r, BaseException):
            raise r
        return r

    return _fake


def test_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_call_model", fake_model(GOOD))
    res = client.post("/api/excuse", json=VALID)
    assert res.status_code == 200
    assert res.json() == json.loads(GOOD)


def test_tone_defaults_and_code_fence_and_clamp(monkeypatch: pytest.MonkeyPatch) -> None:
    fenced = '```json\n{"excuse": "평행우주의 제가…", "credibility": 150, "comment": "우주적"}\n```'
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(fenced, calls=calls))
    res = client.post("/api/excuse", json={"situation": "지각", "absurdity": 10})
    assert res.status_code == 200
    assert res.json()["credibility"] == 100
    assert "말투: 공손한 직장인체" in calls[0]


def test_previous_excuse_adds_instruction(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(GOOD, calls=calls))
    client.post("/api/excuse", json={**VALID, "previous_excuse": "비둘기가 막았다"})
    assert "완전히 다른 것" in calls[0] and "비둘기가 막았다" in calls[0]


def test_retry_once_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model("JSON 아님", GOOD, calls=calls))
    res = client.post("/api/excuse", json=VALID)
    assert res.status_code == 200
    assert len(calls) == 2


@pytest.mark.parametrize(
    "first,second",
    [
        ("JSON 아님", "여전히 아님"),
        (GOOD.replace("소인", "가" * 300), "{}"),  # 200자 초과, 필드 없음
        (RuntimeError("503"), RuntimeError("503")),  # API 오류
    ],
)
def test_llm_error_after_retry(monkeypatch: pytest.MonkeyPatch, first: object, second: object) -> None:
    monkeypatch.setattr(llm, "_call_model", fake_model(first, second))  # type: ignore[arg-type]
    res = client.post("/api/excuse", json=VALID)
    assert res.status_code == 502
    assert res.json() == {"error": {"code": "LLM_ERROR", "message": "핑계 공장이 잠깐 멈췄어요"}}


def test_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    async def slow(system: str, user: str) -> str:
        await asyncio.sleep(1)
        return GOOD

    monkeypatch.setattr(llm, "_call_model", slow)
    monkeypatch.setattr(llm, "TIMEOUT_SECONDS", 0.05)
    res = client.post("/api/excuse", json=VALID)
    assert res.status_code == 504
    assert res.json()["error"]["code"] == "LLM_TIMEOUT"


@pytest.mark.parametrize(
    "patch",
    [
        {"situation": ""},
        {"situation": "   "},
        {"situation": "가" * 51},
        {"absurdity": 0},
        {"absurdity": 11},
        {"tone": "랩퍼체"},
        {"previous_excuse": "가" * 301},
    ],
)
def test_invalid_input(patch: dict[str, object]) -> None:
    res = client.post("/api/excuse", json={**VALID, **patch})
    assert res.status_code == 422
    assert res.json() == {"error": {"code": "INVALID_INPUT", "message": "입력을 다시 확인해주세요"}}


def test_missing_field() -> None:
    res = client.post("/api/excuse", json={"situation": "지각"})
    assert res.status_code == 422
