# 레거시 보관소

이 저장소는 쇼핑몰 실습(`_unified_mall`)에서 출발해 **보험 보장 판정**으로 전환됐다.
여기는 그 과정에서 쓰이지 않게 된 것들을 **버전별 압축본**으로 모아 둔 자리다.

## ★압축해서 보관하는 이유

**현행 코드가 레거시를 참조하면 레거시를 지울 수 없게 된다.**

한 번 그런 일이 있었다 — 커머스 시딩 CSV 를 여기로 옮기고
`settings.LEGACY_DATA_DIR` 을 만들어 현행 코드가 그걸 읽게 했다.
그러면 "레거시"가 아니라 **그냥 다른 폴더에 있는 현행 코드**다.

그래서 **압축본으로만 둔다.** `import` 도, 파일 경로 참조도 불가능하다.
레거시 폴더를 통째로 지워도 현행 프로젝트는 그대로 돈다.

## 보관물

| 파일 | 내용 |
|---|---|
| `v3_commerce.zip` | 쇼핑몰 실습(`_unified_mall` ~ `_unified_mall_2`) 잔재 |
| `v4_extract/` | 전처리 v4 이전 산출물 |

### `v3_commerce.zip` 안에 든 것

```
app/routers/     products · orders · payments · agent · nlp · mcp · a2a
app/tools/       commerce_tools.py
app/application/ commerce.py
app/adapters/    sql_order_repo · sql_catalog
app/services/    payment · order · catalog
app/schemas/     commerce.py       ← 인증 DTO 만 app/schemas/auth.py 로 분리해 남김
app/ml/          recommend.py
app/agent/       lc_agent · lc_tools · react
app/mcp/         server.py
app/a2a_old/     ★이름만 A2A 인 커머스 잔재. 표준 A2A 가 아니다
static/          shop · orders · index · mcp 화면
data/            mall.db · products.csv · orders.csv · inventory.csv · cs_inquiries.csv
tests/           커머스 테스트 17개
```

## 되살리려면

```bash
cd legacy && unzip v3_commerce.zip
```

그리고 필요한 것을 `app/` 아래로 옮긴 뒤 `app/main.py` 에서 `include_router` 한다.
**다만 되살리기 전에 왜 뺐는지 먼저 읽으라.**

## 남겨 둔 것 (옮기지 않음)

`app/db/models.py` · `app/db/seed.py` 에는 커머스 테이블이 있지만
인증·감사 등 현행 코드가 같은 파일을 쓴다.
분리는 백엔드 담당이 보험 DB 스키마를 새로 짤 때 함께 한다.
