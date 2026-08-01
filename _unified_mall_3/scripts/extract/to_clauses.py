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

#: 조항 머리. ★**줄 시작**에 있는 것만 인정한다.
#: 본문 속 상호참조("제4조에 따라…")를 머리로 오인하면 5~6자짜리 가짜 조항이 쏟아진다
#: (실측: 그렇게 391개 중 112개(28%)가 100자 미만이었다).
#: 조항 머리는 줄 첫머리에 오고, 상호참조는 문장 중간에 온다.
_ARTICLE = re.compile(
    r"^[ \t ]{0,6}제\s*(\d{1,3})\s*조(?:의\s*(\d{1,2}))?"
    #: 제목 괄호는 `()` 말고 `【】` `[]` 도 쓴다(NH 문서 실측).
    r"\s*(?:[（(\[【]\s*([^)）\]】\n]{1,60})\s*[)）\]】])?",
    re.MULTILINE,
)
#: ★특별약관은 `제N조` 대신 **`N. (제목)`** 을 쓴다.
#:
#:   자동차사고 변호사선임비용(...)(실손) 특별약관
#:   1. (특별약관의 적용범위 및 효력)
#:   2. (보험금의 지급사유)
#:
#: 이걸 몰라서 표본 10건 중 4건이 "조항 머리를 하나도 못 찾음"으로 실패했다.
#:
#: ★오탐이 무섭다. 본문에는 `1.` 로 시작하는 번호 목록이 널려 있다.
#:   그래서 **줄 전체가 `N. (제목)` 인 것만** 인정한다.
#:   실측(실패 문서 13쪽): 넓은 `^\d+\.` 후보는 258행인데
#:   줄 전체가 `N. (제목)` 인 것은 **6행**뿐이었다(코덱스 교차검증).
#:
#: `N-M.` 도 받는다(조항의 세분화. 실측 21/37 문서에서 발견).
_NUMBERED = re.compile(
    r"^[ \t ]{0,6}(\d{1,3})(?:-(\d{1,2}))?\s*[.．]\s*"
    r"[（(\[【]\s*([^)）\]】\n]{2,60})\s*[)）\]】]\s*$",
    re.MULTILINE,
)
#: `N. (제목)` 을 조항으로 인정하려면 **번호열이 형성**돼야 한다.
#: 단독으로 하나만 있으면 본문 인용일 수 있다.
NUMBERED_MIN_HEADS = 3

#: 목차 판정용(줄 위치 무관). 목차는 조 번호가 촘촘히 나열되므로 전체 검색이 맞다.
_ARTICLE_ANY = re.compile(r"제\s*\d{1,3}\s*조")
#: 항 번호(①②③ 또는 1. 2. 3.)
_PARA = re.compile(r"(?:^|\n)\s*([①-⑳]|\d{1,2}\.)\s")
#: ★목차 신호 1 — **점선(dot leader)**.
#: 목차 줄은 `제1 조 【보장종목】 ......................... 1` 꼴이다.
#: 이 점선이 글자수를 부풀려 목차 판정을 무력화했다(실측: p25 비율 202 로
#: 임계 200 을 간발로 넘겨 본문으로 오판 → 점선 제거 후 33).
_DOTS = re.compile(r"[.·․‥…]{5,}")

#: ★목차 신호 2 — 페이지에 찍힌 **`목 차`** 표시. 비율 추정보다 확실하다.
#: 실측: 25,000자짜리 '조항'의 꼬리가 `251 / 401              목 차` 였다.
_TOC_MARK = re.compile(r"^\s*목\s*차\s*$", re.MULTILINE)

#: ★목차 신호 3 — 줄 끝의 페이지 번호. `… 121` 처럼 끝난다.
_TOC_LINE = re.compile(r"[.·․‥…]{5,}\s*\d{1,4}\s*$", re.MULTILINE)

#: 부(部) 경계. ★**단독 줄로 나온 것만** 인정한다.
#: 초안은 페이지 앞 400자에서 아무 데나 매칭해 '용어의정의'가 266개로 잡혔다 —
#: 그건 부 제목이 아니라 **조항 제목**이었다. 실측으로 확인한 실제 부 제목은
#: p23 '보통약관', p63 '별표' 처럼 **한 줄에 그것만** 있다.
_SECTION_LINE = re.compile(r"^\s*(보통약관|특별약관|별\s*표\s*\d*|부\s*록|약관\s*요약서)\s*$")

#: ★부 경계를 넓힌다 — 위 규칙만으로는 403쪽 약관의 부가 2개뿐이었고,
#:   그래서 조 번호가 **52종 충돌**했다(제2조가 51회). 특별약관마다 조 번호가
#:   1부터 다시 시작하는데 구분이 안 돼 섞인 것이다.
#:
#:   코덱스 교차검증으로 얻은 목록. **제목이 `약관`/`특약`으로 끝나는 줄**이 경계다.
#:     `○○ 보통약관` `○○ 특별약관` `○○ 특약` `제도성특약`
#:     `단체취급특약` `지정대리청구서비스특약` `1-1. [건강] ○○ 특별약관`
#:
#:   ★`제N편` `제N장` `제N절` `제N관` 은 **경계가 아니다.**
#:     `특별약관 → 제1관 일반사항 → 제1조` 구조가 실재하므로,
#:     이걸 경계로 삼으면 **과분할**된다(코덱스 지적).
_SECTION_TITLE = re.compile(
    r"^[ \t]{0,8}(?:\d{1,2}(?:-\d{1,2})?\.?\s*)?"      # 앞의 번호 접두어(선택)
    r"(?:\[[^\]\n]{1,12}\]\s*)?"                        # `[건강]` 같은 분류(선택)
    r"([^\n]{2,40}?(?:특별약관|특약|보통약관|주계약\s*약관))\s*$",
    re.MULTILINE,
)

#: ★제목처럼 생겼지만 제목이 아닌 줄을 걸러 낸다.
#:
#:   처음엔 길이 제한만 뒀더니 이런 본문이 부 제목으로 잡혔다(실측).
#:     "② 해당계약에 단체취급특약이 부가되어 있는 경우에는 이 특약에 대하여도 단체취급특약"
#:     "‘특약 색인(索引)’을 활용하시면 본인이 실제 가입한 특약"
#:
#:   제목은 **문장이 아니다** — 항 번호로 시작하지 않고, 쉼표·마침표가 없고,
#:   조사로 끝나지 않는다.
_PARA_START = re.compile(r"^[ \t]*[①-⑳]")            # 항 번호로 시작하면 본문이다
_SENTENCE_MARK = re.compile(r"[,，.。;；]")            # 문장부호가 있으면 본문이다
_NOT_SECTION_TAIL = re.compile(
    r"(?:은|는|이|가|을|를|의|에|로|와|과|및|한다|합니다|따라|경우|하시면)$"
)


def _looks_like_section(line: str, title: str) -> bool:
    """부 경계 제목인가. 하나라도 걸리면 아니다."""
    if _PARA_START.match(line):
        return False
    if _SENTENCE_MARK.search(title):
        return False
    if _NOT_SECTION_TAIL.search(title):
        return False
    if _DOTS.search(line):          # 목차 줄
        return False
    #: 따옴표·괄호 인용으로 시작하면 본문 안의 언급이다.
    if title.lstrip()[:1] in "‘’“”\"'":
        return False
    return True

#: 목차 페이지 판정 임계값. 실측 근거:
#:   목차 p3=조항머리 36개/머리당 41자, p4=19개/61자, p6=18개/77자
#:   본문 p12=4개/258자, p13=5개/234자
#: 조항머리가 촘촘하고 머리당 텍스트가 짧으면 목차다.
TOC_MIN_HEADS = 6
TOC_MAX_CHARS_PER_HEAD = 200


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

    # ── 목차 페이지 식별 (6단계 정확도의 전제) ──
    #: ★신호를 셋 쓴다. 비율 하나만 보다가 목차를 본문으로 오판했다.
    toc_pages: set[int] = set()
    for pg in pages:
        text = pg["text"]
        # (1) 페이지에 `목 차` 가 찍혀 있으면 그것으로 끝이다.
        if _TOC_MARK.search(text):
            toc_pages.add(pg["page"])
            continue
        # (2) 점선+페이지번호로 끝나는 줄이 여럿이면 목차다.
        if len(_TOC_LINE.findall(text)) >= TOC_MIN_HEADS:
            toc_pages.add(pg["page"])
            continue
        # (3) 비율. ★점선을 지우고 잰다 — 점선이 글자수를 부풀린다.
        stripped = _DOTS.sub(" ", text)
        n = len(_ARTICLE_ANY.findall(stripped))
        if n >= TOC_MIN_HEADS and len(stripped) / n < TOC_MAX_CHARS_PER_HEAD:
            toc_pages.add(pg["page"])

    # ── 5) 문서 구조 복원: 단독 줄로 나온 부 제목만 인정 ──
    section_of_page: dict[int, str] = {}
    current = "머리말"
    for pg in pages:
        if pg["page"] not in toc_pages:  # ★목차 안의 부 제목은 경계가 아니다
            for line in pg["text"].splitlines():
                #: 옛 규칙 — `보통약관` 처럼 그 단어만 있는 줄.
                m = _SECTION_LINE.match(line)
                if m:
                    current = re.sub(r"\s+", "", m.group(1))
                    break
                #: 넓힌 규칙 — `○○ 특별약관` 처럼 제목형 줄.
                m2 = _SECTION_TITLE.match(line)
                if m2:
                    title = re.sub(r"\s+", " ", m2.group(1)).strip()
                    if not _looks_like_section(line, title):
                        continue
                    current = title
                    break
        section_of_page[pg["page"]] = current

    # ── 6) 조항 경계 찾기 (목차 페이지 제외) ──
    #: (페이지, 페이지내 오프셋, 조번호, 가지번호, 제목)
    heads: list[tuple[int, int, str, str, str]] = []
    for pg in pages:
        if pg["page"] in toc_pages:
            continue
        for m in _ARTICLE.finditer(pg["text"]):
            heads.append(
                (pg["page"], m.start(), m.group(1), m.group(2) or "", (m.group(3) or "").strip())
            )

    #: ★`제N조` 가 하나도 없으면 **특별약관 번호 형식**을 시도한다.
    #:   두 형식을 **섞지 않는다** — 섞으면 본문의 번호 목록이 조항으로 끼어든다.
    #:   `제N조` 가 있는 문서는 그것이 정답이고, `N.` 은 그 안의 호(號)다.
    numbering = "article"
    if not heads:
        cand: list[tuple[int, int, str, str, str]] = []
        for pg in pages:
            if pg["page"] in toc_pages:
                continue
            for m in _NUMBERED.finditer(pg["text"]):
                cand.append(
                    (pg["page"], m.start(), m.group(1), m.group(2) or "", m.group(3).strip())
                )
        #: 번호열이 형성돼야 조항으로 본다. 하나뿐이면 본문 인용일 수 있다.
        if len(cand) >= NUMBERED_MIN_HEADS:
            heads = cand
            numbering = "numbered"

    if not heads:
        #: ★가짜 조항 1개를 만들지 않는다.
        #:
        #:   문서 전체를 "조항 1개"로 가장하면 파싱이 성공한 것처럼 보이고,
        #:   근거 조항·페이지 추적이 망가진다. 보장 판정에 그대로 쓰이면
        #:   "약관 어디에 근거했나"를 댈 수 없게 된다.
        #:
        #:   대신 **성격이 다른 산출물**임을 명시한 fallback 을 만든다.
        #:   RAG 검색에는 쓰되(문서를 버릴 이유는 없다), 자동 판정에는
        #:   `parse_status` 를 보고 걸러야 한다.
        return _fallback(page_doc, pages, toc_pages, section_of_page)

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
            #: ★목차 페이지는 본문에 넣지 않는다.
            #:   조항 **머리**는 목차에서 안 찾으면서 **본문**은 목차째로 담고 있었다.
            #:   그래서 조항 하나가 42,632자가 됐고 그 안에 조 머리 194개·점선줄 253개가
            #:   들어 있었다. 조 사이에 목차가 끼면 그 조가 목차를 통째로 삼킨다.
            if p in toc_pages:
                continue
            t = text_of.get(p, "")
            a = off if p == page else 0
            b = end_off if p == end_page else len(t)
            parts.append(t[a:b])
        body = "\n".join(parts)

        # ── 9) 계층형 청킹: 긴 조항은 항 단위로 쪼갠다 ──
        paras = [x for x in _PARA.split(body) if x and x.strip()]
        if numbering == "numbered":
            #: 특별약관 번호 형식. `제N조` 가 아니므로 그렇게 부르지 않는다.
            label = f"{no}." + (f"{sub}" if sub else "")
        else:
            label = f"제{no}조" + (f"의{sub}" if sub else "")
        section_name = section_of_page.get(page, "미상")
        clauses.append(
            {
                "clause_no": label,
                "title": title,
                # ★특별약관이 여러 개면 조 번호가 1부터 다시 시작한다.
                # 부 이름을 함께 들고 다녀야 유일해진다.
                "section": section_name,
                "qualified_no": f"{section_name}/{label}",
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
                "content_hash": _clause_hash(section_name, title, body),
            }
        )

    dup: dict[str, int] = {}
    for c in clauses:
        dup[c["content_hash"]] = dup.get(c["content_hash"], 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        #: ★이 문서가 어떻게 파싱됐는지. 판정에 쓸 수 있는지 여기서 갈린다.
        "parse_status": "ok",
        #: 어떤 번호 체계로 쪼갰나. `제N조` 인지 특별약관의 `N.` 인지.
        "numbering": numbering,
        "toc_pages": sorted(toc_pages),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": page_doc["source"],
        "identification": page_doc.get("identification", "unidentified"),
        "extractor": page_doc.get("extractor", ""),
        "stats": {
            "pages": page_doc["stats"]["pages"],
            "clauses": len(clauses),
            "sections": len(set(section_of_page.values())),
            "toc_pages_excluded": len(toc_pages),
            "unique_clause_hashes": len(dup),
            "duplicate_clauses": sum(v - 1 for v in dup.values() if v > 1),
        },
        "sections": sorted(set(section_of_page.values())),
        "clauses": clauses,
    }


def _fallback(page_doc: dict, pages: list[dict], toc_pages: set[int],
              section_of_page: dict[int, str]) -> dict:
    """조항 머리를 못 찾은 문서 — **페이지 단위 청크**로 남긴다.

    ★왜 실패로 버리지 않나

        문서를 버리면 검색에서 아예 사라진다. 약관 원문은 있는데
        "그런 문서 없다"고 답하게 되는 것이 더 나쁘다.

    ★왜 조항 1개로 만들지 않나

        파싱이 성공한 것처럼 보이기 때문이다. 그러면 통계에서 정상 문서와
        섞이고, 보장 판정이 "근거 조항"을 대야 할 때 문서 전체를 들이대게 된다.

        그래서 `parse_status="no_clause_heads"` / `chunk_type="page_fallback"`
        을 **명시**한다. 자동 판정은 이 값을 보고 걸러야 한다.
    """
    chunks: list[dict] = []
    for pg in pages:
        if pg["page"] in toc_pages:
            continue
        body = pg["text"]
        if not body.strip():
            continue
        section_name = section_of_page.get(pg["page"], "미상")
        chunks.append(
            {
                "clause_no": f"p{pg['page']}",
                "title": "",
                "section": section_name,
                "qualified_no": f"{section_name}/p{pg['page']}",
                #: ★조항이 아니다. 이름을 다르게 붙여 섞이지 않게 한다.
                "chunk_type": "page_fallback",
                "locator": {"page_from": pg["page"], "page_to": pg["page"], "char_offset": 0},
                "text": body,
                "char_length": len(body),
                "paragraph_count": 0,
                "tables_on_pages": (
                    {str(pg["page"]): len(pg.get("tables", []))} if pg.get("tables") else {}
                ),
                "content_hash": _clause_hash(section_name, "", body),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        #: ★"성공"이 아니다. 판정에 쓰려면 이 값을 확인해야 한다.
        "parse_status": "no_clause_heads",
        "numbering": "none",
        "toc_pages": sorted(toc_pages),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": page_doc["source"],
        "identification": page_doc.get("identification", "unidentified"),
        "extractor": page_doc.get("extractor", ""),
        "stats": {
            "pages": page_doc["stats"]["pages"],
            #: ★조항이 아니므로 `clauses` 를 0 으로 둔다. 청크 수는 따로 센다.
            "clauses": 0,
            "fallback_chunks": len(chunks),
            "sections": len(set(section_of_page.values())),
            "toc_pages_excluded": len(toc_pages),
            "unique_clause_hashes": len({c["content_hash"] for c in chunks}),
            "duplicate_clauses": 0,
        },
        "sections": sorted(set(section_of_page.values())),
        "clauses": chunks,
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
