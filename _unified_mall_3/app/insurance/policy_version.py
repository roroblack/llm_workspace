"""가입일 → **적용 약관 버전**을 확정한다.

★이게 판정의 첫 단추다

    같은 질병·같은 병원비라도 세대마다 자기부담금이 다르다.
    1세대는 사실상 전액 보상, 4세대는 급여 20%·비급여 30%를 본인이 낸다.
    **어느 약관이 적용되는지를 먼저 정하지 않으면 나머지가 다 틀린다.**

★현행 약관으로 폴백하지 않는다

    가입 시점 약관을 못 찾았을 때 "일단 최신 약관으로 답한다"는
    **가장 위험한 폴백**이다. 사용자는 자기 계약이 아닌 약관으로 안내받는다.
    못 찾으면 `NotResolved` 를 돌려준다 — "확인 불가"가 정답이다.

★판정에서 제외하는 것

    · `excluded_reason` 이 있는 문서 (사업방법서·여행실손·비의료실손)
    · `date_confidence == "unknown"` (판매시점을 모른다)
    · `parse_status != "ok"` (조항 구조화 실패 — 근거를 댈 수 없다)

    셋 다 "쓸 수 있는데 안 쓰는" 게 아니라 **쓰면 틀리는** 것들이다.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import InfraError, ValidationErr

_ROOT = Path(__file__).resolve().parents[2]
_MANIFESTS = _ROOT / "data" / "raw" / "manifests"

_DATE = re.compile(r"^\d{8}$")
#: 특별약관·특약 — 본계약에 붙는 것이지 그 자체가 "가입 상품"이 아니다.
_RIDER = re.compile(r"특별약관|특약|할인|중지\s*및\s*재개|계약전환|제도성")


def _norm(s: str) -> str:
    return re.sub(r"[\s·∙・()（）\[\]]+", "", s or "")


@dataclass(frozen=True)
class PolicyVersion:
    """확정된 약관 버전 하나."""

    insurer: str
    product_name: str
    sale_start: str
    sale_end: str
    generation: int | None
    generation_label: str
    product_line: str
    sha256: str
    date_confidence: str
    generation_confidence: str
    #: 검수 전 설정으로 판정했으면 여기 남는다.
    generation_review: str = ""

    @property
    def is_rider(self) -> bool:
        """특별약관(부가 특약)인가.

        ★본약관과 같은 자리에서 경쟁시키면 안 된다.
          "삼성화재 2019-05-01 가입" 을 물었더니 후보에
          `[갱신형] 무배당 실손의료비 특별약관` 이 본약관과 나란히 올라와
          **`ambiguous_product` 로 되물었다.** 특약은 본계약에 붙는 것이지
          그 자체로 "가입한 상품"이 아니다.
        """
        return bool(_RIDER.search(self.product_name))

    @property
    def usable_for_judgment(self) -> bool:
        """자동 판정에 쓸 수 있는가."""
        if self.date_confidence not in ("exact", "month"):
            return False
        #: ★`00000000` 은 "모른다"를 뜻하는 자리표시자다. 날짜가 아니다.
        if not self.sale_start or self.sale_start == "00000000":
            return False
        return True


@dataclass(frozen=True)
class NotResolved:
    """확정하지 못했다. **추측하지 않는다.**"""

    reason_code: str
    message: str
    #: 후보가 여럿이라 못 정한 경우 사용자에게 보여 줄 목록.
    candidates: tuple[PolicyVersion, ...] = ()


def _row_to_version(r: dict) -> PolicyVersion:
    return PolicyVersion(
        insurer=r.get("insurer", ""),
        product_name=r.get("product_name", "") or r.get("original_name", ""),
        sale_start=(r.get("sale_start") or "").strip(),
        sale_end=(r.get("sale_end") or "").strip(),
        generation=r.get("generation"),
        generation_label=r.get("generation_label", ""),
        product_line=r.get("product_line", ""),
        sha256=r.get("sha256", ""),
        date_confidence=r.get("date_confidence", "exact"),
        generation_confidence=r.get("generation_confidence", ""),
        generation_review=r.get("generation_review", ""),
    )


def load_versions() -> list[PolicyVersion]:
    """판정에 쓸 수 있는 약관 버전 전부."""
    if not _MANIFESTS.exists():
        raise InfraError(f"매니페스트 폴더가 없습니다: {_MANIFESTS}")
    seen: set[str] = set()
    out: list[PolicyVersion] = []
    for m in sorted(_MANIFESTS.glob("*.jsonl")):
        for line in m.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("excluded_reason") or "").strip():
                continue
            sha = r.get("sha256", "")
            if not sha or sha in seen:
                continue
            seen.add(sha)
            v = _row_to_version(r)
            if not v.usable_for_judgment:
                continue
            out.append(v)
    return out


def resolve(
    *,
    insurer: str,
    enrolled_on: str,
    product_name: str | None = None,
    versions: list[PolicyVersion] | None = None,
) -> PolicyVersion | NotResolved:
    """`enrolled_on` 시점에 적용되는 약관 버전을 고른다.

    Args:
        insurer: 보험사명.
        enrolled_on: 가입일 `YYYYMMDD`.
        product_name: 상품명(알면 좁혀진다).
        versions: 미리 읽어 둔 목록(테스트·성능용).

    Returns:
        확정되면 `PolicyVersion`, 아니면 `NotResolved`.
    """
    if not _DATE.match(enrolled_on or ""):
        raise ValidationErr(f"가입일 형식이 잘못됐습니다(YYYYMMDD): {enrolled_on!r}")

    pool = versions if versions is not None else load_versions()
    ins = _norm(insurer)
    cand = [v for v in pool if _norm(v.insurer) == ins]
    if not cand:
        return NotResolved(
            reason_code="insurer_not_supported",
            message=f"'{insurer}' 약관을 보유하고 있지 않습니다.",
        )

    if product_name:
        pn = _norm(product_name)
        narrowed = [v for v in cand if pn in _norm(v.product_name)]
        if narrowed:
            cand = narrowed

    #: 가입일 이전에 판매를 시작한 것 중 **가장 늦은 것**이 적용 약관이다.
    #: 종료일을 아는 경우 가입일이 그 안에 들어야 한다.
    applicable = [
        v
        for v in cand
        if v.sale_start <= enrolled_on and (not v.sale_end or enrolled_on <= v.sale_end)
    ]
    if not applicable:
        #: ★현행 약관으로 대신하지 않는다.
        return NotResolved(
            reason_code="no_version_at_date",
            message=(
                f"{insurer} 의 {enrolled_on} 시점 약관을 찾지 못했습니다. "
                "보유 중인 약관의 판매기간 밖입니다."
            ),
            candidates=tuple(sorted(cand, key=lambda v: v.sale_start)[-3:]),
        )

    #: ★본약관을 먼저 본다. 특약은 본계약에 붙는 것이라 "가입 상품"이 아니다.
    #:   상품명을 명시했으면 그 뜻을 존중해 특약도 후보로 둔다.
    if not product_name:
        main_only = [v for v in applicable if not v.is_rider]
        if main_only:
            applicable = main_only

    applicable.sort(key=lambda v: v.sale_start)
    best = applicable[-1]

    #: ★상품 라인이 갈리면 **반드시 되묻는다.**
    #:   일반 실손 / 노후실손 / 유병력자실손은 자기부담금 체계가 아예 다르다.
    #:   시작일이 우연히 하나만 최신이라고 노후실손을 골라 버리면,
    #:   일반 실손 가입자에게 노후실손 기준으로 답하게 된다.
    if not product_name:
        lines = {v.product_line for v in applicable if v.product_line}
        if len(lines) > 1:
            latest_per_line = {}
            for v in applicable:
                cur = latest_per_line.get(v.product_line)
                if cur is None or v.sale_start > cur.sale_start:
                    latest_per_line[v.product_line] = v
            return NotResolved(
                reason_code="ambiguous_product_line",
                message=(
                    "일반 실손·노후실손·유병력자실손 중 어느 상품인지 알려주세요. "
                    "상품에 따라 자기부담금이 다릅니다."
                ),
                candidates=tuple(latest_per_line.values()),
            )

    #: 같은 시작일이 여럿이면 상품을 특정하지 못한 것이다.
    same = [v for v in applicable if v.sale_start == best.sale_start]
    if len(same) > 1 and not product_name:
        return NotResolved(
            reason_code="ambiguous_product",
            message="같은 시점에 해당하는 상품이 여럿입니다. 상품명을 알려주세요.",
            candidates=tuple(same[:5]),
        )
    return best
