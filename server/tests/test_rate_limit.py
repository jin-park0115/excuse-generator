# 레이트리밋 테스트: 분당 10회, 일 200회 (PRD 섹션 7). 시간은 now 인자로 직접 넣는다.
import json

import pytest
from fastapi.testclient import TestClient

import llm
import main
from rate_limit import RateLimiter


def test_per_minute_limit_and_reset() -> None:
    rl = RateLimiter(per_minute=10, per_day=200)
    assert all(rl.allow("a", now=t) for t in range(10))  # 0~9초에 10번
    assert not rl.allow("a", now=10)  # 11번째는 거절
    assert rl.allow("b", now=10)  # 다른 IP는 따로 센다
    assert rl.allow("a", now=60)  # 첫 호출(0초)로부터 1분이 지나면 다시 허용


def test_per_day_limit() -> None:
    rl = RateLimiter(per_minute=10, per_day=200)
    # 1분에 10번씩 20분 = 200번
    assert all(rl.allow("a", now=m * 60 + s) for m in range(20) for s in range(10))
    assert not rl.allow("a", now=20 * 60)  # 하루 한도 초과
    assert rl.allow("a", now=24 * 60 * 60)  # 첫 호출로부터 24시간이 지나면 다시 허용


def test_rejected_call_is_not_counted() -> None:
    rl = RateLimiter(per_minute=1, per_day=200)
    assert rl.allow("a", now=0)
    assert not rl.allow("a", now=30)
    assert rl.allow("a", now=60)  # 30초의 거절은 기록되지 않아서 60초에 허용


def test_endpoint_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    good = json.dumps({"excuse": "버스가 늦었습니다.", "comment": "그럴 법하네요."}, ensure_ascii=False)

    async def fake(system: str, user: str) -> str:
        return good

    monkeypatch.setattr(llm, "_call_model", fake)
    monkeypatch.setattr(main, "limiter", RateLimiter(per_minute=10, per_day=200))
    client = TestClient(main.app)
    body = {"situation": "지각", "absurdity": 1}
    assert all(client.post("/api/excuse", json=body).status_code == 200 for _ in range(10))
    res = client.post("/api/excuse", json=body)
    assert res.status_code == 429
    assert res.json() == {"error": {"code": "RATE_LIMITED", "message": "핑계도 쉬어가며 만들어야 해요. 잠시 후 다시!"}}


def test_limit_uses_last_forwarded_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    # 프록시 뒤에서는 X-Forwarded-For 맨 뒤(프록시가 붙인 값)로 사용자를 구분한다. 맨 앞은 조작 가능하므로 무시
    good = json.dumps({"excuse": "버스가 늦었습니다.", "comment": "그럴 법하네요."}, ensure_ascii=False)

    async def fake(system: str, user: str) -> str:
        return good

    monkeypatch.setattr(llm, "_call_model", fake)
    monkeypatch.setattr(main, "limiter", RateLimiter(per_minute=1, per_day=200))
    client = TestClient(main.app)
    body = {"situation": "지각", "absurdity": 1}
    post = lambda xff: client.post("/api/excuse", json=body, headers={"X-Forwarded-For": xff}).status_code  # noqa: E731
    assert post("9.9.9.9, 1.1.1.1") == 200
    assert post("8.8.8.8, 1.1.1.1") == 429  # 맨 앞을 바꿔도 같은 사용자(1.1.1.1)
    assert post("9.9.9.9, 2.2.2.2") == 200  # 맨 뒤가 다르면 다른 사용자
