# /api/excuse 테스트. 실제 LLM은 부르지 않고 llm._call_model을 가짜 함수로 바꿔서 확인한다.
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import llm
from main import app

client = TestClient(app)
VALID = {"situation": "지각", "absurdity": 7, "tone": "사극체", "previous_excuse": None}
GOOD = json.dumps({"excuse": "소인, 학이 길을 막아…", "comment": "학이 나오는 순간 끝."}, ensure_ascii=False)


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
    body = res.json()
    assert body["excuse"] == "소인, 학이 길을 막아…" and body["comment"] == "학이 나오는 순간 끝."
    assert 5 <= body["credibility"] <= 30  # 레벨 7 범위


def test_tone_default_and_code_fence_and_server_credibility(monkeypatch: pytest.MonkeyPatch) -> None:
    # LLM이 credibility를 보내도 무시하고, 서버가 뽑아 프롬프트에 넘긴 값을 그대로 쓴다
    fenced = '```json\n{"excuse": "평행우주의 제가…", "credibility": 150, "comment": "우주적"}\n```'
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(fenced, calls=calls))
    res = client.post("/api/excuse", json={"situation": "지각", "absurdity": 10})
    assert res.status_code == 200
    cred = res.json()["credibility"]
    assert 0 <= cred <= 5
    assert f"신뢰도: {cred}" in calls[0]
    assert "말투: 공손한 직장인체" in calls[0]


@pytest.mark.parametrize("level,low,high", [(1, 70, 95), (3, 70, 95), (4, 30, 70), (6, 30, 70), (7, 5, 30), (9, 5, 30), (10, 0, 5)])
def test_credibility_range_per_level(level: int, low: int, high: int) -> None:
    values = {llm.pick_credibility(level) for _ in range(500)}
    assert min(values) >= low and max(values) <= high
    assert len(values) > 1  # 매번 같은 값이 아니라 랜덤


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
    assert calls[0] == calls[1]  # 재시도 때도 같은 신뢰도를 넘긴다


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


def test_cosmic_topic_only_for_level_10() -> None:
    topics = {llm.pick_cosmic_topic(10) for _ in range(500)}
    assert topics <= set(llm.COSMIC_TOPICS)
    assert len(topics) > 1  # 매번 같은 소재가 아니라 랜덤
    assert all(llm.pick_cosmic_topic(level) is None for level in range(1, 10))


def test_cosmic_topic_in_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(GOOD, GOOD, calls=calls))
    client.post("/api/excuse", json={**VALID, "absurdity": 10})
    client.post("/api/excuse", json={**VALID, "absurdity": 9})
    assert any(f"소재: {t}" in calls[0] for t in llm.COSMIC_TOPICS)
    assert "소재:" not in calls[1]


@pytest.mark.parametrize(
    "tone,bad",
    [
        ("사극체", {"excuse": "소인, 늦었사옵니다.", "comment": "신뢰도 3점답게 아무도 안 믿소."}),  # 코멘트에 점수
        ("사극체", {"excuse": "소인, 늦었사옵니다.", "comment": "40점짜리 핑계이옵니다."}),
        ("공손한 직장인체", {"excuse": "버스가 늦게 와서 늦었사옵니다.", "comment": "평범하네요."}),  # 말투 섞임
        ("공손한 직장인체", {"excuse": "버스가 늦게 왔습니다.", "comment": "소인도 믿겠습니다."}),
        ("공손한 직장인체", {"excuse": "부득이한 조치였사오니 양해 바랍니다.", "comment": "평범하네요."}),
        ("사극체", {"excuse": "소인, 세종대왕을 뵙고 왔사옵니다.", "comment": "허황되옵니다."}),  # 실존 인물
    ],
)
def test_rule_violation_is_retried(monkeypatch: pytest.MonkeyPatch, tone: str, bad: dict[str, str]) -> None:
    excuse = "소인, 버스가 늦었사옵니다." if tone == "사극체" else "버스가 늦게 왔습니다."
    good = json.dumps({"excuse": excuse, "comment": "그럴 법하네요."}, ensure_ascii=False)
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(json.dumps(bad, ensure_ascii=False), good, calls=calls))
    res = client.post("/api/excuse", json={**VALID, "tone": tone})
    assert res.status_code == 200
    assert len(calls) == 2  # 규칙 위반이라 재시도했다
    assert res.json()["comment"] == "그럴 법하네요."
