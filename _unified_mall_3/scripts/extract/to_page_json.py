"""약관 PDF → 페이지별 JSON 변환.

★왜 이 형식인가

    RAG 에 쓸 것은 텍스트지만, 실손 약관은 **보장한도·자기부담금·갱신주기가 표에 있다**.
    평문만 뽑으면 **셀 경계가 사라져** 어느 값이 어느 담보에 속하는지가 구조로 보장되지 않는다.
    ※단, `find_tables()` 결과가 원 표를 **정확히 복원한다는 뜻은 아니다** — 병합 헤더 분해,
      빈 행 삽입 등이 실측에서 확인됐다. "평문보다 낫다"까지가 검증된 범위다.

    그래서 페이지 단위로 **텍스트 + 표(셀 배열) + 페이지 번호**를 함께 저장한다.
      - 표가 셀 배열로 남는다(원 구조의 완전 복원은 아님 — 위 주석 참조)
      - `locator`(몇 쪽)를 유지해 판정 근거로 인용할 수 있다
      - 실측(무작위 20건): PDF 대비 **합계 11.7% / 중앙값 14.9%**, 파일별 4~29%
        (초기에 보고한 "3%"는 큰 파일만 본 편향 표본이었다 — 정정)

    ★표별 CSV 를 따로 저장하지 않는다
        표는 이미 이 JSON 안에 셀 배열로 들어 있다. CSV 로 또 쓰면 **같은 데이터가 두 벌**이 되어
        어긋났을 때 무엇이 맞는지 판단할 근거가 없어지고, 831건 x 표 수십 개 = 수만 개 파일이 된다.
        사람 검수는 파일이 아니라 **검수 화면에서 표를 렌더링**해 한다.
        엑셀이 필요하면 그때 JSON 에서 뽑으면 된다(파생물은 재생성 가능해야 한다).

★PDF 는 캐시가 아니라 **불변 원본 아카이브**다
    추출 로직은 반드시 바뀐다. 그때 원본이 없으면 다시 받아야 하는데 판매중지 상품 URL 은
    언제 내려갈지 모른다. **재취득 가능성은 가정이고, 가정 위에 비가역적 삭제를 세울 수 없다.**
    이 스크립트는 원본을 읽기만 하고 절대 삭제·이동하지 않는다.

★산출물은 덮어쓰지 않는다
    추출기 버전이 바뀌면 결과가 달라진다. 같은 경로에 덮어쓰면 이전 결과와 그에 기반한
    검수 근거가 사라진다. 그래서 **추출기·스키마 버전을 경로에 넣는다.

실행:
    python -m scripts.extract.to_page_json --sha 968e67f4d3b6        # 한 건
    python -m scripts.extract.to_page_json --insurer samsungfire --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz

from app.core.errors import InfraError

_ROOT = Path(__file__).resolve().parents[2]
_RAW = _ROOT / "data" / "raw" / "insurance_terms"
_MANIFEST = _ROOT / "data" / "raw" / "fetch_manifest.jsonl"
_OUT = _ROOT / "data" / "extracted"

#: v2 — 텍스트 정규화 추가(제어문자·사용자영역 글리프 제거). §_clean_text
SCHEMA_VERSION = "2"
#: 이 값이 바뀌면 같은 PDF 라도 결과가 달라진다. 산출물에 함께 기록한다.
EXTRACTOR = f"pymupdf/{fitz.__doc__.split()[1] if fitz.__doc__ else 'unknown'}"


def _version_tag() -> str:
    """산출물 경로에 넣을 버전 태그. 추출기가 바뀌면 경로가 바뀐다."""
    return f"s{SCHEMA_VERSION}_{EXTRACTOR.replace('/', '-').replace(':', '')}"


def _load_manifest() -> list[dict]:
    """★매니페스트는 보험사별로 나뉘어 있다. `glob` 으로 전부 읽어 빠뜨리지 않는다."""
    from scripts.crawl.split_manifest import load_all

    records = load_all()
    if not records:
        raise InfraError("수집 기록이 없습니다(data/raw/manifests/*.jsonl).")
    return records


#: 지워야 할 것 1 — C0 제어문자(줄바꿈·탭은 남긴다).
#: 지워야 할 것 2 — 사용자 정의 영역(PUA) 글리프.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PUA = re.compile(r"[-]")


def _clean_text(s: str) -> tuple[str, int, int]:
    """텍스트 정규화. `(정리된 문자열, 지운 제어문자 수, 지운 PUA 수)`.

    ★왜 필요한가 — **검색이 깨진다**

        추출본을 열어 보니 이랬다(실측).

            '회사는\\x01 다음\\x01 중\\x01 어느\\x01 한\\x01 가지의\\x01 경우에...'

        `\\x01` 이 낱말마다 끼어 있다. 이 상태로는
        `"보험금을 지급하지 않습니다"` 로 검색해도 **안 걸린다.**
        보장 판정에서 면책 조항을 못 찾는다는 뜻이다.

        표본 64건 중 **27건(42%)** 이 오염돼 있었고 `\\x01` 이 279,623회 나왔다.

    ★지워도 되는지 확인했다

        `\\x01` 은 **항상 공백 바로 앞**에 온다(상위 조합 전부 `앞=글자 뒤=' '`).
        즉 공백의 잉여 마커이고, 지우면 원문이 그대로 남는다.
        `\\uf000` 은 줄머리에 오는 **장식 글리프**다(`앞='\\n' 뒤='회'`).

        ★①②③ 같은 원문자는 **PUA 가 아니다**(U+2460~). 지워지지 않는다.

    ★조용히 지우지 않는다

        몇 자를 지웠는지 산출물 `stats.normalized` 에 남긴다.
        나중에 "이 문서 왜 이러지" 할 때 근거가 된다.
    """
    n_ctl = len(_CONTROL.findall(s))
    n_pua = len(_PUA.findall(s))
    if n_ctl:
        s = _CONTROL.sub("", s)
    if n_pua:
        s = _PUA.sub("", s)
    return s, n_ctl, n_pua


def extract(pdf: Path, meta: dict) -> dict:
    """한 건을 페이지별 JSON 구조로 만든다."""
    doc = fitz.open(str(pdf))
    pages: list[dict] = []
    total_tables = 0
    n_ctl_all = n_pua_all = 0
    for i, page in enumerate(doc):
        text, n_ctl, n_pua = _clean_text(page.get_text())
        n_ctl_all += n_ctl
        n_pua_all += n_pua
        tables: list[list[list[str]]] = []
        try:
            for t in page.find_tables().tables:
                #: ★표 안의 글자도 같은 오염을 겪는다. 같이 정리한다.
                cells = [
                    [_clean_text("" if c is None else str(c))[0].strip() for c in row]
                    for row in t.extract()
                ]
                if cells:
                    tables.append(cells)
        except Exception:  # noqa: BLE001
            # 표 인식 실패는 페이지 전체 실패가 아니다. 다만 조용히 '표 없음'으로
            # 만들지 않도록 아래 table_extraction_failed 로 표시한다.
            tables = []
            pages.append(
                {
                    "page": i + 1,
                    "text": text,
                    "tables": [],
                    "table_extraction_failed": True,
                }
            )
            continue
        total_tables += len(tables)
        pages.append({"page": i + 1, "text": text, "tables": tables})
    n = doc.page_count
    doc.close()

    text_len = sum(len(p["text"]) for p in pages)
    return {
        "schema_version": SCHEMA_VERSION,
        "extractor": EXTRACTOR,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "insurer": meta.get("insurer", ""),
            "product_name": meta.get("product_name", ""),
            "product_code": meta.get("product_code", ""),
            "sale_start": meta.get("sale_start", ""),
            "sale_end": meta.get("sale_end", ""),
            "url": meta.get("url", ""),
            "sha256": meta.get("sha256", ""),
            "bytes": meta.get("bytes", 0),
        },
        #: ★받았다는 이유로 무엇인지 안다고 하지 않는다. 식별은 별도 단계다.
        "identification": meta.get("identification", "unidentified"),
        "stats": {
            "pages": n,
            "text_length": text_len,
            "tables": total_tables,
            #: ★무엇을 지웠는지 남긴다. 조용한 변환은 나중에 원인을 못 찾게 한다.
            "normalized": {"control_removed": n_ctl_all, "pua_removed": n_pua_all},
        },
        "pages": pages,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", help="sha256 접두사(12자 이상)로 한 건만 변환")
    ap.add_argument("--insurer", help="보험사 슬러그 폴더 (예: samsungfire)")
    ap.add_argument("--limit", type=int, default=1)
    args = ap.parse_args()

    records = _load_manifest()
    by_sha: dict[str, dict] = {}
    for r in records:
        by_sha.setdefault(r["sha256"], r)

    targets: list[dict] = []
    if args.sha:
        hits = [r for s, r in by_sha.items() if s.startswith(args.sha)]
        if not hits:
            raise InfraError(f"매니페스트에서 sha 접두사 '{args.sha}' 를 찾지 못했습니다.")
        targets = hits[:1]
    else:
        slug = args.insurer or "samsungfire"
        targets = [
            r for r in by_sha.values() if f"/{slug}/" in r["saved_as"]
        ][: args.limit]
        if not targets:
            raise InfraError(f"'{slug}' 폴더의 수집 기록을 찾지 못했습니다.")

    _OUT.mkdir(parents=True, exist_ok=True)
    for meta in targets:
        pdf = _ROOT / meta["saved_as"]
        if not pdf.exists():
            print(f"[SKIP] 파일 없음: {meta['saved_as']}")
            continue
        doc = extract(pdf, meta)
        slug = Path(meta["saved_as"]).parent.name
        out_dir = _OUT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        # ★버전별 경로. 같은 PDF 를 새 추출기로 다시 뽑아도 이전 결과가 남는다.
        ver_dir = out_dir / _version_tag()
        ver_dir.mkdir(parents=True, exist_ok=True)
        out = ver_dir / f"{meta['sha256'][:12]}.json"
        if out.exists():
            print(f"[SKIP] 이미 있음(덮어쓰지 않음): {out.relative_to(_ROOT)}")
            continue
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

        s = doc["stats"]
        ratio = out.stat().st_size / max(meta.get("bytes", 1), 1) * 100
        print(
            f"[OK] {(meta.get('product_name') or '(상품명 없음)')[:30]}\n"
            f"     {s['pages']}쪽 / 텍스트 {s['text_length']:,}자 / 표 {s['tables']}개\n"
            f"     PDF {meta.get('bytes', 0):,}B → JSON {out.stat().st_size:,}B ({ratio:.1f}%)"
            + f"\n     {out.relative_to(_ROOT)}"
        )


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(_ROOT))
    main()
