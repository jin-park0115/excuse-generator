# FastAPI 서버 진입점. 앱의 요청을 받아 LLM 핑계를 돌려준다.
import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import llm
from schemas import ExcuseRequest, ExcuseResponse

# 로그에는 시간·레벨·말투·응답 시간·에러 코드만 남긴다 (사용자 입력 텍스트·API 키는 남기지 않음)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("excuse")

app = FastAPI(title="핑계 생성기 API")


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
async def create_excuse(req: ExcuseRequest) -> ExcuseResponse | JSONResponse:
    start = time.monotonic()
    error = "-"
    try:
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
