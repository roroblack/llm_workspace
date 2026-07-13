# 명명 정렬(app_ori 기준) 및 작동 검증 보고서

`app` 폴더의 함수·매개변수·지역변수 이름을 `app_ori`의 명명 규칙에 맞춰 정렬한 뒤,
MySQL(`fastapi_db`) 실연동으로 전체 엔드포인트를 end-to-end 검증한 결과입니다.

- 작성일: 2026-07-03
- 성격: 순수 리네이밍 리팩터링(동작 로직 변경 없음) + 회귀 검증
- 결과: **엔드포인트 15/15 PASS + cascade 삭제 PASS**

---

## 1. 적용한 명명 변경

| 파일 | 변경 전 | 변경 후 (app_ori 기준) |
|------|---------|----------------------|
| `app/security.py` | `hash_password(plain_password)` | `hash_password(password)` |
| `app/security.py` | `return jwt.encode(...)` | `encoded_jwt = jwt.encode(...)` 후 `return encoded_jwt` |
| `app/routers/auth.py` | `signup(user_in)` | `signup(user_data)` |
| `app/routers/auth.py` | `existing` / `user` | `existing_user` / `new_user` |
| `app/routers/boards.py` | `create_board(board_in)` / `board` | `create_board(board_data)` / `new_board` |
| `app/routers/boards.py` | `list_boards` | `get_boards` |
| `app/routers/boards.py` | `update_board(board_in)` | `update_board(board_data)` |
| `app/main.py` | `read_root()` | `root()` |

### 변경 없이 유지 (이미 app_ori와 동일)
- `verify_password(plain_password, hashed_password)` — 파라미터명 일치
- 헬퍼 `to_board_detail_response` / `to_board_list_response`
- 스키마명, `get_board` / `delete_board` 등

### 정적 점검
- 옛 이름(`board_in`, `user_in`, `list_boards`, `read_root`) 소스 잔여 참조: **0건**
- 전 파일 `py_compile` 통과
- 라우터 import·와이어링 정상
  - auth: `login`, `signup`
  - boards: `create_board`, `delete_board`, `get_board`, `get_boards`, `update_board`

---

## 2. 작동 검증 결과 (MySQL 실연동, 15/15 PASS)

| # | 테스트 | 기대 | 결과 |
|---|--------|------|------|
| 1 | `GET /` 헬스체크 | 200 | ✅ 200 |
| 2 | `POST /auth/signup` | 201 | ✅ 201 |
| 3 | `POST /auth/signup` 중복 | 409 | ✅ 409 |
| 4 | `POST /auth/login` | 토큰 발급 | ✅ 발급 |
| 5 | 로그인 잘못된 비밀번호 | 401 | ✅ 401 |
| 6 | `POST /boards` (인증) writer_name | "홍길동" | ✅ 홍길동 |
| 7 | `POST /boards` (인증 없음) | 401 | ✅ 401 |
| 8 | `GET /boards` 목록: content 제외 | 제외 | ✅ 제외 |
| 9 | `GET /boards` 목록: writer_name 포함 | "홍길동" | ✅ 포함 |
| 10 | `GET /boards/{id}` 조회수 증가 | 1→2 | ✅ 1→2 |
| 11 | `GET /boards/{id}` writer_id+writer_name | 포함 | ✅ 포함 |
| 12 | `PUT /boards/{id}` (인증) | 200 | ✅ 200 |
| 13 | `GET /boards/999` 없음 | 404 | ✅ 404 |
| 14 | `DELETE /boards/{id}` (인증) | 204 | ✅ 204 |
| 15 | `DELETE` 재삭제(이미 없음) | 404 | ✅ 404 |
| — | 회원 삭제 시 게시글 **cascade** | before=1→after=0 | ✅ PASS |

> 테스트는 게시글 생성 응답의 실제 `id`를 받아 사용했습니다.
> (MySQL `AUTO_INCREMENT`는 DELETE 후에도 값이 계속 증가하므로 id를 1로 가정하면 안 됩니다.
>  최초 실행 시 이 가정 때문에 5건이 404로 실패했고, 테이블 TRUNCATE로 id를 리셋하고
>  실제 id를 사용하도록 고쳐 재실행하여 전 항목 통과를 확인했습니다.)
>
> 검증용 임시 데이터(user01, casc01 및 게시글)는 모두 정리 완료했습니다.

---

## 3. 결론

- 리네이밍은 **동작에 영향을 주지 않는 순수 리팩터링**임을 회귀 테스트로 확인했습니다.
- 앞선 재설계 개선(FK 관계, 목록/상세 스키마 분리, cascade, timezone-aware, 204 등)은
  이름 변경 후에도 **모두 정상 동작**합니다.
- 상세 개선 항목·근거는 [`improvements.md`](improvements.md) 참고.
