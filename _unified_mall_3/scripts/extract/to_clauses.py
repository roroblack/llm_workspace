"""페이지 JSON → 조항 단위 구조화 (전처리 5·6·7·8·9단계).

★왜 이게 병목인가

    페이지 단위까지만 오면 판정 근거를 **"몇 쪽"** 으로만 인용할 수 있다.
    실제로 필요한 것은 **"제○조 몇 항"** 이다. 그리고 이게 없으면
    8(중복 제거) · 9(청킹) · 10(색인) · 11(평가)이 전부 막힌다.
    ERD 의 `assessment_clause_citation` 이 참조할 `policy_clause` 를 만드는 단계가 여기다.

이 스크립트가 하는 일 (단계 번호는 팀이 정리한 11단계 기준)

    5 문서 구조 복원   : 보통약관/특별약관/별표 같은 **부(部) 경계**를 찾는다
    6 조항 구조화      : `제○조(제목)` 로 잘라 조항 단위 레코드를 만든다
    7 메타데이터 부착   : 출처·페이지·부 경계·표를 각 조항에 붙인다
    8 중복 처리(준비)  : 조항마다 **내용 해시**를 계산한다
                        ★번호가 아니라 **내용**이 정체성이다 — 같은 번호라도 내용이
                          다르면 다른 조항이고, 번호가 바뀌어도 내용이 같을 수 있다
    9 계층형 청킹      : 부 → 조 → (긴 조는 항 단위) 로 나눈다

이 스크립트가 **하지 않는 일**
    - 조항이 무엇을 뜻하는지 해석하지 않는다
    - 표가 어느 조항에 속하는지 **추정하지 않는다.** 같은 페이지에 있으면 그 사실만 기록한다
    - 경계를 못 찾으면 조용히 넘어가지 않고 그 사실을 남긴다

실행:
    python -m scripts.extract.to_clauses --sha 968e67f4d3b6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.errors import InfraError, ValidationErr

_ROOT = Path(__file__).resolve().parents[2]
_IN = _ROOT / "data" / "extracted"
_OUT = _ROOT / "data" / "structured"

SCHEMA_VERSION = "1"

#: 조항 머리. `제12조(보험금의 지급사유)` / `제 12 조` 변형을 함께 잡는다.
_ARTICLE = re.compile(r"제\s*(\d{1,3})\s*조(?:의\s*(\d{1,2}))?\s*(?:[（(]\s*([^)）\n]{1,60})\s*[)）])?")
#: 항 번호(①②③ 또는 1. 2. 3.)
_PARA = re.compile(r"(?:^|\n)\s*([①-⑳]|\d{1,2}\.)\s")
#: 부(部) 경계. 문서 구조 복원(5단계)에 쓴다.
_SECTION = re.compile(
    r"(보통약관|특별약관|무배당\s*특별약관|별\s*표\s*\d*|부\s*록|용어의\s*정의|약관\s*요약서)"
)


def _norm(text: str) -> str:
    """해시 계산용 정규화. 공백·줄바꿈 차이로 다른 조항이 되지 않게 한다."""
    return re.sub(r"\s+", " ", text).strip()


def _clause_hash(section: str, title: str, body: str) -> str:
    """★조항의 정체성. **번호를 넣지 않는다** — 번호가 바뀌어도 내용이 같으면 같은 조항이다."""
    return hashlib.sha256(f"{section}\x1f{title}\x1f{_norm(body)}".encode()).hexdigest()


def build(page_doc: dict) -> dict:
    pages = page_doc["pages"]
    if not pages:
        raise ValidationErr("페이지가 없습니다.")

    # ── 5) 문서 구조 복원: 현재 페이지가 어느 부(部)에 속하는지 추적 ──
    section_of_page: dict[int, str] = {}
    current = "미상"
    for pg in pages:
        m = _SECTION.search(pg["text"][:400])
        if m:
            current = re.sub(r"\s+", "", m.group(1))
        section_of_page[pg["page"]] = current

    # ── 6) 조항 경계 찾기 ──
    #: (페이지, 페이지내 오프셋, 조번호, 가지번호, 제목)
    heads: list[tuple[int, int, str, str, str]] = []
    for pg in pages:
        for m in _ARTICLE.finditer(pg["text"]):
            heads.append(
                (pg["page"], m.start(), m.group(1), m.group(2) or "", (m.group(3) or "").strip())
            )
    if not heads:
        raise InfraError(
            "조항 머리(`제○조`)를 하나도 찾지 못했습니다. "
            "약관이 아니거나 텍스트 추출이 실패했을 수 있습니다."
        )

    text_of = {pg["page"]: pg["text"] for pg in pages}
    tables_of = {pg["page"]: pg.get("tables", []) for pg in pages}

    clauses: list[dict] = []
    for i, (page, off, no, sub, title) in enumerate(heads):
        # 본문 = 이 머리부터 다음 머리 전까지 (페이지를 넘어갈 수 있다)
        if i + 1 < len(heads):
            end_page, end_off = heads[i + 1][0], heads[i + 1][1]
        else:
            end_page, end_off = pages[-1]["page"], len(text_of[pages[-1]["page"]])

        parts: list[str] = []
        for p in range(page, end_page + 1):
            t = text_of.get(p, "")
            a = off if p == page else 0
            b = end_off if p == end_page else len(t)
            parts.append(t[a:b])
        body = "\n".join(parts)

        # ── 9) 계층형 청킹: 긴 조항은 항 단위로 쪼갠다 ──
        paras = [x for x in _PARA.split(body) if x and x.strip()]
        label = f"제{no}조" + (f"의{sub}" if sub else "")
        clauses.append(
            {
                "clause_no": label,
                "title": title,
                "section": section_of_page.get(page, "미상"),
                # ── 7) 메타데이터: locator ──
                "locator": {"page_from": page, "page_to": end_page, "char_offset": off},
                "text": body,
                "char_length": len(body),
                "paragraph_count": max(len(paras) - 1, 0),
                # 같은 페이지에 있던 표. ★어느 조항 것인지 추정하지 않는다.
                "tables_on_pages": {
                    str(p): len(tables_of.get(p, [])) for p in range(page, end_page + 1)
                    if tables_of.get(p)
                },
                # ── 8) 중복 처리 준비 ──
                "content_hash": _clause_hash(
                    section_of_page.get(page, "미상"), title, body
                ),
            }
        )

    dup: dict[str, int] = {}
    for c in clauses:
        dup[c["content_hash"]] = dup.get(c["content_hash"], 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": page_doc["source"],
        "identification": page_doc.get("identification", "unidentified"),
        "extractor": page_doc.get("extractor", ""),
        "stats": {
            "pages": page_doc["stats"]["pages"],
            "clauses": len(clauses),
            "sections": len(set(section_of_page.values())),
            "unique_clause_hashes": len(dup),
            "duplicate_clauses": sum(v - 1 for v in dup.values() if v > 1),
        },
        "sections": sorted(set(section_of_page.values())),
        "clauses": clauses,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", required=True, help="sha256 접두사")
    args = ap.parse_args()

    hits = sorted(_IN.rglob(f"{args.sha}*.json"))
    if not hits:
        raise InfraError(f"페이지 JSON 을 찾지 못했습니다: {args.sha} (4단계를 먼저 실행하세요)")
    src = hits[0]
    doc = build(json.loads(src.read_text(encoding="utf-8")))

    rel = src.relative_to(_IN)
    out = _OUT / rel.parent / f"{args.sha[:12]}.clauses.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    s = doc["stats"]
    print(f"[OK] {src.relative_to(_ROOT)}")
    print(f"     {s['pages']}쪽 → 조항 {s['clauses']}개 / 부(部) {s['sections']}개")
    print(f"     고유 조항 해시 {s['unique_clause_hashes']}개 / 문서 내 중복 {s['duplicate_clauses']}개")
    print(f"     부 목록: {doc['sections']}")
    print(f"     → {out.relative_to(_ROOT)} ({out.stat().st_size:,}B)")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(_ROOT))
    main()
