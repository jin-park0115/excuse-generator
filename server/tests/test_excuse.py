# /api/excuse 테스트. 실제 LLM은 부르지 않고 llm._call_model을 가짜 함수로 바꿔서 확인한다.
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import llm
import main
from main import app
from rate_limit import RateLimiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트마다 레이트리밋을 새로 만들어 앞 테스트의 호출 수가 영향을 주지 않게 한다."""
    monkeypatch.setattr(main, "limiter", RateLimiter())
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


@pytest.mark.parametrize(
    "levels,pool",
    [
        ((1, 2, 3), llm.REALISTIC_TOPICS),
        ((4, 5, 6), llm.SUSPICIOUS_TOPICS),
        ((7, 8, 9), llm.ABSURD_TOPICS),
        ((10,), llm.COSMIC_TOPICS),
    ],
)
def test_topic_pool_per_level(levels: tuple[int, ...], pool: list[str]) -> None:
    for level in levels:
        topics = {llm.pick_topic(level) for _ in range(500)}
        assert topics <= set(pool)
        assert len(topics) > len(pool) // 2  # 한 소재에 쏠리지 않고 여러 소재가 나온다


def test_topic_pools_respect_level_rules() -> None:
    # 4~9는 과장되므로 컨디션 소재를 쓰지 않는다 (병명·응급실로 번지는 것 방지)
    assert not any("컨디션" in t for t in llm.SUSPICIOUS_TOPICS + llm.ABSURD_TOPICS)
    # 동물은 7~9에만
    assert "동물" not in llm.REALISTIC_TOPICS + llm.SUSPICIOUS_TOPICS
    assert "동물" in llm.ABSURD_TOPICS


def test_every_level_gets_topic_in_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(*[GOOD] * 10, calls=calls))
    for level in range(1, 11):
        client.post("/api/excuse", json={**VALID, "absurdity": level})
    for level, prompt in zip(range(1, 11), calls):
        assert any(f"소재: {t}" in prompt for t in llm.topic_pool(level)), level


def test_prompt_has_no_specific_example_scenes() -> None:
    # 프롬프트 예시를 LLM이 그대로 따라 하지 않도록 특정 장면 예시를 두지 않는다
    for scene in ["15분", "동전 87개", "손자 자랑", "다람쥐", "비둘기", "무지개색"]:
        assert scene not in llm.SYSTEM_PROMPT, scene


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


def test_exaggeration_only_for_levels_7_to_9() -> None:
    for level in (7, 8, 9):
        picked = {llm.pick_exaggeration(level) for _ in range(500)}
        assert picked == set(llm.EXAGGERATIONS)  # 후보가 모두 고르게 나온다
    assert all(llm.pick_exaggeration(level) is None for level in (1, 2, 3, 4, 5, 6, 10))


def test_exaggeration_in_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model(GOOD, GOOD, calls=calls))
    client.post("/api/excuse", json={**VALID, "absurdity": 8})
    client.post("/api/excuse", json={**VALID, "absurdity": 5})
    assert any(f"과장 방법: {e}" in calls[0] for e in llm.EXAGGERATIONS)
    assert "과장 방법:" not in calls[1]


def test_retry_keeps_same_topic_and_exaggeration(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(llm, "_call_model", fake_model("JSON 아님", GOOD, calls=calls))
    client.post("/api/excuse", json={**VALID, "absurdity": 8})
    assert len(calls) == 2 and calls[0] == calls[1]


def test_prompt_has_level_7_to_9_bar() -> None:
    assert "레벨 4~6보다 확실히 황당" in llm.SYSTEM_PROMPT
    assert "웃음이 터질" in llm.SYSTEM_PROMPT


def test_level_7_to_9_forbids_level_10_moves() -> None:
    assert "저절로 생기거나 늘어나는 것" in llm.SYSTEM_PROMPT
    assert "기계가 스스로 의지를 갖는 것" in llm.SYSTEM_PROMPT
    assert any("원래 있던 사람·물건" in e for e in llm.EXAGGERATIONS)


def test_slang_only_for_geupsik() -> None:
    for tone in ["공손한 직장인체", "사극체", "뉴스 앵커체", "발표자(학회)체"]:
        assert all(llm.pick_slang(tone, 10) is None for _ in range(200))
    picks = [llm.pick_slang("급식체", 10) for _ in range(2000)]
    assert None in picks  # 0개인 경우도 있다
    assert {p for p in picks if p} == set(llm.SLANG)  # 레벨 10에서는 목록의 유행어가 모두 나온다
    rate = sum(p is not None for p in picks) / len(picks)
    assert abs(rate - llm.SLANG_RATE) < 0.05


def test_slang_entries_complete() -> None:
    assert llm.SLANG
    for s in llm.SLANG:
        assert s.expression and s.meaning and s.usage


def test_slang_in_prompt_with_meaning(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    ok = json.dumps({"excuse": "엄.. 버스 놓쳤음", "comment": "그럴 수 있지"}, ensure_ascii=False)  # 급식체 응답
    monkeypatch.setattr(llm, "_call_model", fake_model(ok, ok, calls=calls))
    slang = llm.SLANG[0]
    monkeypatch.setattr(llm, "pick_slang", lambda tone, level: slang)
    client.post("/api/excuse", json={**VALID, "tone": "급식체"})
    monkeypatch.setattr(llm, "pick_slang", lambda tone, level: None)
    client.post("/api/excuse", json={**VALID, "tone": "급식체"})
    assert f'유행어: "{slang.expression}"' in calls[0] and slang.meaning in calls[0]
    assert len(calls) == 2  # 재시도 없이 요청 2번
    assert "유행어:" not in calls[1]  # 고른 게 없으면 넣지 않는다


def test_slang_keeps_safety_rule() -> None:
    assert "유행어를 쓰더라도 실존 인물·팀·집단을 언급하거나 놀리지 않는다" in llm.SYSTEM_PROMPT


def test_slang_level_range() -> None:
    by_expr = {s.expression: s for s in llm.SLANG}
    assert (by_expr["줴줴이야~"].min_level, by_expr["줴줴이야~"].max_level) == (9, 10)
    assert (by_expr["엄.."].min_level, by_expr["엄.."].max_level) == (1, 10)
    for level in range(1, 11):
        picked = {llm.pick_slang("급식체", level) for _ in range(500)} - {None}
        allowed = {s for s in llm.SLANG if s.min_level <= level <= s.max_level}
        assert picked == allowed, level  # 레벨 범위 밖의 유행어는 절대 나오지 않는다


def test_no_slang_when_no_candidate_for_level(monkeypatch: pytest.MonkeyPatch) -> None:
    only_high = [llm.Slang("줴줴이야~", "망했다", "이 핑계는 줴줴이야~", min_level=9, max_level=10)]
    monkeypatch.setattr(llm, "SLANG", only_high)
    monkeypatch.setattr(llm, "SLANG_RATE", 1.0)  # 확률 때문이 아니라 후보가 없어서 None인지 확인
    assert all(llm.pick_slang("급식체", level) is None for level in range(1, 9))
    assert llm.pick_slang("급식체", 9) == only_high[0]


def test_borderline_slang_in_profanity_rule() -> None:
    for word in ["개노잼", "개레전드", "이딴"]:
        assert word in llm.SYSTEM_PROMPT, word
