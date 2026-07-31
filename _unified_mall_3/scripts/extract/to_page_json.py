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
from datetime import datetime, timezone
from pathlib import Path

import fitz

from app.core.errors import InfraError

_ROOT = Path(__file__).resolve().parents[2]
_RAW = _ROOT / "data" / "raw" / "insurance_terms"
_MANIFEST = _ROOT / "data" / "raw" / "fetch_manifest.jsonl"
_OUT = _ROOT / "data" / "extracted"

SCHEMA_VERSION = "1"
#: 이 값이 바뀌면 같은 PDF 라도 결과가 달라진다. 산출물에 함께 기록한다.
EXTRACTOR = f"pymupdf/{fitz.__doc__.split()[1] if fitz.__doc__ else 'unknown'}"


def _version_tag() -> str:
    """산출물 경로에 넣을 버전 태그. 추출기가 바뀌면 경로가 바뀐다."""
    return f"s{SCHEMA_VERSION}_{EXTRACTOR.replace('/', '-').replace(':', '')}"


def _load_manifest() -> list[dict]:
    if not _MANIFEST.exists():
        raise InfraError(f"매니페스트가 없습니다: {_MANIFEST}")
    return [
        json.loads(line)
        for line in _MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def extract(pdf: Path, meta: dict) -> dict:
    """한 건을 페이지별 JSON 구조로 만든다."""
    doc = fitz.open(str(pdf))
    pages: list[dict] = []
    total_tables = 0
    for i, page in enumerate(doc):
        text = page.get_text()
        tables: list[list[list[str]]] = []
        try:
            for t in page.find_tables().tables:
                cells = [[("" if c is None else str(c)).strip() for c in row] for row in t.extract()]
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
        "stats": {"pages": n, "text_length": text_len, "tables": total_tables},
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
