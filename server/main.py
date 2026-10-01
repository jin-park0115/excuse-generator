# FastAPI 서버 진입점. 앱의 요청을 받아 LLM 핑계를 돌려준다 (M1: /health만 있음).
from fastapi import FastAPI

app = FastAPI(title="핑계 생성기 API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
