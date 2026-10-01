# FastAPI 서버 진입점. 앱의 요청을 받아 LLM 핑계를 돌려준다.
import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import llm
from rate_limit import RateLimiter
from schemas import ExcuseRequest, ExcuseResponse

# 로그에는 시간·레벨·말투·응답 시간·에러 코드만 남긴다 (사용자 입력 텍스트·API 키는 남기지 않음)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("excuse")

app = FastAPI(title="핑계 생성기 API")

# 개발 중에는 전체 허용. 배포할 때는 ALLOWED_ORIGINS="https://a.com,https://b.com"처럼 제한한다
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in (os.getenv("ALLOWED_ORIGINS") or "*").split(",")],  # .env는 llm.py import 때 읽힌다
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

limiter = RateLimiter(per_minute=10, per_day=200)


def client_ip(request: Request) -> str:
    """레이트리밋용 클라이언트 IP. Render 같은 프록시 뒤에서는 X-Forwarded-For의 맨 뒤 값(프록시가 붙인 실제 접속 IP)을 쓴다.
    맨 앞 값은 클라이언트가 마음대로 넣을 수 있어서 쓰지 않는다."""
    # ponytail: 프록시가 한 겹이라고 가정. 프록시가 여러 겹이면 맨 뒤가 내부 프록시 IP가 되어 모두가 한도를 같이 쓴다
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def on_invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
    log.info("excuse error=INVALID_INPUT")
    return error_response(422, "INVALID_INPUT", "입력을 다시 확인해주세요")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/excuse", response_model=ExcuseResponse)
async def create_excuse(req: ExcuseRequest, request: Request) -> ExcuseResponse | JSONResponse:
    start = time.monotonic()
    error = "-"
    try:
        if not limiter.allow(client_ip(request)):
            error = "RATE_LIMITED"
            return error_response(429, error, "핑계도 쉬어가며 만들어야 해요. 잠시 후 다시!")
        return await llm.generate_excuse(req)
    except llm.LLMTimeout:
        error = "LLM_TIMEOUT"
        return error_response(504, error, "너무 오래 고민하는 중이에요. 다시 시도해주세요")
    except llm.LLMError:
        error = "LLM_ERROR"
        return error_response(502, error, "핑계 공장이 잠깐 멈췄어요")
    finally:
        ms = int((time.monotonic() - start) * 1000)
        log.info("excuse absurdity=%d tone=%s ms=%d error=%s", req.absurdity, req.tone, ms, error)
