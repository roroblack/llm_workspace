# app 폴더 재설계 개선 보고서

`app_ori` 폴더의 더 나은 설계를 `app` 폴더로 병합하여 재설계했습니다.
이 문서는 **정확히 무엇이, 왜 개선되었는지**와 **실제 동작 검증 결과**를 기록합니다.

- 작성일: 2026-07-03
- 대상 경로: `app/` (실서비스 코드), 비교 원본: `app_ori/`
- 검증 방식: MySQL(`fastapi_db`) 실연동 + 전체 엔드포인트 end-to-end 테스트

---

## 1. 개선 항목 요약

| # | 항목 | 변경 전 (기존 app) | 변경 후 (재설계 app) | 출처 | 효과 |
|---|------|-------------------|---------------------|------|------|
| 1 | 작성자 연결 방식 | `writer` = username **문자열 복사** | `user_id` **ForeignKey → users.id** + `relationship` | app_ori | 정규화·무결성·관계 조회 |
| 2 | 회원 삭제 시 게시글 | 방치(고아 데이터) | `cascade="all, delete-orphan"`로 **자동 삭제** | app_ori | 데이터 정합성 |
| 3 | 게시글 응답 스키마 | 목록·상세 **동일**(항상 content 포함) | `BoardListResponse`(가벼움)/`BoardDetailResponse`(전체) **분리** | app_ori | 목록 응답 경량화 |
| 4 | 작성자 정보 노출 | username만 | **writer_id + writer_name(실명)** | app_ori | 화면 표시 편의 |
| 5 | JWT 만료 시각 | `datetime.utcnow()` (naive, 3.12+ deprecated) | `datetime.now(timezone.utc)` (**timezone-aware**) | app_ori | 정확성·향후 호환 |
| 6 | DELETE 응답 | 200 + JSON 본문 | **204 No Content** (REST 표준) | app_ori | 규약 준수 |
| 7 | 입력 검증 강도 | username≥2, password≥1 | **username≥3, password≥4** | app_ori | 최소 품질 보장 |

> 참고: 아래 두 가지는 **기존 app이 더 나았던 부분이라 그대로 유지**했습니다.
> - 중복 회원가입 응답: **409 Conflict** 유지 (app_ori는 400) — 중복 리소스에는 409가 의미상 정확.
> - `requirements.txt`의 **`bcrypt==4.0.1` 고정** 유지 — passlib 1.7.4의 회원가입 크래시 예방.

---

## 2. 항목별 상세

### 2-1. 작성자를 외래키(ForeignKey) 관계로 연결 ⭐
기존에는 게시글에 작성자 `username`을 **문자열로 복사**해 저장했습니다.
이 방식은 FK 제약이 없어 무결성을 보장하지 못하고, 회원의 이름 등 부가 정보를 함께 조회할 수 없습니다.

```python
# 변경 후: app/models.py
class Board(Base):
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    writer: Mapped["User"] = relationship("User", back_populates="posts")

class User(Base):
    posts: Mapped[list["Board"]] = relationship(
        "Board", back_populates="writer", cascade="all, delete-orphan"
    )
```

- **효과**: `board.writer.name`처럼 관계를 타고 작성자 정보를 조회 가능.
- **무결성**: 존재하지 않는 user_id로는 게시글을 만들 수 없음(FK 제약).

### 2-2. 회원 삭제 시 게시글 자동 삭제 (cascade)
`cascade="all, delete-orphan"` 덕분에 회원을 삭제하면 그 회원이 쓴 게시글도 함께 삭제되어
**고아(orphan) 데이터가 남지 않습니다.** (아래 3장에서 실제 검증)

### 2-3. 목록/상세 응답 스키마 분리
- `BoardListResponse`: `id, title, view_count, writer_name, created_at` — **본문 content 제외**로 경량.
- `BoardDetailResponse`: 위 필드 + `content, writer_id, updated_at` — 전체 정보.

목록 화면에서는 글 본문이 필요 없으므로, 매 게시글의 본문 전체를 내려보내던 낭비를 제거했습니다.

### 2-4. 응답에 작성자 실명(writer_name) 포함
관계를 통해 `writer_id`(회원 번호)와 `writer_name`(실제 이름)을 응답에 포함해,
프론트에서 "홍길동"처럼 바로 표시할 수 있습니다. 변환은 라우터의 헬퍼 함수
`to_board_detail_response` / `to_board_list_response`가 담당합니다.

### 2-5. JWT 만료 시각 timezone-aware
`datetime.utcnow()`는 시간대 정보가 없는(naive) 값이며 Python 3.12+에서 deprecated입니다.
`datetime.now(timezone.utc)`로 교체해 정확성과 향후 호환성을 확보했습니다.

### 2-6. DELETE는 204 No Content
성공적으로 삭제한 경우 본문 없이 `204`를 반환하도록 변경해 REST 규약을 따릅니다.

### 2-7. 입력 검증 강화
`username`은 3자 이상, `password`는 4자 이상으로 최소 품질을 보장합니다.
(README 예시 `user01`/`1234`는 그대로 통과합니다.)

---

## 3. 실제 동작 검증 결과 (MySQL 실연동)

`fastapi_db`에 연결해 전체 흐름을 end-to-end로 실행한 결과입니다. **전 항목 통과.**

| 테스트 | 기대 | 결과 |
|--------|------|------|
| 회원가입 `POST /auth/signup` | 201 | ✅ 201, 회원 생성 |
| 로그인 `POST /auth/login` | JWT 발급 | ✅ 토큰 발급(125자) |
| 게시글 등록 `POST /boards` (인증) | 201 + writer_name | ✅ writer_id=1, writer_name="홍길동" |
| 목록 `GET /boards` | content 필드 없음 | ✅ content 미포함, writer_name 포함 |
| 상세 `GET /boards/{id}` ×2 | 조회수 증가 | ✅ view_count 1→2 |
| 수정 `PUT /boards/{id}` (인증) | 반영 | ✅ 제목 변경 확인 |
| 인증 없이 등록 | 401 | ✅ 401 |
| 삭제 `DELETE /boards/{id}` (인증) | 204 | ✅ 204 |
| 중복 회원가입 | 409 | ✅ 409 |
| **회원 삭제 시 게시글 cascade** | 함께 삭제 | ✅ before=1 → after=0 |

> 검증에 사용한 임시 데이터(user01, casc01 및 게시글)는 모두 정리 완료했습니다.

---

## 4. 변경된 파일

- `app/models.py` — FK + relationship + cascade 적용, `password_hash` 컬럼
- `app/schemas.py` — 목록/상세 응답 스키마 분리, 검증 강화, `TokenResponse`
- `app/security.py` — JWT 만료 시각 timezone-aware
- `app/routers/auth.py` — `password_hash` 사용, 중복가입 409 유지
- `app/routers/boards.py` — FK 기반 소유권 검사, 응답 변환 헬퍼, DELETE 204

변경 없이 유지: `app/main.py`, `app/database.py`, `requirements.txt`(bcrypt 고정 유지)
