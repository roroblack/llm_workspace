"""보험 보장 사전검토 도메인 — 엔티티와 값객체.

이 모듈은 **프레임워크를 모른다.** DB·HTTP·LLM 어느 것도 import 하지 않는다.
클린아키텍처 2단계에서 가장 안쪽이며, 바깥(app/outer)은 여기에 의존하지만
여기서는 바깥을 절대 참조하지 않는다.

설계 원칙:
- 모르는 것은 모른다고 표현한다(`IdentificationStatus.UNIDENTIFIED`, `Verdict.NEEDS_EXPERT`).
- 확신 없는 값을 기본값으로 채우지 않는다. 폴백 금지.
- 표본이 부족하면 비율을 계산해 주지 않는다 — 계산이 가능하다는 것과
  말해도 된다는 것은 다르다(`CohortStats.approval_rate`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from app.core.errors import ValidationErr


class InsurerKind(str, Enum):
    """손해보험사 9곳 / 생명보험사 7곳."""

    GENERAL = "general"
    LIFE = "life"


class ClauseKind(str, Enum):
    """조항 종류.

    ``EXCLUSION``(면책)이 **별도 값으로 존재해야** '보장조항과 면책조항을 함께 인용'하는
    규칙을 쿼리와 테스트로 강제할 수 있다. 본문 텍스트에서 면책을 찾아내는 방식이면
    누락됐는지 검증할 방법이 없다.
    """

    COVERAGE = "coverage"
    EXCLUSION = "exclusion"
    DEFINITION = "definition"
    LIMIT = "limit"


class IdentificationStatus(str, Enum):
    """이 약관 문서가 '무엇인지' 확정됐는가.

    받아왔다는 이유로 무엇인지 안다고 하지 않는다. 수집과 식별은 별개 작업이며,
    판정에 쓸 수 있는 것은 ``CONFIRMED`` 뿐이다.
    """

    UNIDENTIFIED = "unidentified"
    AMBIGUOUS = "ambiguous"
    CONFIRMED = "confirmed"


class Verdict(str, Enum):
    """사전검토 결과 — 4단. 이진 판정(된다/안된다)은 만들지 않는다."""

    LIKELY_COVERED = "likely_covered"
    UNLIKELY = "unlikely"
    NEEDS_DOCUMENTS = "needs_documents"
    NEEDS_EXPERT = "needs_expert"


class DataSource(str, Enum):
    """이 수치가 어디서 왔는가. 응답에서 절대 생략하지 않는다."""

    SYNTHETIC = "synthetic"
    VERIFIED_REAL = "verified_real"


@dataclass(frozen=True)
class PolicyVersion:
    """약관 버전 — 이 도메인의 중심.

    가입일·사고일로 '어느 버전이 적용되는지'를 정하는 것이 판정의 출발점이다.
    현행 약관을 과거 계약에 대입하는 것은 폴백이며 오답의 직접 원인이다.
    """

    id: str
    product_id: str
    version_label: str
    valid_from: date
    valid_to: date | None
    identification_status: IdentificationStatus
    #: 판정 근거의 근거 — 어디서 언제 받았고 무엇인지 증명할 수 있어야 한다.
    source_url: str | None = None
    sha256: str | None = None
    #: 약관은 저작물이다. 확인 전에는 재배포하지 않는다.
    redistributable: bool = False

    def usable_for_assessment(self) -> bool:
        """판정에 쓸 수 있는가. 식별이 확정된 것만 허용한다."""
        return self.identification_status is IdentificationStatus.CONFIRMED

    def applies_on(self, when: date) -> bool:
        """이 날짜에 이 버전이 적용되는가."""
        if when < self.valid_from:
            return False
        return self.valid_to is None or when <= self.valid_to


@dataclass(frozen=True)
class KcdCode:
    """질병분류기호.

    ``code`` 문자열만으로는 유일하지 않다. 같은 ``J20.9``라도 차수가 다르면 다른 코드다.
    그래서 ``version_label``을 항상 함께 들고 다닌다.
    """

    version_label: str
    code: str
    name_ko: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.version_label, self.code)


@dataclass(frozen=True)
class Citation:
    """판정 근거로 인용한 약관 조항.

    인용할 수 있는 것은 약관 조항뿐이다. 상호작용 로그·FAQ·다른 사용자의 답변은
    여기 들어올 수 없다(순환 참조·코퍼스 오염 방지).
    """

    clause_id: str
    kind: ClauseKind
    locator: str


@dataclass(frozen=True)
class CohortStats:
    """코호트 집계 결과.

    ``verified`` 증빙만 집계에 반영된다. 정합성만 통과한 증빙(``consistent``)은
    여기 오지 않는다 — 그 검사가 확인한 것은 문서 내부 정합성일 뿐,
    실제로 보험사가 그렇게 결정했는지가 아니다.
    """

    n: int
    approved_n: int
    denied_n: int
    data_source: DataSource
    min_sample: int
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def min_sample_met(self) -> bool:
        return self.n >= self.min_sample

    def approval_rate(self) -> float:
        """승인 비율.

        ★표본이 최소치에 미달하면 **계산해 주지 않고 실패한다.**
        40건으로 낸 82.5%는 신뢰구간이 ±12%p 수준이라 단정하면 거짓이 된다.
        '계산할 수 있다'와 '말해도 된다'는 다르다.
        """
        if not self.min_sample_met:
            raise ValidationErr(
                f"표본이 부족해 비율을 산출하지 않습니다 (n={self.n}, 최소 {self.min_sample})."
            )
        return self.approved_n / self.n
