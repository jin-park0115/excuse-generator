# CORS 테스트: ALLOWED_ORIGINS에 넣은 웹 주소만 브라우저 호출을 허용한다 (PRD 섹션 7, M7-4).
import importlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import main

WEB = "https://excuse-generator-app.vercel.app"


@pytest.fixture
def restricted_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # CORS 설정은 import 때 읽으므로 환경변수를 바꾼 뒤 main을 다시 불러온다
    monkeypatch.setenv("ALLOWED_ORIGINS", WEB)
    yield TestClient(importlib.reload(main).app)
    monkeypatch.delenv("ALLOWED_ORIGINS")
    importlib.reload(main)  # 다른 테스트를 위해 원래(전체 허용)로 되돌린다


def preflight(client: TestClient, origin: str):
    return client.options(
        "/api/excuse",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
    )


def test_allowed_web_origin(restricted_app: TestClient) -> None:
    res = preflight(restricted_app, WEB)
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == WEB


def test_other_origin_blocked(restricted_app: TestClient) -> None:
    res = preflight(restricted_app, "https://evil.example.com")
    assert res.status_code == 400
    assert "access-control-allow-origin" not in res.headers


def test_no_origin_like_native_app_still_works(restricted_app: TestClient) -> None:
    # Expo 앱(네이티브)은 Origin 헤더를 보내지 않아 CORS와 상관없이 호출된다
    assert restricted_app.get("/health").status_code == 200


def test_default_allows_all() -> None:
    res = preflight(TestClient(main.app), "https://anything.example.com")
    assert res.headers["access-control-allow-origin"] == "*"
