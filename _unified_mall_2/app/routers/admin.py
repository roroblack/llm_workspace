"""관리자 라우터 (Phase 9) — **전부 ADMIN 전용**.

fail-closed 설계: 권한 검사를 엔드포인트마다 붙이면 새 엔드포인트에서 빠뜨리기 쉽다.
그래서 `APIRouter(dependencies=[Depends(require_admin)])`로 **라우터 단위**로 강제하고,
`/api/admin/*` 전 라우트가 이 의존성을 갖는지 가드레일 테스트로 고정한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.roles import require_admin
from app.db.database import get_db
from app.db.models import KnowledgeGap, Order, RunEvent

# 라우터 전역 fail-closed — 여기 추가되는 모든 엔드포인트가 자동으로 ADMIN 전용이 된다.
router = APIRouter(
    prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/orders")
def admin_list_orders(
    db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=200)
) -> list[dict]:
    """전체 주문 요약(최신순). 최소권한 관점에서 요약 필드만 노출한다."""
    rows = db.query(Order).order_by(Order.id.desc()).limit(limit).all()
    return [
        {
            "order_no": o.order_no,
            "user_id": o.user_id,
            "status": o.status,
            "total_amount": o.total_amount,
            "item_count": len(o.items),
        }
        for o in rows
    ]


@router.get("/events")
def admin_list_events(
    db: Session = Depends(get_db),
    trace_id: str | None = None,
    kind: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """관측 이벤트(run_events) 조회 — trace 상관 추적용."""
    q = db.query(RunEvent)
    if trace_id:
        q = q.filter(RunEvent.trace_id == trace_id)
    if kind:
        q = q.filter(RunEvent.kind == kind)
    rows = q.order_by(RunEvent.id.desc()).limit(limit).all()
    # detail은 "요약만" 관례지만 자유 문자열이라 무엇이든 들어올 수 있다 → 출력 시에도
    # 마스킹을 한 겹 더 건다(심층 방어, Codex 지적).
    from app.obs.pii import mask_pii

    return [
        {
            "id": e.id,
            "trace_id": e.trace_id,
            "kind": e.kind,
            "detail": mask_pii(e.detail),
        }
        for e in rows
    ]


#: /index가 노출할 필드 화이트리스트. check_readiness()를 그대로 흘리면 내부 경로·구성이
#: 과다 노출될 수 있다(Codex 지적) → 명시한 것만 내보낸다.
_INDEX_FIELDS = ("ready", "db_tables_ready", "vector_index_ready", "missing_tables")


@router.get("/index")
def admin_index_status() -> dict:
    """RAG 인덱스·DB 준비 상태(읽기 전용, 허용 필드만)."""
    from app.obs.readiness import check_readiness

    status = check_readiness()
    return {k: status[k] for k in _INDEX_FIELDS if k in status}


@router.get("/knowledge-gaps")
def admin_list_knowledge_gaps(
    db: Session = Depends(get_db),
    resolved: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """지식보강 큐 — 근거 없어 답하지 못한 질문(PII 마스킹 후 저장된 형태)."""
    q = db.query(KnowledgeGap)
    if resolved is not None:
        q = q.filter(KnowledgeGap.resolved == resolved)
    rows = q.order_by(KnowledgeGap.id.desc()).limit(limit).all()
    # 저장 시 마스킹 불변식에만 기대지 않는다 — 과거 데이터·직접 SQL 삽입·스캔 우회가 있으면
    # 원문이 남아 있을 수 있으므로 출력 시에도 한 겹 더 마스킹한다(심층 방어, Codex 지적).
    from app.obs.pii import mask_pii

    return [
        {
            "id": g.id,
            "question": mask_pii(g.question),
            "trace_id": g.trace_id,
            "resolved": g.resolved,
        }
        for g in rows
    ]
