# API 요청·응답 모양을 정의하는 Pydantic 모델 (PRD 섹션 5).
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Tone = Literal["공손한 직장인체", "사극체", "급식체", "뉴스 앵커체", "발표자(학회)체"]


class ExcuseRequest(BaseModel):
    situation: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    absurdity: int = Field(ge=1, le=10)
    tone: Tone = "공손한 직장인체"
    previous_excuse: Annotated[str, StringConstraints(max_length=300)] | None = None


class ExcuseResponse(BaseModel):
    excuse: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    credibility: int = Field(ge=0, le=100)
    comment: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
