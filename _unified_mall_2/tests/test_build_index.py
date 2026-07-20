"""인덱스 빌드 경계 테스트 (임베딩 불필요 → CI 경로 유지).

Phase 8: 레거시 `app/rag/qa.py` 삭제로 `test_qa.py`가 없어지면서, qa와 무관한 build_index
검사를 여기로 이관했다. `test_rag.py`는 ml 마커(실 임베딩)라 CI에서 제외되므로 그쪽에 두면
CI 커버리지를 잃는다 — 그래서 마커 없는 별도 파일로 둔다.
"""

from __future__ import annotations

import pytest

from app.core.errors import InfraError


def test_pdf_parse_failure_raises_infra_error(tmp_path):
    """PDF 파싱 실패는 TXT로 조용히 대체하지 않고 InfraError로 명시 실패(무폴백)."""
    from app.rag.build_index import _load_docs

    (tmp_path / "broken.pdf").write_text("이건 진짜 PDF가 아니라 그냥 텍스트입니다", encoding="utf-8")
    with pytest.raises(InfraError):
        _load_docs(tmp_path)
