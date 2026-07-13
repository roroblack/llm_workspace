"""요청과 응답에 사용하는 Pydantic 스키마를 정의하는 모듈입니다.

게시글은 목록용(가벼움)과 상세용(전체 필드)을 분리해
필요한 데이터만 응답하도록 설계했습니다.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 회원(User) 스키마 ----------


class UserCreate(BaseModel):
    """회원가입 요청 스키마입니다."""

    username: str = Field(..., min_length=3, max_length=50, examples=["user01"])
    password: str = Field(..., min_length=4, max_length=100, examples=["1234"])
    name: str = Field(..., min_length=1, max_length=50, examples=["홍길동"])


class UserResponse(BaseModel):
    """회원 정보 응답 스키마입니다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    created_at: datetime


# ---------- 토큰(Token) 스키마 ----------


class TokenResponse(BaseModel):
    """로그인 성공 시 반환하는 토큰 스키마입니다."""

    access_token: str
    token_type: str = "bearer"


# ---------- 게시글(Board) 스키마 ----------


class BoardCreate(BaseModel):
    """게시글 등록 요청 스키마입니다."""

    title: str = Field(..., min_length=1, max_length=200, examples=["첫 번째 게시글"])
    content: str = Field(..., min_length=1, examples=["FastAPI와 MySQL을 연동한 게시글입니다."])


class BoardUpdate(BaseModel):
    """게시글 수정 요청 스키마입니다."""

    title: str = Field(..., min_length=1, max_length=200, examples=["수정된 제목"])
    content: str = Field(..., min_length=1, examples=["수정된 내용입니다."])


class BoardListResponse(BaseModel):
    """게시글 전체 조회에 사용하는 가벼운 응답 스키마입니다(본문 content 제외)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    view_count: int
    writer_name: str
    created_at: datetime


class BoardDetailResponse(BaseModel):
    """게시글 상세 조회에 사용하는 전체 응답 스키마입니다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    view_count: int
    writer_id: int
    writer_name: str
    created_at: datetime
    updated_at: datetime
