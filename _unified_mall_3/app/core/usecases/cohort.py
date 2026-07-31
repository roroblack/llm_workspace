"""코호트 통계 유스케이스 — 팀 MVP 기능 2·3.

기능 2: "이전 지급받은 고객의 데이터로 청구승인율을 보여준다" (33건/40건)
기능 3: "네 케이스가 다른 곳에서는 이랬다" — 연령대 등으로 묶은 유사 케이스

★이 유스케이스가 막아야 하는 것

1. **표본이 적은데 비율만 보여주는 것.** 40건의 33건은 82.5%로 보이지만
   95% 신뢰구간이 ±12%p 수준이다. 최소표본 미달이면 비율을 내지 않는다.
2. **생존 편향을 숨기는 것.** 지급받은 사람이 부지급 당한 사람보다 훨씬 많이 제보한다.
   승인율이 실제보다 높게 나오며, 이것은 **사후 보정이 불가능한 구조적 편향**이다.
   보정하는 척하지 않고 경고로 남긴다.
3. **합성 데이터를 실제라고 말하는 것.** ``data_source`` 는 응답에서 절대 생략하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.domain.insurance import CohortStats, DataSource, KcdCode
from app.core.errors import ValidationErr
from app.core.ports.insurance import CohortStatsPort

#: 이 표본수 미만이면 비율을 공개하지 않는다.
#: 값 자체는 정책이며, 실제 데이터를 보기 전에는 확정할 수 없다(현재는 잠정치).
DEFAULT_MIN_SAMPLE = 30

#: 우리 표본에 구조적으로 존재하며 보정할 수 없는 편향.
_STRUCTURAL_WARNINGS = (
    "제보 편향: 지급받은 사람이 부지급 사례보다 더 많이 제보하는 경향이 있어 "
    "승인 비율이 실제보다 높게 나타날 수 있습니다.",
    "이 수치는 우리가 수집·검증한 표본 기준이며 보험사 전체 통계가 아닙니다.",
)


@dataclass(frozen=True)
class CohortAnswer:
    """화면·API 어디로 나가든 이 값들이 함께 나간다."""

    stats: CohortStats
    #: 표본이 충분할 때만 채워진다. 미달이면 ``None`` 이고, 대신 ``headline`` 이 사실만 말한다.
    approval_rate: float | None
    #: 사람이 읽는 한 줄. 비율이 아니라 건수로 말한다.
    headline: str

    @property
    def data_source(self) -> DataSource:
        return self.stats.data_source


class CohortQuery:
    """코호트 통계 조회."""

    def __init__(self, stats_port: CohortStatsPort, *, min_sample: int = DEFAULT_MIN_SAMPLE) -> None:
        if min_sample < 1:
            raise ValidationErr("min_sample 은 1 이상이어야 합니다.")
        self._stats = stats_port
        self._min_sample = min_sample

    def run(
        self,
        *,
        kcd_code: KcdCode,
        product_id: str,
        age_band: str | None,
        data_source: DataSource,
    ) -> CohortAnswer:
        """한 번의 조회는 **하나의 ``data_source`` 만** 본다.

        합성과 실제를 한 응답에서 합치지 않는다. 두 값을 모두 보고 싶으면
        호출을 두 번 하고, 화면에서도 따로 표시한다.
        """
        stats = self._stats.fetch(
            kcd_code=kcd_code,
            product_id=product_id,
            age_band=age_band,
            data_source=data_source,
        )

        if stats.data_source is not data_source:
            # 요청한 출처와 다른 데이터가 돌아오면 조용히 쓰지 않고 실패시킨다.
            raise ValidationErr(
                f"요청한 출처와 반환된 출처가 다릅니다: "
                f"{data_source.value} != {stats.data_source.value}"
            )

        warnings = tuple(stats.warnings) + _STRUCTURAL_WARNINGS
        if data_source is DataSource.SYNTHETIC:
            warnings = ("합성 데이터입니다. 실제 지급 통계가 아닙니다.",) + warnings

        enriched = CohortStats(
            n=stats.n,
            approved_n=stats.approved_n,
            denied_n=stats.denied_n,
            data_source=stats.data_source,
            min_sample=self._min_sample,
            warnings=warnings,
        )

        rate = enriched.approval_rate() if enriched.min_sample_met else None
        return CohortAnswer(stats=enriched, approval_rate=rate, headline=_headline(enriched))


def _headline(stats: CohortStats) -> str:
    """건수로 말한다. 비율은 표본이 충분할 때만 덧붙인다."""
    base = f"검증된 {stats.n}건 중 {stats.approved_n}건 승인 · {stats.denied_n}건 부지급"
    if not stats.min_sample_met:
        return f"{base} (표본이 적어 비율은 표시하지 않습니다)"
    return f"{base} ({stats.approved_n / stats.n:.1%})"
