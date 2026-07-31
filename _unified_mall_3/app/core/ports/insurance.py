"""안쪽 계층이 바깥에 요구하는 인터페이스(포트).

유스케이스는 **이 Protocol 만** 받는다. 구현 클래스(pgvector·FastAPI·OCR 라이브러리)를
직접 알지 않는다. 그래서 담당자 ①은 DB·LLM 없이 유스케이스를 테스트할 수 있고,
②③④⑤는 각자 자기 디렉터리에서 구현만 갈아 끼우면 된다.

★포트 시그니처 변경은 팀 전체의 계약 변경이다. PR로만 바꾸고 자기 승인 금지.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence

from app.core.domain.insurance import (
    Citation,
    CohortStats,
    DataSource,
    KcdCode,
    PolicyVersion,
)


class PolicyVersionResolverPort(Protocol):
    """가입일·사고일로 적용 약관 버전을 확정한다.

    확정할 수 없으면 **현행 버전으로 대체하지 말고** 실패해야 한다.
    조용한 대체는 폴백이며 오답의 직접 원인이다.
    """

    def resolve(
        self, *, product_id: str, enrolled_on: date, incident_on: date
    ) -> PolicyVersion: ...


class TermsRetrieverPort(Protocol):
    """약관 조항 검색.

    ★보장조항만 반환하면 안 된다. 관련 **면책조항을 함께** 반환해야 하며,
    이는 반환값의 ``kind`` 로 검증한다(면책 누락 테스트).
    """

    def search(
        self, *, query: str, policy_version_id: str, top_k: int
    ) -> Sequence[Citation]: ...


class KcdLookupPort(Protocol):
    """질병명·코드 조회.

    ★``candidates_by_name`` 은 **여러 개를 반환한다.** '우울증'은 F32/F33/F34.1 등이고
    약관 판정이 코드마다 다르다. 하나를 자동으로 고르면 틀린 답을 확신 있게 주게 된다.
    선택은 사용자가 한다.
    """

    def candidates_by_name(self, *, name: str, limit: int) -> Sequence[KcdCode]: ...

    def get(self, *, version_label: str, code: str) -> KcdCode: ...


class CohortStatsPort(Protocol):
    """코호트 집계 조회.

    구현은 ``verified`` 증빙만 집계하는 뷰를 읽어야 하며, 합성/실제를 섞을 수 없도록
    ``data_source`` 별로 물리적으로 분리된 저장소를 본다.
    """

    def fetch(
        self,
        *,
        kcd_code: KcdCode,
        product_id: str,
        age_band: str | None,
        data_source: DataSource,
    ) -> CohortStats: ...


class AuditLogPort(Protocol):
    """감사 기록 — 누가 언제 무엇을 바꿨나.

    특히 ``verified`` 승격은 반드시 남는다. 이 서비스에서 가장 중요한 로그다.
    """

    def record(
        self,
        *,
        actor_id: str,
        actor_type: str,
        action: str,
        target: str,
        detail: dict[str, object],
    ) -> None: ...


class AgentIdentityPort(Protocol):
    """호출자가 사람인지 에이전트인지.

    ★반환값에 ``unknown`` 이 있는 이유: 사람인 척하는 에이전트를 100% 판별하는 방법은 없다.
    그래서 판별에 의존하는 설계를 하지 않는다 — 판별에 실패해도 안전하도록
    모든 응답에 불확실성 필드를 항상 싣는다.

    Returns:
        ``"declared"``(스스로 밝힘) / ``"inferred"``(행동으로 추정) / ``"unknown"``
    """

    def classify(self, *, api_key: str | None, user_agent: str | None) -> str: ...
