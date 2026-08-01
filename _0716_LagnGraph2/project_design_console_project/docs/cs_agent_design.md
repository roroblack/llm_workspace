# CS 티켓 자동 분류·답변 에이전트 — 설계 문서

## 1. 요구사항 분석
- 입력: `data/support_tickets.csv`의 `content`
- 출력: severity(긴급/보통/낮음) + 답변 초안
- 확인된 티켓 수: 8건

## 2. 도구 목록
| 도구 | 입력 → 출력 | 설명 |
|---|---|---|
| classify_severity | str → str | 심각도 분류 |
| search_faq | str → str | FAQ 검색 |
| draft_reply | (str, str) → str | 답변 초안 생성 |

## 3. 데이터 흐름
티켓 입력 → 심각도 분류 → FAQ 검색 → 답변 초안 → 최종 결과

## 4. 텍스트 아키텍처
support_tickets.csv → classify_severity → search_faq(10건) → draft_reply → 출력

## 5. 구성요소 판단
- RAG: 보류 — 현재 FAQ는 CSV 검색으로 충분
- 메모리: 제외 — 티켓 단건 처리
- 멀티에이전트: 제외 — 도구 3개
