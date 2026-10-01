# /health 엔드포인트가 살아 있는지 확인하는 테스트.
from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    res = TestClient(app).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
