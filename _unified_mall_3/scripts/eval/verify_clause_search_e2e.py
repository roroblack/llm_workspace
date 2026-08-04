"""조항 의미검색이 **실제로 도는지** 끝에서 끝까지 확인한다.

    python -m scripts.eval.verify_clause_search_e2e            # 리랭킹 끄고
    python -m scripts.eval.verify_clause_search_e2e --rerank   # 켜고(GPU 권장)

★단위 테스트는 어댑터를 가짜로 바꾼다. 이 스크립트는 **진짜를 쓴다** —
  진짜 PG · 진짜 임베더 · (선택) 진짜 리랭커 · 진짜 라우터.
  「테스트가 통과한다」와 「서비스가 돈다」는 다른 말이다(CLAUDE.md §4).

★관리자 인증은 `dependency_overrides` 로 통과시킨다. 비밀번호를 넣지 않는다 —
  검증하려는 것은 **경로가 도는가**이지 로그인 폼이 아니다.
  다만 **경로가 고객앱에 없는지**는 여기서 함께 확인한다.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: 문서화된 실패 사례 — 벡터만으로는 「보상하지 않는 사항」이 올라온다(거리 0.941).
QUERY = "치과치료 보철료는 보상하나요"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerank", action="store_true")
    ap.add_argument("--query", default=QUERY)
    ap.add_argument("--final-k", type=int, default=5)
    ap.add_argument("--out", type=pathlib.Path, default=None)
    a = ap.parse_args()

    from fastapi.testclient import TestClient

    from app.auth.roles import require_admin
    from app.core.config import get_settings
    from app.main import create_app

    st = get_settings()
    report: dict = {
        "schema_version": "clause-search-e2e-v1",
        "query": a.query,
        "rerank_requested": a.rerank,
        "settings": {
            "INSURANCE_CLAUSE_RERANK_ENABLED": st.INSURANCE_CLAUSE_RERANK_ENABLED,
            "CLAUSE_RERANK_SCORE_BODY": st.CLAUSE_RERANK_SCORE_BODY,
            "CLAUSE_RERANK_MAX_LENGTH": st.CLAUSE_RERANK_MAX_LENGTH,
            "RERANKER_MODEL": st.RERANKER_MODEL,
        },
        "checks": [],
    }

    def check(name: str, ok: bool, detail: str = "") -> None:
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(f"  {'OK ' if ok else '★실패'} {name}" + (f" — {detail}" if detail else ""))

    # ── 1. 고객앱에 경로가 없어야 한다 ──────────────────────────────
    r = TestClient(create_app("customer")).post(
        "/api/admin/clause-search", json={"query": a.query})
    check("고객앱(8080)에 경로 없음", r.status_code == 404, f"HTTP {r.status_code}")

    # ── 2. 승인 릴리스 프로필이 완전한가 ────────────────────────────
    from app.adapters import clause_query_embedder

    try:
        emb = clause_query_embedder.build()
        check("질의 임베더 생성", True, emb.profile_key)
    except Exception as exc:  # noqa: BLE001
        check("질의 임베더 생성", False, f"{type(exc).__name__}: {exc}")
        return 1

    # ── 3. 색인이 준비됐는가 ───────────────────────────────────────
    from app.adapters import pgvector_clause_index as ix

    check("색인 세대·모델 확인", bool(ix.current_generation()),
          f"{ix.current_generation()} / {ix.current_embed_model()[:40]}")

    # ── 4. 실제 검색 ──────────────────────────────────────────────
    app = create_app("admin")
    app.dependency_overrides[require_admin] = lambda: {"username": "e2e", "role": "ADMIN"}
    client = TestClient(app)

    body = {"query": a.query, "allow_global": True, "final_k": a.final_k,
            "rerank": a.rerank}
    t0 = time.perf_counter()
    res = client.post("/api/admin/clause-search", json=body)
    elapsed = round(time.perf_counter() - t0, 1)
    app.dependency_overrides.clear()

    report["http_status"] = res.status_code
    report["elapsed_seconds"] = elapsed
    if res.status_code != 200:
        check(f"검색 요청(rerank={a.rerank})", False,
              f"HTTP {res.status_code}: {str(res.json())[:200]}")
        report["body"] = res.json()
        if a.out:
            a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        return 1

    d = res.json()
    report["body"] = {k: v for k, v in d.items() if k != "hits"}
    report["hits"] = d["hits"]
    check(f"검색 요청(rerank={a.rerank})", True, f"HTTP 200 · {elapsed}초")
    check("근거 후보를 찾음", len(d["hits"]) > 0, f"{len(d['hits'])}건")
    check("재정렬 여부가 요청과 일치", d["reranked"] is a.rerank, f"reranked={d['reranked']}")
    check("어느 색인으로 찾았는지 남김", "index_generation" in (d.get("provenance") or {}),
          str(d.get("provenance", {}).get("index_generation")))
    check("판정처럼 읽히는 필드 없음",
          not ({"verdict", "covered", "abstained"} & set(d)))
    if a.rerank:
        check("채점 본문이 설정대로",
              d["provenance"].get("rerank_score_body") == st.CLAUSE_RERANK_SCORE_BODY,
              str(d["provenance"].get("rerank_score_body")))

    print(f"\n  질의: {a.query}")
    print(f"  후보 {d['provenance'].get('candidates_found')}건 → 상위 {len(d['hits'])}건"
          f" (본문 없어 제외 {d.get('dropped_incomplete')}건)")
    for i, h in enumerate(d["hits"], 1):
        print(f"   {i}. [{h['distance']:.3f}] {h['insurer']} · {h['section']} "
              f"{h['qualified_no']} {h['title'][:28]} p{h['page_from']}–{h['page_to']}")

    ok = all(c["ok"] for c in report["checks"])
    report["all_ok"] = ok
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n  기록 → {a.out}")
    print(f"\n  {'전부 통과' if ok else '★실패 있음'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
