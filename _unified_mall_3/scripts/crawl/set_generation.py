"""실손의료보험 **세대**를 판매개시일로 판정해 매니페스트에 넣는다.

★왜 세대가 필요한가

    세대마다 **자기부담금과 보장범위가 다르다.** 같은 질병·같은 병원비라도
    1세대는 전액, 4세대는 급여 20%·비급여 30%를 본인이 낸다.
    "보장받을 수 있나"에 답하려면 **가입 시점의 세대**를 먼저 정해야 한다.

★경계는 어디서 왔나 — 감독규정이지 약관이 아니다

    조항 1,702개를 뒤졌으나 세대 경계를 정의한 문구는 **없다**(`4세대` 언급 7회뿐).
    세대 구분은 금융감독원 표준약관 개정 시점으로 정해지는 것이라 약관 본문에
    적히지 않는다. 그래서 경계는 **공개된 개정 이력**을 따른다.

        1세대 (구실손)        ~ 2009-09-30
        2세대 (표준화실손)     2009-10-01 ~ 2017-03-31
        3세대 (착한실손)      2017-04-01 ~ 2021-06-30
        4세대                2021-07-01 ~

★5세대는 **단정하지 않는다**

    기획서에는 "1~5세대"로 적혀 있다. 그런데 수집물에서 근거를 못 찾았다.
      · 상품명·약관 어디에도 `5세대` 표기가 없다
      · 2026-07-01 에 76건이 몰려 있고 흥국화재 상품명에 `_20260701이후` 가 붙지만,
        그것이 세대 교체인지 통상 개정인지 **이 데이터로는 구분되지 않는다**

    그래서 2026-07-01 이후는 `generation=4` 로 두되
    `generation_note="2026-07 개정 — 세대 교체 여부 미확인"` 을 남긴다.
    확인되면 경계를 추가한다. **모르는 것을 아는 척하지 않는다.**

★등급을 그대로 물려받는다

    `date_confidence="month"` 인 문서는 날짜가 월까지만 정확하다.
    다행히 **세대 경계가 모두 월 초·월 말**이라 월 단위로도 세대는 갈린다.
    다만 경계월(2009-09/10, 2017-03/04, 2021-06/07)에 걸치면 흔들릴 수 있어
    `generation_confidence` 를 따로 남긴다.

실행:
    python -m scripts.crawl.set_generation --dry-run
    python -m scripts.crawl.set_generation
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from app.core.errors import InfraError

_ROOT = Path(__file__).resolve().parents[2]
_MANIFESTS = _ROOT / "data" / "raw" / "manifests"

#: (시작일 포함, 세대, 통칭). 마지막 구간은 끝이 없다.
GENERATIONS: list[tuple[str, int, str]] = [
    ("00000000", 1, "구실손"),
    ("20091001", 2, "표준화실손"),
    ("20170401", 3, "착한실손"),
    ("20210701", 4, "4세대"),
]

#: 경계가 걸린 달 — 여기 해당하면 월 단위 날짜로는 세대가 흔들린다.
_BOUNDARY_MONTHS = {"200909", "200910", "201703", "201704", "202106", "202107"}

#: 세대 교체 여부가 확인되지 않은 개정 시점.
_UNVERIFIED_FROM = "20260701"


def generation_of(sale_start: str) -> tuple[int, str]:
    """`(세대, 통칭)`."""
    gen, name = GENERATIONS[0][1], GENERATIONS[0][2]
    for start, g, label in GENERATIONS:
        if sale_start >= start:
            gen, name = g, label
        else:
            break
    return gen, name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not _MANIFESTS.exists():
        raise InfraError(f"매니페스트 폴더가 없습니다: {_MANIFESTS}")

    dist = collections.Counter()
    conf = collections.Counter()
    skipped = 0
    for m in sorted(_MANIFESTS.glob("*.jsonl")):
        rows = [
            json.loads(line)
            for line in m.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        changed = False
        for r in rows:
            start = (r.get("sale_start") or "").strip()
            if not start or len(start) < 8 or start == "00000000":
                #: ★날짜를 모르면 세대도 모른다. 비워 둔다.
                if r.get("generation") is not None:
                    r.pop("generation", None)
                    r.pop("generation_label", None)
                    changed = True
                r["generation_confidence"] = "unknown"
                skipped += 1
                continue

            gen, label = generation_of(start)
            r["generation"] = gen
            r["generation_label"] = label

            #: 신뢰도 — 날짜 등급과 경계 근접 여부를 함께 본다.
            date_conf = r.get("date_confidence", "exact")
            if date_conf == "month" and start[:6] in _BOUNDARY_MONTHS:
                #: 경계달인데 일자를 모른다 → 세대가 갈릴 수 있다.
                gc = "ambiguous"
            elif date_conf == "month":
                gc = "month"
            else:
                gc = "exact"
            r["generation_confidence"] = gc

            if start >= _UNVERIFIED_FROM:
                r["generation_note"] = "2026-07 개정 — 세대 교체 여부 미확인"

            dist[f"{gen}세대({label})"] += 1
            conf[gc] += 1
            changed = True

        if changed and not args.dry_run:
            tmp = m.with_suffix(".jsonl.tmp")
            tmp.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                encoding="utf-8",
            )
            tmp.replace(m)

    print("세대 분포(행 기준):")
    for k in sorted(dist):
        print(f"  {k:<16}{dist[k]:>5}행")
    print(f"\n세대 판정 신뢰도: {dict(conf)}")
    print(f"날짜를 몰라 판정 못 한 행 {skipped}")
    if args.dry_run:
        print("(dry-run: 아무것도 쓰지 않았습니다.)")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(_ROOT))
    main()
