# -*- coding: utf-8 -*-
"""
API 요청/응답 스키마 모듈입니다.
FastAPI는 Pydantic 스키마를 이용해 요청 JSON을 검증하고 Swagger 문서를 자동 생성합니다.
"""

# typing.List는 문자열 리스트 같은 타입 주석에 사용합니다.
from typing import Any, List, Optional

# pydantic의 BaseModel과 Field는 데이터 스키마를 정의하기 위해 사용합니다.
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """사용자 질문 요청 스키마입니다."""

    # question은 사용자가 ReAct 에이전트에게 입력하는 질문입니다.
    question: str = Field(..., description="사용자 질문")

    # max_steps는 에이전트 루프의 최대 반복 횟수입니다.
    max_steps: int = Field(6, description="ReAct 루프 최대 반복 횟수")


class AgentStep(BaseModel):
    """ReAct 루프의 한 단계 실행 기록 스키마입니다."""

    # step은 현재 몇 번째 반복인지 나타냅니다.
    step: int

    # thought는 모델이 어떤 판단을 했는지 요약한 설명입니다.
    thought: str

    # action은 호출한 도구 이름입니다.
    action: str

    # action_input은 도구에 전달된 인자입니다.
    action_input: dict[str, Any]

    # observation은 도구 실행 결과입니다.
    observation: str


class AgentResponse(BaseModel):
    """ReAct 에이전트 응답 스키마입니다."""

    # answer는 최종 사용자 답변입니다.
    answer: str

    # steps는 ReAct 루프의 단계별 기록입니다.
    steps: List[AgentStep] = []

    # stopped_by는 종료 이유입니다.
    stopped_by: str = "final_answer"


class VectorSearchRequest(BaseModel):
    """Vector DB 검색 요청 스키마입니다."""

    # query는 검색할 자연어 질문입니다.
    query: str = Field(..., description="Vector DB 검색 질의")

    # top_k는 검색 결과 개수입니다.
    top_k: int = Field(3, description="상위 검색 결과 개수")


class VectorSearchItem(BaseModel):
    """Vector DB 검색 결과 1건 스키마입니다."""

    # doc_id는 문서 고유 ID입니다.
    doc_id: str

    # source는 원본 파일명 또는 출처입니다.
    source: str

    # score는 코사인 유사도 점수입니다.
    score: float

    # text는 검색된 문서 내용 일부입니다.
    text: str


class VectorSearchResponse(BaseModel):
    """Vector DB 검색 응답 스키마입니다."""

    # items는 검색 결과 목록입니다.
    items: List[VectorSearchItem]


class StatusResponse(BaseModel):
    """서버 상태 응답 스키마입니다."""

    # ok는 서버가 정상인지 나타냅니다.
    ok: bool

    # message는 상태 메시지입니다.
    message: str

    # details는 설정 상태나 부가 정보를 담습니다.
    details: Optional[dict[str, Any]] = None
