# app/schemas.py
# API 요청과 응답 데이터 구조를 정의하는 Pydantic 스키마 파일입니다.

from datetime import datetime  # 응답에 날짜와 시간을 포함하기 위해 사용합니다.
from pydantic import BaseModel, Field  # 데이터 검증 모델과 필드 조건을 정의하기 위해 사용합니다.


class UserCreate(BaseModel):
    # 회원가입 요청 데이터 구조입니다.
    username: str = Field(..., min_length=3, max_length=50, description="로그인 아이디")  # 아이디 길이를 검증합니다.
    password: str = Field(..., min_length=4, max_length=100, description="로그인 비밀번호")  # 비밀번호 길이를 검증합니다.
    name: str = Field(..., min_length=1, max_length=50, description="회원 이름")  # 이름 길이를 검증합니다.


class UserResponse(BaseModel):
    # 회원가입 성공 후 반환할 회원 정보 구조입니다.
    id: int  # 회원 고유 번호입니다.
    username: str  # 로그인 아이디입니다.
    name: str  # 회원 이름입니다.
    created_at: datetime  # 가입 시각입니다.

    model_config = {"from_attributes": True}  # SQLAlchemy ORM 객체를 Pydantic 응답으로 변환할 수 있게 합니다.


class TokenResponse(BaseModel):
    # 로그인 성공 후 반환할 JWT 토큰 응답 구조입니다.
    access_token: str  # API 인증에 사용할 액세스 토큰입니다.
    token_type: str = "bearer"  # Swagger 인증 방식에서 사용하는 토큰 타입입니다.


class BoardCreate(BaseModel):
    # 게시글 등록 요청 데이터 구조입니다.
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")  # 제목 필수 입력 조건입니다.
    content: str = Field(..., min_length=1, description="게시글 내용")  # 내용 필수 입력 조건입니다.


class BoardUpdate(BaseModel):
    # 게시글 수정 요청 데이터 구조입니다.
    title: str = Field(..., min_length=1, max_length=200, description="수정할 게시글 제목")  # 수정 제목입니다.
    content: str = Field(..., min_length=1, description="수정할 게시글 내용")  # 수정 내용입니다.


class BoardListResponse(BaseModel):
    # 게시글 전체 조회에서 사용할 간단 응답 구조입니다.
    id: int  # 게시글 번호입니다.
    title: str  # 게시글 제목입니다.
    view_count: int  # 게시글 조회수입니다.
    writer_name: str  # 작성자 이름입니다.
    created_at: datetime  # 작성 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.


class BoardDetailResponse(BaseModel):
    # 게시글 상세 조회에서 사용할 응답 구조입니다.
    id: int  # 게시글 번호입니다.
    title: str  # 게시글 제목입니다.
    content: str  # 게시글 내용입니다.
    view_count: int  # 게시글 조회수입니다.
    writer_id: int  # 작성자 회원 번호입니다.
    writer_name: str  # 작성자 이름입니다.
    created_at: datetime  # 작성 시각입니다.
    updated_at: datetime  # 수정 시각입니다.

    model_config = {"from_attributes": True}  # ORM 객체 기반 변환을 허용합니다.
